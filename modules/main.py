import os
import re
import sys
import json
import time
import base64
import asyncio
import logging
import requests
import urllib.parse
from urllib.parse import quote, urlparse
from logging.handlers import RotatingFileHandler

import cloudscraper
from aiohttp import ClientSession
from pyromod import listen  # noqa: F401  (adds bot.listen)
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from pyrogram.enums import ChatType

import core as helper
from core import DownloadError, redact
from vars import API_ID, API_HASH, BOT_TOKEN

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler("logs.txt", maxBytes=50000000, backupCount=10),
        logging.StreamHandler(),
    ],
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logger = logging.getLogger("bot")

# Initialize the bot
bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

my_name = "Mr_X45"
PW_API = "https://ankitshakyaxapi.vercel.app/download"
VALID_RES = ("144", "240", "360", "480", "720", "1080")
DEFAULT_RES = "480"

_here = os.path.dirname(os.path.abspath(__file__))
_cookie_candidates = [
    os.getenv("COOKIES_FILE_PATH", ""),
    "youtube_cookies.txt",
    os.path.join(_here, "youtube_cookies.txt"),
    os.path.join(_here, "..", "youtube_cookies.txt"),
]
cookies_file_path = next((p for p in _cookie_candidates if p and os.path.isfile(p)), None)

DEFAULT_PW_TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzYxNTE3MzAuMTI2LCJkYXRhIjp7Il9pZCI6IjYzMDRjMmY3Yzc5NjBlMDAxODAwNDQ4NyIsInVzZXJuYW1lIjoiNzc2MTAxNzc3MCIsImZpcnN0TmFtZSI6IkplZXYgbmFyYXlhbiIsImxhc3ROYW1lIjoic2FoIiwib3JnYW5pemF0aW9uIjp7Il9pZCI6IjVlYjM5M2VlOTVmYWI3NDY4YTc5ZDE4OSIsIndlYnNpdGUiOiJwaHlzaWNzd2FsbGFoLmNvbSIsIm5hbWUiOiJQaHlzaWNzd2FsbGFoIn0sImVtYWlsIjoiV1dXLkpFRVZOQVJBWUFOU0FIQEdNQUlMLkNPTSIsInJvbGVzIjpbIjViMjdiZDk2NTg0MmY5NTBhNzc4YzZlZiJdLCJjb3VudHJ5R3JvdXAiOiJJTiIsInR5cGUiOiJVU0VSIn0sImlhdCI6MTczNTU0NjkzMH0.iImf90mFu_cI-xINBv4t0jVz-rWK1zeXOIwIFvkrS0M"
)

BCOV_AUTH = (
    'bcov_auth=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE3MjQyMzg3OTEsImNvbiI6eyJpc0FkbWluIjpmYWxzZSwiYXVzZXIiOiJVMFZ6TkdGU2NuQlZjR3h5TkZwV09FYzBURGxOZHowOSIsImlkIjoiZEUxbmNuZFBNblJqVEROVmFWTlFWbXhRTkhoS2R6MDkiLCJmaXJzdF9uYW1lIjoiYVcxV05ITjVSemR6Vm10ak1WUlBSRkF5ZVNzM1VUMDkiLCJlbWFpbCI6Ik5Ga3hNVWhxUXpRNFJ6VlhiR0ppWTJoUk0wMVdNR0pVTlU5clJXSkRWbXRMTTBSU2FHRnhURTFTUlQwPSIsInBob25lIjoiVUhVMFZrOWFTbmQ1ZVcwd1pqUTViRzVSYVc5aGR6MDkiLCJhdmF0YXIiOiJLM1ZzY1M4elMwcDBRbmxrYms4M1JEbHZla05pVVQwOSIsInJlZmVycmFsX2NvZGUiOiJOalZFYzBkM1IyNTBSM3B3VUZWbVRtbHFRVXAwVVQwOSIsImRldmljZV90eXBlIjoiYW5kcm9pZCIsImRldmljZV92ZXJzaW9uIjoiUShBbmRyb2lkIDEwLjApIiwiZGV2aWNlX21vZGVsIjoiU2Ftc3VuZyBTTS1TOTE4QiIsInJlbW90ZV9hZGRyIjoiNTQuMjI2LjI1NS4xNjMsIDU0LjIyNi4yNTUuMTYzIn19.snDdd-PbaoC42OUhn5SJaEGxq0VzfdzO49WTmYgTx8ra_Lz66GySZykpd2SxIZCnrKR6-R10F5sUSrKATv1CDk9ruj_ltCjEkcRq8mAqAytDcEBp72-W0Z7DtGi8LdnY7Vd9Kpaf499P-y3-godolS_7ixClcYOnWxe2nSVD5C9c5HkyisrHTvf6NFAuQC_FD3TzByldbPVKK0ag1UnHRavX8MtttjshnRhv5gJs5DQWj4Ir_dkMcJ4JaVZO3z8j0OxVLjnmuaRBujT-1pavsr1CCzjTbAcBvdjUfvzEhObWfA1-Vl5Y4bUgRHhl1U-0hne4-5fF0aouyu71Y6W0eg'
)

