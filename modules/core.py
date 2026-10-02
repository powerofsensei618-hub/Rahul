import os
import re
import glob
import time
import json
import shutil
import asyncio
import logging
import datetime
import subprocess
import concurrent.futures

import aiohttp
import aiofiles
import requests

try:  # optional, only used for faster Telegram transfers
    import tgcrypto  # noqa: F401
except Exception:  # pragma: no cover
    pass

from utils import progress_bar

from pyrogram import Client
from pyrogram.types import Message
from pyrogram.errors import FloodWait

try:  # pytube breaks often; it must never stop the bot from starting
    from pytube import Playlist
except Exception:  # pragma: no cover
    Playlist = None

from yt_dlp import YoutubeDL

logger = logging.getLogger(__name__)

UA = ("Mozilla/5.0 (Linux; Android 12; RMX2121) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36")

ARIA_ARGS = "aria2c:-x16 -s16 -k1M -j16 --file-allocation=none"


class DownloadError(Exception):
    """Raised with a short, user-presentable reason."""


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------
def duration(filename):
    """Video duration in seconds (0 if it can't be read)."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", filename],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        return float(result.stdout.decode().strip())
    except Exception:
        return 0.0


def video_size(filename):
    """(width, height) of the first video stream, or (0, 0)."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "json", filename],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        st = json.loads(result.stdout.decode())["streams"][0]
        return int(st["width"]), int(st["height"])
    except Exception:
        return 0, 0


def exec(cmd):  # noqa: A001 (kept for backward compatibility)
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = process.stdout.decode()
    print(output)
    return output


def pull_run(work, cmds):
    with concurrent.futures.ThreadPoolExecutor(max_workers=work) as executor:
        print("Waiting for tasks to complete")
        list(executor.map(exec, cmds))


def human_readable_size(size, decimal_places=2):
    unit = "B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size < 1024.0 or unit == 'PB':
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"


def time_name():
    date = datetime.date.today()
    now = datetime.datetime.now()
    current_time = now.strftime("%H%M%S")
    return f"{date} {current_time}.mp4"


def redact(text):
    """Hide tokens/signatures before showing a URL/command in chat or logs."""
    text = re.sub(r"(token=)[^&\s]+", r"\1***", text or "")
    text = re.sub(r"(Signature=|bcov_auth=|X-Access-Token[:=]\s*)[^&\s]+", r"\1***", text)
    return text


def tail(text, n=6, limit=600):
    lines = [l for l in (text or "").strip().splitlines() if l.strip()]
    out = "\n".join(lines[-n:])
    return out[-limit:]


async def run_args(args, timeout=None):
    """Run a command WITHOUT a shell (no injection) and WITHOUT blocking the bot."""
    proc = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        return 124, "", "timed out"
    return proc.returncode, out.decode(errors="ignore"), err.decode(errors="ignore")


# --------------------------------------------------------------------------
# PDF / generic file download
# --------------------------------------------------------------------------
async def aio(url, name):
    k = f'{name}.pdf'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(k, mode='wb')
                await f.write(await resp.read())
                await f.close()
            else:
                raise DownloadError(f"HTTP {resp.status} while downloading file")
    return k


async def download(url, name):
    """Download a (drive/pdf) file. Raises instead of returning a missing file."""
    ka = f'{name}.pdf'
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers={"User-Agent": UA}) as resp:
            if resp.status != 200:
                raise DownloadError(f"HTTP {resp.status} while downloading file")
            f = await aiofiles.open(ka, mode='wb')
            await f.write(await resp.read())
            await f.close()
    return ka


