"""Roast bot: replies to one specific user with a random insult when he uses a trigger word."""

import logging
import os
import random
import re
import sys
from pathlib import Path

import discord
from dotenv import load_dotenv

# --- Config ---------------------------------------------------------------

TARGET_USER_ID = 757937911533404230

ALLOWED_CATEGORY_IDS = frozenset({
    1366054158540603412,
    852867224721031179,
    1366056965364781167,
})

BASE_DIR = Path(__file__).resolve().parent
TRIGGER_FILE = BASE_DIR / "trigger-words.txt"
INSULT_FILE = BASE_DIR / "insults.txt"

# --------------------------------------------------------------------------

log = logging.getLogger("roast-bot")

_NUMBER_PREFIX = re.compile(r"^\d+\.\s*")


def parse_numbered_lines(text: str) -> list[str]:
    """Return non-blank lines with any leading "N. " prefix removed."""
    entries = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        line = _NUMBER_PREFIX.sub("", line, count=1).strip()
        if line:
            entries.append(line)
    return entries


def load_list(path: Path, label: str) -> list[str]:
    """Load a numbered list file, exiting with a clear error if it is missing or empty."""
    try:
        text = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        sys.exit(f"Error: {label} file not found: {path}")
    entries = parse_numbered_lines(text)
    if not entries:
        sys.exit(f"Error: {label} file contains no entries: {path}")
    return entries


def build_trigger_pattern(words: list[str]) -> re.Pattern[str]:
    """Build a case-insensitive, whole-word regex matching any of the trigger words."""
    escaped = [re.escape(w) for w in sorted(set(words), key=len, reverse=True)]
    return re.compile(r"(?<!\w)(?:" + "|".join(escaped) + r")(?!\w)", re.IGNORECASE)


def find_trigger(pattern: re.Pattern[str], text: str) -> str | None:
    """Return the first trigger word found in text (lowercased), or None."""
    match = pattern.search(text)
    return match.group(0).lower() if match else None


class ShuffleBag:
    """Hands out every item once in random order before reshuffling.

    The first item of a new round never equals the last item of the previous one
    (unless every item is identical, which makes that impossible).
    """

    def __init__(self, items: list[str], rng: random.Random | None = None):
        if not items:
            raise ValueError("ShuffleBag needs at least one item")
        self._items = list(items)
        self._rng = rng or random.Random()
        self._bag: list[str] = []
        self._pos = 0
        self._last: str | None = None

    def _refill(self) -> None:
        self._bag = self._items[:]
        self._rng.shuffle(self._bag)
        self._pos = 0
        if self._last is not None and self._bag[0] == self._last:
            for i in range(1, len(self._bag)):
                if self._bag[i] != self._last:
                    self._bag[0], self._bag[i] = self._bag[i], self._bag[0]
                    break

    def set_items(self, items: list[str]) -> None:
        """Replace the items and start a fresh round on the next draw."""
        if not items:
            raise ValueError("ShuffleBag needs at least one item")
        self._items = list(items)
        self._bag = []
        self._pos = 0

    def next(self) -> str:
        if self._pos >= len(self._bag):
            self._refill()
        item = self._bag[self._pos]
        self._pos += 1
        self._last = item
        return item


class ReloadingList:
    """A list file that is reloaded when its modification time changes.

    If a reload fails (missing file, bad encoding, no entries) the previous
    entries are kept and a warning is logged.
    """

    def __init__(self, path: Path, label: str):
        self.path = path
        self.label = label
        self.items = load_list(path, label)
        self._mtime = path.stat().st_mtime_ns
        self._unreadable = False

    def refresh(self) -> bool:
        """Reload the file if it changed. Returns True if new entries were loaded."""
        try:
            mtime = self.path.stat().st_mtime_ns
        except OSError as exc:
            if not self._unreadable:
                log.warning("%s file unavailable, keeping %d old entries: %s",
                            self.label, len(self.items), exc)
                self._unreadable = True
            return False
        self._unreadable = False
        if mtime == self._mtime:
            return False

        # Record the new mtime even on failure so a bad file warns once, not on every message.
        self._mtime = mtime
        try:
            entries = parse_numbered_lines(self.path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeDecodeError) as exc:
            log.warning("Could not reload %s file, keeping %d old entries: %s",
                        self.label, len(self.items), exc)
            return False
        if not entries:
            log.warning("%s file is empty, keeping %d old entries", self.label, len(self.items))
            return False

        self.items = entries
        log.info("Reloaded %s: %d entries", self.label, len(entries))
        return True


class Roaster:
    """Matches trigger words and hands out insults, picking up list edits on the fly."""

    def __init__(self, triggers: ReloadingList, insults: ReloadingList,
                 rng: random.Random | None = None):
        self.triggers = triggers
        self.insults = insults
        self._pattern = build_trigger_pattern(triggers.items)
        self._bag = ShuffleBag(insults.items, rng)

    def match(self, text: str) -> str | None:
        if self.triggers.refresh():
            self._pattern = build_trigger_pattern(self.triggers.items)
        return find_trigger(self._pattern, text)

    def next_insult(self) -> str:
        if self.insults.refresh():
            self._bag.set_items(self.insults.items)
        return self._bag.next()


def category_id_of(channel) -> int | None:
    """Category ID of a channel, using the parent channel for threads."""
    if isinstance(channel, discord.Thread):
        channel = channel.parent
    return getattr(channel, "category_id", None)


def create_client(roaster: Roaster) -> discord.Client:
    intents = discord.Intents.default()
    intents.message_content = True

    client = discord.Client(
        intents=intents,
        allowed_mentions=discord.AllowedMentions(
            everyone=False, roles=False, users=False, replied_user=True
        ),
    )

    @client.event
    async def on_ready():
        log.info("Ready: logged in as %s (id %s)", client.user, client.user.id)

    @client.event
    async def on_message(message: discord.Message):
        if message.author.bot or message.author.id != TARGET_USER_ID:
            return
        if category_id_of(message.channel) not in ALLOWED_CATEGORY_IDS:
            return

        word = roaster.match(message.content)
        if word is None:
            return

        try:
            reply = await message.reply(roaster.next_insult(), mention_author=True)
        except discord.HTTPException as exc:
            log.warning("Failed to reply in #%s: %s", message.channel, exc)
            return

        response_ms = (reply.created_at - message.created_at).total_seconds() * 1000
        log.info(
            "Replied in #%s: matched '%s', response time %.0f ms",
            message.channel, word, response_ms,
        )

    return client


def main() -> None:
    discord.utils.setup_logging()

    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        sys.exit("Error: DISCORD_TOKEN is not set. Copy .env.example to .env and add your bot token.")

    triggers = ReloadingList(TRIGGER_FILE, "Trigger words")
    insults = ReloadingList(INSULT_FILE, "Insults")
    log.info("Loaded %d trigger words and %d insults", len(triggers.items), len(insults.items))

    client = create_client(Roaster(triggers, insults))
    client.run(token, log_handler=None)


if __name__ == "__main__":
    main()