VISION_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Language': 'en-US,en;q=0.9', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive',
    'Pragma': 'no-cache', 'Referer': 'http://www.visionias.in/', 'Sec-Fetch-Dest': 'iframe',
    'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'cross-site', 'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RMX2121) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36',
    'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"', 'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
}


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def jwt_expiry(token):
    """Return the exp (unix time) of a JWT, or None if it can't be read."""
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return float(json.loads(base64.urlsafe_b64decode(payload))["exp"])
    except Exception:
        return None


def clean_name(text):
    for ch in ("\t", ":", "/", "\\", "+", "#", "|", "@", "*", ".", "?", '"', "'",
               "<", ">", "`", "$", "%", "\r", "\n"):
        text = text.replace(ch, "")
    return text.replace("https", "").replace("http", "").strip()


def parse_links(text):
    """Split 'Title:https://url' lines; ignore blank / broken lines."""
    links = []
    for line in text.splitlines():
        line = line.strip()
        if not line or "://" not in line:
            continue
        links.append(line.split("://", 1))
    return links


def build_pw_url(url, token, quality):
    """
    Build the PW downloader-API url. The txt link already carries
    parentId/childId/videoId, so they stay as separate query params.
    Any old token=/quality= in the link is dropped so they never duplicate.
    """
    base, _, rest = url.partition("&")
    if rest:
        rest = "&".join(p for p in rest.split("&")
                        if p and not p.lower().startswith(("token=", "quality=")))
    url = f"{PW_API}?mpd_url={base}"
    if rest:
        url += f"&{rest}"
    if token:
        url += f"&token={token}"
    return f"{url}&quality={quality}"


def extract_content_id(url):
    """URL se content ID extract karega"""
    try:
        for key in ("contentId=", "contentHashId=", "contentHashIdl="):
            if key in url:
                content_id = url.split(key, 1)[1]
                for char in ("?", "&"):
                    content_id = content_id.split(char)[0]
                if ".m3u8" in content_id:
                    content_id = content_id.split(".m3u8")[0]
                return content_id or None
        return None
    except Exception as e:
        logger.error(f"Error extracting content ID: {e}")
        return None


def get_jw_signed_url(content_id, access_token):
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en",
        "Origin": "https://web.classplusapp.com",
        "Referer": "https://web.classplusapp.com/",
        "Region": "IN",
        "User-Agent": "Mozilla/5.0",
        "X-Access-Token": access_token,
    }

    # 1. First try: contentId
    content_api = ("https://api.classplusapp.com/cams/uploader/video/"
                   f"jw-signed-url?contentId={quote(content_id, safe='')}")
    try:
        r = requests.get(content_api, headers=headers, timeout=15)
        if r.ok:
            signed_url = r.json().get("url")
            if signed_url:
                hostname = (urlparse(signed_url).hostname or "").lower()
                if hostname == "akamai-cdn.classplusapp.com":
                    return signed_url
    except Exception as e:
        logger.error(f"classplus contentId lookup failed: {e}")

    # 2. Fallback: same ID as liveSessionId
    live_api = ("https://api.classplusapp.com/cams/uploader/video/"
                f"jw-signed-url?liveSessionId={quote(content_id, safe='')}&isAgora=2")
    r = requests.get(live_api, headers=headers, timeout=15)
    r.raise_for_status()
    signed_url = r.json().get("url")
    if not signed_url:
        raise DownloadError("Classplus did not return a video url (token expired / wrong id?)")
    return signed_url


