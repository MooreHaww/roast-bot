<div align="center">

# 🔥 roast-bot

**A tiny Discord bot with one job: when one particular friend says one of his favourite words, it fires back with a random (friendly) roast.**

![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![discord.py](https://img.shields.io/badge/discord.py-2.6%2B-5865F2?style=for-the-badge&logo=discord&logoColor=white)
![Tests](https://img.shields.io/badge/tests-33%20passing-brightgreen?style=for-the-badge)
![Reply time](https://img.shields.io/badge/median%20reply-~670%20ms-orange?style=for-the-badge)
![Release](https://img.shields.io/badge/release-v1.0.1-E8457C?style=for-the-badge)

</div>

---

## 💡 Why this project exists

It started as a joke for our family server of cousins and friends. It also became a chance to build something small **with real users**, and to do the basics properly instead of copying a tutorial. Even a tiny bot needs the things that matter in production code:

- 🔐 **Secrets handling:** the bot token lives in a `.env` file and is never hardcoded, logged or committed.
- 🔎 **Careful text matching:** case-insensitive, whole words only, and regex-escaped, so "bs" never matches inside "absolutely".
- 🎲 **Fair randomness:** a shuffle bag uses every insult once before any repeats, and never sends the same one twice in a row.
- ♻️ **Hot reload:** edit the word and insult lists while the bot runs. A broken edit is rejected and the last good list is kept.
- 🛑 **Fail fast:** a missing or empty list at startup stops the bot with a clear error.
- 🧱 **Least privilege:** only the Message Content intent, and it can ping only the person it replies to, never `@everyone` or roles.
- 🙈 **Privacy:** private lists and secrets stay out of git, and logs record which word matched, never the message.
- ✅ **Tested and measured:** pytest covers parsing, matching, the shuffle bag and hot reload, and every reply logs its response time.

## 🔎 What it does

- Watches **one** target user (by Discord user ID) and ignores everyone else and all bots.
- Works only in channels under a configured set of **categories**. Threads count when their parent channel is in one.
- When his message contains a word from `trigger-words.txt`, it replies to that message with **one** random line from `insults.txt` and pings him.
- Sends exactly one reply per message, even if several trigger words appear.
- Has **no cooldown**: every message with a trigger word gets an immediate reply.

Example console output:

```text
2026-10-16 18:02:11 INFO     roast-bot Loaded 3 trigger words and 3 insults
2026-10-16 18:02:13 INFO     roast-bot Ready: logged in as RoastBot#1234 (id 1234567890)
2026-10-16 18:05:40 INFO     roast-bot Replied in #general: matched 'heck', response time 287 ms
2026-10-16 18:07:02 INFO     roast-bot Reloaded Insults: 4 entries
```

**Measured:** about **670 ms** median over 18 replies (range 195 to 2841 ms), taken from Discord's own timestamps on his message and the reply. The bot ran on a home PC in Istanbul through a VPN, so a host closer to Discord should be faster.

## ⚙️ Setup

You need Python 3.10+ and a Discord bot with **Message Content Intent** turned on. Commands below are for Windows PowerShell; on Mac or Linux use `source .venv/bin/activate` and `cp`.

```powershell
git clone https://github.com/MooreHaww/roast-bot.git
cd roast-bot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env                           # paste your bot token into .env
Copy-Item trigger-words.example.txt trigger-words.txt
Copy-Item insults.example.txt insults.txt             # then edit both lists
python bot.py
```

If PowerShell says running scripts is disabled, run `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` once.

<details>
<summary><b>🤖 Create the Discord bot and find the IDs (click to expand)</b></summary>

1. In the [Discord Developer Portal](https://discord.com/developers/applications) click **New Application**, then open the **Bot** tab.
2. Turn **Public Bot** off and turn **Message Content Intent** on (leave the other intents off). Save.
3. Open **OAuth2 → URL Generator**. Under Scopes tick only **bot**. Under Permissions tick **View Channels**, **Send Messages**, **Send Messages in Threads** and **Read Message History**. Open the generated URL and add the bot to your server.
4. On the **Bot** tab click **Reset Token**, copy it, and put it in `.env` as `DISCORD_TOKEN=your-token` (no spaces, no quotes). The token is the bot's password: never share it, and reset it if it leaks.
5. In Discord turn on **Developer Mode** (User Settings → Advanced). Right-click the target person and **Copy User ID**, and right-click each category to watch and **Copy Category ID**.
6. Put those IDs in the config block at the top of `bot.py`:

```python
TARGET_USER_ID = 123456789012345678

ALLOWED_CATEGORY_IDS = frozenset({
    111111111111111111,
    222222222222222222,
})
```

</details>

**Editing the lists.** Both files use one entry per line, each starting with a number, a dot and a space (`1. heck`). The numbers are ignored, blank lines are skipped, matching ignores case, and only whole words match, so add spelling variants as separate lines. Save as UTF-8. Changes apply automatically while the bot runs.

**Run the tests:**

```powershell
python -m pytest -v
```

| Problem | Fix |
|---|---|
| `Connection timeout to host https://discord.com` | Discord is blocked on your network. Use a VPN that covers the whole computer |
| `Improper token has been passed` | Reset the token and paste it after `DISCORD_TOKEN=` |
| `PrivilegedIntentsRequired` | Turn on **Message Content Intent**, save, restart |
| Online but never replies | Check `TARGET_USER_ID`, that the channel is under an allowed category, and the word has no trailing dot |
| `403 Forbidden ... Missing Permissions` | Give the bot **Send Messages** (or **in Threads**) in that channel |

## 🎯 What I wanted to learn

- Building and running a real bot with `discord.py`, including intents and permissions.
- Writing **robust text matching** with regex: escaping, word boundaries, case-insensitivity.
- Handling secrets properly and keeping private data out of version control.
- Designing a **fair random picker** (a shuffle bag) instead of plain `random.choice`.
- Hot-reloading configuration safely: only swap in a new list if it loads and is not empty.
- Testing small pieces in isolation, and measuring real latency instead of guessing.

## 🏗️ How it was built

I described the idea, planned it, built it step by step with each change reviewed, and tested it myself on a live server. All the code is in `bot.py`:

| Piece | What it does |
|---|---|
| `parse_numbered_lines` / `load_list` | Reads a list file (UTF-8, including a byte-order mark), strips the `N. ` prefixes and skips blank lines. A missing or empty file stops startup |
| `ReloadingList` | Remembers the file's modification time and reloads only when it changes. A failed reload keeps the old entries and logs one warning |
| `build_trigger_pattern` | Escapes every word with `re.escape` and joins them into one case-insensitive regex with "no letter or digit directly before or after" lookarounds |
| `ShuffleBag` | Deals all insults in random order, reshuffles when empty, and never starts a new round with the insult just sent |
| `Roaster` | Joins the pieces: refreshes the lists, matches the message, draws an insult |
| `on_message` | Checks author, bot status, category (or thread parent) and trigger word, then replies once and logs the matched word and response time |

**Tests** (`tests/`, 33 in total): list parsing, matching edge cases (`absolutely`, `class` and `bass` must not match), shuffle-bag fairness over many random seeds, and hot reload (changed files reload, bad files keep the old list).

## 🗺️ Plan / what's next

Everything above works today. **The ideas below are planned and are not in the code yet:**

- [x] Single target user, categories, shuffle bag, hot reload, tests
- [x] Measured response time
- [ ] Several target users, each tracked separately, with per-user word and insult lists
- [ ] Settings in a config file (YAML or JSON) instead of constants in `bot.py`
- [ ] Reply in the language of the message, with a separate list per language
- [ ] Support languages without spaces (such as Chinese), where whole-word regex does not work
- [ ] An optional cooldown, off by default
- [ ] An admin command to pause and resume the bot from Discord
- [ ] Hosting it so the bot stays online without a PC left running

## 📄 Notes

Private repository for a private server. The real trigger words and insults are kept out of git on purpose.
