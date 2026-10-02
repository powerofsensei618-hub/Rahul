# SudoR2spr WOODcraft
# Add your details here (or better: set them as environment variables)
import os

# `or` (instead of a default arg) so an EMPTY env var (e.g. an unset GitHub
# secret) still falls back to the default instead of breaking the login.
API_ID = int(os.environ.get("API_ID") or "39355925")
API_HASH = os.environ.get("API_HASH") or "1ee4d337d7b4b1d01d071c7c7f72fd34"
BOT_TOKEN = os.environ.get("BOT_TOKEN") or ""