async def pwdlx_video(url, output_filename):
    """Physics Wallah downloader-API video."""
    return await helper.robust_download(url, output_filename, preflight=True)


async def new_classplus_cdn(url, raw_text2, output_filename):
    fmt = (f"bestvideo[height<={raw_text2}]+bestaudio/"
           f"best[height<={raw_text2}]/bestvideo+bestaudio/best")
    extra = ["-f", fmt,
             "--add-header", "Origin: https://web.classplusapp.com",
             "--add-header", "Referer: https://web.classplusapp.com/"]
    return await helper.robust_download(url, output_filename, extra=extra,
                                        direct_fallback=False)


async def fetch_visionias(url):
    async with ClientSession() as session:
        async with session.get(url, headers=VISION_HEADERS) as resp:
            text = await resp.text()
    found = re.search(r"(https://.*?playlist.m3u8.*?)\"", text)
    if not found:
        raise DownloadError("visionias: playlist.m3u8 not found on the page")
    return found.group(1)


async def download_pdf(url, name):
    """cloudscraper first (handles protected hosts), yt-dlp as fallback."""
    out = f"{name}.pdf"
    url = url.replace(" ", "%20")

    def _get():
        scraper = cloudscraper.create_scraper()
        resp = scraper.get(url, timeout=60)
        if resp.status_code != 200:
            raise DownloadError(f"Failed to download PDF: {resp.status_code} {resp.reason}")
        with open(out, "wb") as f:
            f.write(resp.content)

    try:
        await asyncio.to_thread(_get)
    except Exception as first:
        rc, _, err = await helper.run_args(
            ["yt-dlp", "-o", out.replace("%", "%%"), "-R", "25", "--fragment-retries", "25", url])
        if rc != 0 or not os.path.isfile(out):
            raise DownloadError(f"{first}")
    return out


def classify(url):
    p = urlparse(url)
    host = (p.hostname or "").lower()
    path = p.path.lower()
    if p.netloc == "ankitshakyaxapi.vercel.app" or host == "ankitshakyaxapi.vercel.app":
        return "pw"
    if host == "akamai-cdn.classplusapp.com":
        return "classplus"
    if "drive.google.com" in host or "docs.google.com" in host:
        return "drive"
    if path.endswith(".pdf"):
        return "pdf"
    if path.endswith((".jpg", ".jpeg", ".png")):
        return "image"
    return "video"


def redact_for_chat(url):
    return redact(url)[:600]


class Data:
    START = (
        "🌟 Welcome Dear🧸😘 {0}! 🌟\n\n"
    )


# Define the start command handler
@bot.on_message(filters.command("start"))
async def start(client: Client, msg: Message):
    if msg.from_user:
        tgname = msg.from_user.mention
    elif msg.chat.type == ChatType.CHANNEL:
        tgname = msg.chat.title or "None"
    else:
        tgname = "None"

    start_message = await client.send_message(msg.chat.id, Data.START.format(tgname))

    steps = [
        "Initializing Uploader bot...😚🤖\n\nProgress: [⬜⬜⬜⬜⬜⬜⬜⬜⬜] 0%\n\n",
        "Loading features...😗⏳\n\nProgress: [🟥🟥🟥⬜⬜⬜⬜⬜⬜] 25%\n\n",
        "This may take a moment, sit back and relax!🫣💪\n\nProgress: [🟧🟧🟧🟧🟧⬜⬜⬜⬜] 50%\n\n",
        "Checking Bot Status...😙🔍\n\nProgress: [🟨🟨🟨🟨🟨🟨🟨⬜⬜] 75%\n\n",
        "Checking status Okay... Command is Private Dear🫂.**Bot Made BY @rahulx45_vibe**🔍\n\nProgress:[🟩🟩🟩🟩🟩🟩🟩🟩🟩] 100%\n\n",
    ]
    for step in steps:
        await asyncio.sleep(1)
        try:
            await start_message.edit_text(Data.START.format(tgname) + step)
        except Exception:
            pass