def old_download(url, file_name, chunk_size=1024 * 10):
    if os.path.exists(file_name):
        os.remove(file_name)
    r = requests.get(url, allow_redirects=True, stream=True, timeout=60)
    with open(file_name, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            if chunk:
                fd.write(chunk)
    return file_name


# --------------------------------------------------------------------------
# yt-dlp output parsers (kept for compatibility)
# --------------------------------------------------------------------------
def parse_vid_info(info):
    info = info.strip()
    info = info.split("\n")
    new_info = []
    temp = []
    for i in info:
        i = str(i)
        if "[" not in i and '---' not in i:
            while "  " in i:
                i = i.replace("  ", " ")
            i = i.strip()
            i = i.split("|")[0].split(" ", 2)
            try:
                if "RESOLUTION" not in i[2] and i[2] not in temp and "audio" not in i[2]:
                    temp.append(i[2])
                    new_info.append((i[0], i[2]))
            except Exception:
                pass
    return new_info


def vid_info(info):
    info = info.strip()
    info = info.split("\n")
    new_info = dict()
    temp = []
    for i in info:
        i = str(i)
        if "[" not in i and '---' not in i:
            while "  " in i:
                i = i.replace("  ", " ")
            i = i.strip()
            i = i.split("|")[0].split(" ", 3)
            try:
                if "RESOLUTION" not in i[2] and i[2] not in temp and "audio" not in i[2]:
                    temp.append(i[2])
                    new_info.update({f'{i[2]}': f'{i[0]}'})
            except Exception:
                pass
    return new_info


async def run(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    print(f'[{cmd!r} exited with {proc.returncode}]')
    if proc.returncode != 0:
        return False
    if stdout:
        return f'[stdout]\n{stdout.decode()}'
    if stderr:
        return f'[stderr]\n{stderr.decode()}'


# --------------------------------------------------------------------------
# YouTube helpers
# --------------------------------------------------------------------------
def get_playlist_videos(playlist_url):
    if Playlist is None:
        logger.error("pytube is not available")
        return None, None
    try:
        playlist = Playlist(playlist_url)
        playlist_title = playlist.title
        videos = {}
        for video in playlist.videos:
            try:
                videos[video.title] = video.watch_url
            except Exception as e:
                logger.error(f"Could not retrieve video details: {e}")
        return playlist_title, videos
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return None, None


def get_all_videos(channel_url):
    ydl_opts = {'quiet': True, 'extract_flat': True, 'skip_download': True}
    with YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(channel_url, download=False)
        if result and 'entries' in result:
            channel_name = result['title']
            all_videos = list(result['entries'])
            video_links = {index + 1: (video['title'], video['url'])
                           for index, video in enumerate(all_videos)}
            return video_links, channel_name
        return None, None


def save_to_file(video_links, channel_name):
    sanitized_channel_name = re.sub(r'[^\w\s-]', '', channel_name).strip().replace(' ', '_')
    filename = f"{sanitized_channel_name}.txt"
    with open(filename, 'w', encoding='utf-8') as file:
        for number, (title, url) in video_links.items():
            if url.startswith("https://"):
                formatted_url = url
            elif "shorts" in url:
                formatted_url = f"https://www.youtube.com{url}"
            else:
                formatted_url = f"https://www.youtube.com/watch?v={url}"
            file.write(f"{number}. {title}: {formatted_url}\n")
    return filename


# --------------------------------------------------------------------------
# Video download
# --------------------------------------------------------------------------
def ytdlp_args(output, use_aria=True, extra=None):
    """Build a yt-dlp argument list (never a shell string)."""
    # '%' has a special meaning in yt-dlp output templates
    safe_out = output.replace("%", "%%")
    args = ["yt-dlp", "--newline", "--no-warnings", "--no-playlist",
            "-R", "10", "--fragment-retries", "10",
            "--merge-output-format", "mp4", "-N", "8"]
    if use_aria and shutil.which("aria2c"):
        args += ["--downloader", "aria2c", "--downloader-args", ARIA_ARGS]
    if extra:
        args += list(extra)
    args += ["-o", safe_out]
    return args


def find_output(name_or_path):
    """yt-dlp can change the extension; locate whatever it really wrote."""
    if os.path.isfile(name_or_path):
        return name_or_path
    base = os.path.splitext(name_or_path)[0]
    for ext in ("mp4", "mkv", "webm", "mp4.webm", "mov"):
        if os.path.isfile(f"{base}.{ext}"):
            return f"{base}.{ext}"
    for p in glob.glob(glob.escape(base) + ".*"):
        if not p.endswith((".part", ".ytdl", ".aria2", ".jpg")):
            return p
    return None


def _cleanup_partial(output):
    base = os.path.splitext(output)[0]
    for p in glob.glob(glob.escape(base) + "*"):
        if p.endswith((".part", ".ytdl", ".aria2")) or ".part" in p:
            try:
                os.remove(p)
            except OSError:
                pass


def probe_url(url):
    """
    Look at what an API/CDN url answers BEFORE handing it to yt-dlp, so a real
    reason (expired token, bad quality, 403 ...) is shown instead of the
    useless "returned non-zero exit status 1".
    """
    try:
        r = requests.get(url, stream=True, timeout=30, allow_redirects=True,
                         headers={"User-Agent": UA})
    except requests.RequestException as e:
        raise DownloadError(f"Server not reachable: {e}")
    try:
        ctype = (r.headers.get("content-type") or "").lower()
        if r.status_code >= 400 or "json" in ctype or "html" in ctype:
            body = ""
            try:
                body = next(r.iter_content(2048), b"").decode(errors="ignore")
            except Exception:
                pass
            msg = body
            try:
                j = json.loads(body)
                msg = (j.get("message") or j.get("error") or j.get("detail") or body) \
                    if isinstance(j, dict) else body
            except Exception:
                pass
            msg = re.sub(r"<[^>]+>", " ", str(msg)).strip()[:300]
            raise DownloadError(f"Server replied HTTP {r.status_code}: {msg or 'no details'}")
    finally:
        r.close()


def _direct_stream(url, output, headers=None):
    h = {"User-Agent": UA}
    h.update(headers or {})
    with requests.get(url, stream=True, timeout=60, headers=h, allow_redirects=True) as r:
        if r.status_code >= 400:
            raise DownloadError(f"HTTP {r.status_code} on direct download")
        ctype = (r.headers.get("content-type") or "").lower()
        if "json" in ctype or "html" in ctype:
            raise DownloadError("Server returned a web/JSON page instead of a video")
        with open(output, "wb") as fd:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    fd.write(chunk)
    if not os.path.isfile(output) or os.path.getsize(output) < 1024:
        raise DownloadError("Downloaded file is empty")
    return output


async def robust_download(url, output, extra=None, headers=None, direct_fallback=True, preflight=False):
    """
    1) yt-dlp + aria2c  2) yt-dlp native downloader  3) plain HTTP stream.
    Returns the real output path or raises DownloadError with the real reason.
    """
    if preflight:
        await asyncio.to_thread(probe_url, url)

    last_err = ""
    attempts = [True, False]
    for use_aria in attempts:
        _cleanup_partial(output)
        args = ytdlp_args(output, use_aria=use_aria, extra=extra) + [url]
        logger.info("running: %s", redact(" ".join(args)))
        rc, out, err = await run_args(args)
        found = find_output(output)
        if rc == 0 and found:
            return found
        last_err = tail(err or out)
        logger.error("yt-dlp failed (aria=%s) rc=%s: %s", use_aria, rc, redact(last_err))
        await asyncio.sleep(2)

    if direct_fallback:
        try:
            _cleanup_partial(output)
            return await asyncio.to_thread(_direct_stream, url, output, headers)
        except DownloadError as e:
            last_err = f"{last_err}\n{e}".strip()
        except Exception as e:
            last_err = f"{last_err}\n{e}".strip()

    raise DownloadError(redact(last_err) or "yt-dlp failed with no output")


async def download_video(url, cmd, name):
    """
    Generic downloader used for YouTube / jw / visionias / others.
    `cmd` is a list of yt-dlp arguments (without the url) or None.
    Returns the downloaded file path (raises DownloadError on failure).
    """
    out = f"{name}.mp4"
    extra = None
    if isinstance(cmd, (list, tuple)):
        extra = list(cmd)
    # visionias links are flaky -> a few extra tries
    tries = 3 if "visionias" in url else 1
    last = None
    for _ in range(tries):
        try:
            return await robust_download(url, out, extra=extra, direct_fallback=False)
        except DownloadError as e:
            last = e
            await asyncio.sleep(5)
    raise last


# --------------------------------------------------------------------------
# Telegram upload
# --------------------------------------------------------------------------
async def send_doc(bot: Client, m: Message, cc, ka, cc1, prog, count, name):
    reply = await m.reply_text(f"Uploading » `{name}`")
    await asyncio.sleep(1)
    await m.reply_document(ka, caption=cc1)
    await reply.delete(True)
    await asyncio.sleep(1)
    os.remove(ka)


async def send_vid(bot: Client, m: Message, cc, filename, thumb, name, prog):
    try:
        await prog.delete(True)
    except Exception:
        pass
    reply = await m.reply_text(f"**⥣ Uploading ...** » `{name}`")

    dur = int(duration(filename))
    width, height = video_size(filename)
    auto_thumb = f"{filename}.jpg"

    thumbnail = None
    if thumb and thumb != "no" and os.path.isfile(thumb):
        thumbnail = thumb
    else:
        # grab a frame from the middle (a fixed 00:01:00 fails on short videos)
        ts = max(min(dur // 2, 60), 0)
        await run_args(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(ts),
                        "-i", filename, "-vframes", "1", auto_thumb])
        if os.path.isfile(auto_thumb):
            thumbnail = auto_thumb

    caption = cc if len(cc) <= 1024 else cc[:1020] + "..."
    start_time = time.time()
    kwargs = dict(caption=caption, progress=progress_bar, progress_args=(reply, start_time))
    try:
        try:
            await m.reply_video(filename, supports_streaming=True,
                                height=height or 720, width=width or 1280,
                                thumb=thumbnail, duration=dur, **kwargs)
        except FloodWait:
            raise
        except Exception as e:
            logger.error("reply_video failed (%s) -> sending as document", e)
            await m.reply_document(filename, thumb=thumbnail, **kwargs)
    finally:
        for p in (filename, auto_thumb):
            try:
                if os.path.isfile(p):
                    os.remove(p)
            except OSError:
                pass
        try:
            await reply.delete(True)
        except Exception:
            pass