@bot.on_message(filters.command(["stop"]))
async def restart_handler(_, m):
    await m.reply_text("⚪**WORK IS STOPPED**🔵", True)
    os.execl(sys.executable, sys.executable, *sys.argv)


def make_captions(style, count, name1, b_name, CR):
    if style == "mrx45":
        cc = (f"🎬 **𝐕𝐈𝐃𝐄𝐎 𝐈𝐃** ➭ `{count}` 『𝐌𝐑-𝐗𝟒𝟓』 \n\n❖ **𝐓𝐈𝐓𝐋𝐄** ➭ **{name1}** @rahulx45_vibe\n\n"
              f"❖ **𝗕𝗔𝗧𝗖𝗛** ➭ **{b_name}** \n\n❖ **𝐃𝐎𝐖𝐍𝐋𝐎𝐀𝐃𝐄𝐃 𝐁𝐘** : **{CR}**\n\n```\n━━━✰𝐁𝐘~𝐌𝐑-𝐑𝐀𝐇𝐔𝐋✰━━━\n```")
        cc1 = (f"📚 **𝗣𝗗𝗙 𝗜𝗗** ➭ `{count}` 『𝐌𝐑-𝐗𝟒𝟓』 \n\n❖ **𝐓𝐈𝐓𝐋𝐄** ➭ **{name1}** @rahulx45_vibe\n\n"
               f"❖ **𝗕𝗔𝗧𝗖𝗛** ➭ **{b_name}** \n\n❖ **𝐃𝐎𝐖𝐍𝐋𝐎𝐀𝐃𝐄𝐃 𝐁𝐘** : **{CR}**\n\n```\n━━━✰𝐁𝐘~𝐌𝐑-𝐑𝐀𝐇𝐔𝐋✰━━━\n```")
        ccimg = (f"❖ **𝗜𝗠𝗔𝗚𝗘 𝗜𝗗** ➪ `{count}`『𝐌𝐑-𝐗𝟒𝟓』 \n\n❖ **𝐓𝐈𝐓𝐋𝐄** ➪ \n** {name1} ** 🖼✨\n\n"
                 f"❖ **𝗕𝗔𝗧𝗖𝗛 𝗡𝗔𝗠𝗘** ➪ \n** {b_name} ** 🍁\n\n✈️ **𝐃𝐎𝐖𝐍𝐋𝐎𝐀𝐃𝐄𝐃 𝐁𝐘** ➪ **{CR}**\n\n```\n══**『𝑷𝑶𝑾𝑬𝑹𝑬𝑫 𝑩𝒀 𝑴𝑹-𝑿𝟒𝟓』**══\n```")
    else:
        cc = (f"🎬 **𝐕𝐈𝐃𝐄𝐎 𝐈𝐃** ➪ `{count}` 『𝐌𝐑-𝐑𝐀𝐇𝐔𝐋』 \n\n❖ **𝐓𝐈𝐓𝐋𝐄** ➪ **{name1}** @rahulx45_vibe\n\n"
              f"❖ **𝗕𝗔𝗧𝗖𝗛 𝗡𝗔𝗠𝗘** ➪ **{b_name}** \n\n❖ **𝐃𝐎𝐖𝐍𝐋𝐎𝐀𝐃𝐄𝐃 𝐁𝐘** ➪ **{CR}**\n\n══**『𝑷𝑶𝑾𝑬𝑹𝑬𝑫 𝑩𝒀 𝑴𝑹-𝑿𝟒𝟓』**══")
        cc1 = (f"📚 **𝗣𝗗𝗙 𝗜𝗗** ➪ `{count}` 『𝐌𝐑-𝐑𝐀𝐇𝐔𝐋』 \n\n❖ **𝐓𝐈𝐓𝐋𝐄** ➪ **{name1}** @rahulx45_vibe\n\n"
               f"❖ **𝗕𝗔𝗧𝗖𝗛 𝗡𝗔𝗠𝗘** ➪ **{b_name}** \n\n❖ **𝐃𝐎𝐖𝐍𝐋𝐎𝐀𝐃𝐄𝐃 𝐁𝐘** ➪ **{CR}**\n\n══**『𝑷𝑶𝑾𝑬𝑹𝑬𝑫 𝑩𝒀 𝑴𝑹-𝑿𝟒𝟓』**══")
        ccimg = (f"❖ **𝗜𝗠𝗔𝗚𝗘 𝗜𝗗** ▸ `{count}`𝐌𝐫-𝐗𝟒𝟓\n\n❖ **𝐓𝐈𝐓𝐋𝐄** ▸ \n**❝ {name1} ❞** 🖼✨\n\n"
                 f"❖ **𝗕𝗔𝗧𝗖𝗛 𝗡𝗔𝗠𝗘** ▸ \n**❝ {b_name} ❞** 🍁\n\n✈️ **𝐃𝐎𝐖𝐍𝐋𝐎𝐀𝐃𝐄𝐃 𝐁𝐘** ➪ **{CR}**\n\n════ **『 𝑷𝑶𝑾𝑬𝑹𝑬𝑫 𝑩𝒀 𝑴𝑹-𝑿𝟒𝟓 』** ════")
    return cc, cc1, ccimg


async def process_txt(bot: Client, m: Message, style: str):
    editable = await m.reply_text(
        f"╭───❮ **MR_X45 TXT LEECHER** ❯───►\n"
        f"│\n"
        f"├──» **SEND ME THE TXT FILE TO BEGIN** 📥\n"
        f"├──» **JUST WAIT AND WATCH THE MAGIC** ⚡\n"
        f"│\n"
        f"╰───╭⚡ **POWERED BY MR_X45** ⚡╯───►"
    )
    input: Message = await bot.listen(editable.chat.id)
    if not input.document:
        await m.reply_text("Are yaar **txt** file Bhejni thi \n\n **Chal koi na, command dobara chalao aur txt file bhejo🫂.**")
        return
    x = await input.download()
    await input.delete(True)
    file_name, ext = os.path.splitext(os.path.basename(x))
    credit = "@rahulx45_vibe"

    try:
        # utf-8 is essential: Hindi titles break the default (ASCII) locale in Docker
        with open(x, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        links = parse_links(content)
    except Exception:
        await m.reply_text("Are yaar **txt** file Bhejni thi \n\n **Chal koi na, command dobara chalao aur txt file bhejo🫂.**")
        return
    finally:
        try:
            os.remove(x)
        except OSError:
            pass

    if not links:
        await m.reply_text("❌ Txt file me koi valid link nahi mila (format: `Title:https://link`).")
        return

    await editable.edit(f"╭───❮ **TOTAL LINKS FOUND:** `{len(links)}` ❯───►\n├──» **ENTER START INDEX:** *(DEFAULT IS 1)* 🔢\n╰───╭⚡ **[ Mr_X45 Studio ]** ⚡╯───►")
    input0: Message = await bot.listen(editable.chat.id)
    raw_text = input0.text
    await input0.delete(True)
    try:
        arg = int(raw_text)
        if arg < 1:
            arg = 1
    except Exception:
        arg = 1

    await editable.edit("**ENTER YOUR BATCH NAME OR SEND** `/Rahul` **FOR EXTRACTING NAME FROM TEXT FILENAME.**")
    input1: Message = await bot.listen(editable.chat.id)
    raw_text0 = input1.text
    await input1.delete(True)
    b_name = file_name if raw_text0 == '/Rahul' else raw_text0

    await editable.edit(
        f"╭───❮ **SELECT RESOLUTION** ❯───►\n"
        f"├──» **144**\n├──» **240**\n├──» **360**\n├──» **480**\n├──» **720**\n├──» **1080**\n"
        f"╰───╭⚡ **[ Mr_X45 ]** ⚡╯───►"
    )
    input2: Message = await bot.listen(editable.chat.id)
    raw_text2 = (input2.text or "").strip()
    await input2.delete(True)
    if raw_text2 not in VALID_RES:
        # e.g. "48" (typo of 480) used to be sent to the server as quality=48 and fail
        await m.reply_text(f"⚠️ `{raw_text2}` valid resolution nahi hai, **{DEFAULT_RES}p** use kar raha hoon.")
        raw_text2 = DEFAULT_RES

    await editable.edit("╭───❮ **CREDITS SETUP** ❯───►\n├──» **ENTER UPLOADER NAME OR SEND** `/Rahul` **FOR DEFAULT** 🎓\n╰───╭⚡ **[ @rahulx45_vibe ]** ⚡╯───►")
    input3: Message = await bot.listen(editable.chat.id)
    raw_text3 = input3.text
    await input3.delete(True)
    CR = credit if raw_text3 in ('/Rahul', '/Cutie', '/Love') else raw_text3

    await editable.edit("╭───❮ **PW TOKEN SETUP** ❯───►\n├──» **ENTER PW TOKEN OR SEND** `/X45` **FOR DEFAULT** 🔑\n╰───╭⚡ **[ Mr_X45 Studio ]** ⚡╯───►")
    input4: Message = await bot.listen(editable.chat.id)
    raw_text4 = (input4.text or "").strip()
    await input4.delete(True)
    access_token = DEFAULT_PW_TOKEN if raw_text4 in ('/X45', '/vip') else raw_text4

    exp = jwt_expiry(access_token)
    if exp and exp < time.time():
        when = time.strftime('%d-%b-%Y %H:%M UTC', time.gmtime(exp))
        await m.reply_text(
            f"⚠️ **Token expire ho chuka hai** (expiry: `{when}`).\n"
            f"PW / Classplus links fail honge. Naya token lekar `/stop` karke dobara chalao.\n"
            f"Main phir bhi try kar raha hoon...")

    await editable.edit("╭───❮ **THUMBNAIL SETUP** ❯───►\n├──» **SEND THUMBNAIL URL** (Ending with .jpg) **OR SEND** `no` 🖼️\n╰───╭⚡ **[ Mr_X45 Studio ]** ⚡╯───►")
    input6: Message = await bot.listen(editable.chat.id)
    thumb_text = (input6.text or "").strip()
    await input6.delete(True)
    await editable.delete()

    thumb = "no"
    if thumb_text.startswith(("http://", "https://")):
        try:
            def _thumb():
                r = requests.get(thumb_text, timeout=30)
                r.raise_for_status()
                with open("thumb.jpg", "wb") as f:
                    f.write(r.content)
            await asyncio.to_thread(_thumb)
            thumb = "thumb.jpg"
        except Exception as e:
            await m.reply_text(f"⚠️ Thumbnail download fail ({e}); auto thumbnail use hoga.")

    count = arg
    failed = []
    for i in range(arg - 1, len(links)):
        name1 = clean_name(links[i][0])
        name = f'{str(count).zfill(3)}) {name1[:60]} {my_name}'
        try:
            await process_one(bot, m, style, links[i], name1, name, count, raw_text2,
                              access_token, b_name, CR, thumb)
        except FloodWait as e:
            wait = getattr(e, "value", None) or getattr(e, "x", 5)
            await m.reply_text(f"⏳ FloodWait {wait}s")
            await asyncio.sleep(wait)
            failed.append(count)
        except Exception as e:
            logger.exception("link %s failed", count)
            reason = redact(str(e) or e.__class__.__name__)[:700]
            failed.append(count)
            try:
                await m.reply_text(f"❌ **Failed** `{count}` » `{name1[:60]}`\n\n`{reason}`")
            except Exception:
                pass
        count += 1
        await asyncio.sleep(1)

    if failed:
        await m.reply_text("⚠️ Failed IDs: " + ", ".join(f"`{n}`" for n in failed))
    await m.reply_text("✅ 𝐒𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲 𝐃𝐨𝐧𝐞")


async def process_one(bot, m, style, link, name1, name, count, raw_text2, access_token,
                      b_name, CR, thumb):
    Vxy = (link[1].replace("file/d/", "uc?export=download&id=")
           .replace("www.youtube-nocookie.com/embed", "youtu.be")
           .replace("?modestbranding=1", "")
           .replace("/view?usp=sharing", "")).strip()
    url = "https://" + Vxy

    # ---- resolve special providers -------------------------------------
    if "visionias" in url:
        url = await fetch_visionias(url)
    elif 'https://contentId=' in url or 'contentHashIdl=' in url or 'contentHashId=' in url:
        content_id = extract_content_id(url)
        if not content_id:
            raise DownloadError("Classplus content id not found in link")
        url = await asyncio.to_thread(get_jw_signed_url, content_id, access_token)
    elif ('/master.mpd' in url or "/dash/" in url or ".mp4?" in url or "?Signature=" in url
          or "d1d34p8vz63oiq.cloudfront.net" in url or "parentId=" in url or "childId=" in url):
        if "parentId=" in url or "childId=" in url:
            url = build_pw_url(url, access_token, raw_text2)
        else:
            url = build_pw_url(url, "", raw_text2)

    if "edge.api.brightcove.com" in url:
        url = url.split("bcov_auth")[0] + BCOV_AUTH

    cc, cc1, ccimg = make_captions(style, count, name1, b_name, CR)
    kind = classify(url)
    safe_url = redact_for_chat(url)

    # ---- yt-dlp extra args for the generic downloader ------------------
    if "youtu" in url:
        ytf = f"b[height<={raw_text2}][ext=mp4]/bv[height<={raw_text2}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]"
    else:
        ytf = f"b[height<={raw_text2}]/bv[height<={raw_text2}]+ba/b/bv+ba"

    extra = ["-f", ytf]
    if "jw-prod" in url:
        extra = []
    elif "acecwply" in url:
        extra = ["-f", f"bestvideo[height<={raw_text2}]+bestaudio", "--hls-prefer-ffmpeg"]
    elif ("youtube.com" in url or "youtu.be" in url) and cookies_file_path:
        extra = ["--cookies", cookies_file_path] + extra

    def show_text(title=""):
        return (f"{title}✰🖥️𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐢𝐧𝐠 𝗪𝗮𝗶𝘁..🤖🚀»\n\n📝 Title:- `{name}`\n\n🖥️ 𝐐𝐮𝐥𝐢𝐭𝐲 » `{raw_text2}`\n\n"
                f"**🔗 𝐔𝐑𝐋 »** `{safe_url}`\n\n**𝐁𝐨𝐭 𝐌𝐚𝐝𝐞 𝐁𝐲🧸: ✦ @rahulx45_vibe**")

    if kind == "drive":
        ka = await helper.download(url, name)
        await bot.send_document(chat_id=m.chat.id, document=ka, caption=cc1)
        os.remove(ka)

    elif kind == "pdf":
        ka = await download_pdf(url, name)
        await bot.send_document(chat_id=m.chat.id, document=ka, caption=cc1)
        os.remove(ka)

    elif kind == "image":
        url = url.replace(" ", "%20")

        def _img():
            resp = cloudscraper.create_scraper().get(url, timeout=60)
            if resp.status_code != 200:
                raise DownloadError(f"Failed to download Image: {resp.status_code} {resp.reason}")
            with open(f'{name}.jpg', 'wb') as file:
                file.write(resp.content)

        await asyncio.to_thread(_img)
        await bot.send_photo(chat_id=m.chat.id, photo=f'{name}.jpg', caption=ccimg)
        os.remove(f'{name}.jpg')

    elif kind == "pw":
        prog = await m.reply_text(show_text("**Physics Wallah**\n\n"))
        filename = await pwdlx_video(url, f"{name}.mp4")
        await helper.send_vid(bot, m, cc, filename, thumb, name, prog)

    elif kind == "classplus":
        prog = await m.reply_text(show_text("**ClassPlus**\n\n"))
        filename = await new_classplus_cdn(url, raw_text2, f"{name}.mp4")
        await helper.send_vid(bot, m, cc, filename, thumb, name, prog)

    else:
        prog = await m.reply_text(show_text())
        filename = await helper.download_video(url, extra, name)
        await helper.send_vid(bot, m, cc, filename, thumb, name, prog)


@bot.on_message(filters.command(["Mrx45"]))
async def mrx45_handler(bot: Client, m: Message):
    await process_txt(bot, m, "mrx45")


@bot.on_message(filters.command(["Official"]))
async def official_handler(bot: Client, m: Message):
    await process_txt(bot, m, "official")


if __name__ == "__main__":
    bot.run()
