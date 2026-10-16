# roast-bot

A small Discord bot for a private  server. When one particular user uses one of his "favourite" words, the bot replies to his message with a random (friendly) roast.

## Why this project exists

It started as a joke. I also used it as a chance to build something small with real users, and to do the basics properly instead of copying a tutorial. Even a tiny bot needs the things that matter in production code:

- **Secrets handling:** the bot token is loaded from a `.env` file. It is never hardcoded, logged, or committed.
- **Careful text matching:** the regex is case-insensitive, matches whole words only, and escapes its input, so "bs" does not match inside "absolutely".
- **Fair randomness:** a shuffle bag uses every insult once before any repeats, and never sends the same insult twice in a row.
- **Hot reload:** the word and insult lists can be edited while the bot runs, with no restart. A broken edit is rejected and the last good list is kept.
- **Fail fast:** a missing or empty list at startup stops the bot with a clear error.
- **Least privilege:** the bot uses only the Message Content intent. It can ping only the person it replies to, never `@everyone`, roles or other users.
- **Privacy:** private lists and secrets stay out of git. Logs record which word matched, never the message itself.
- **Tested and measured:** pytest covers parsing, matching, the shuffle bag and hot reload. Every reply logs its response time.

## What it does

- Watches **one** target user, identified by Discord user ID. It ignores everyone else and all bots.
- Acts only in channels under a configured set of **categories**. Threads count when their parent channel is in one of those categories.
- When his message contains a word from `trigger-words.txt`, the bot replies directly to that message with **one** random line from `insults.txt` and pings him.
- Sends exactly one reply per message, even when the message contains several trigger words.
- Has **no cooldown**: every message that contains a trigger word gets an immediate reply.

## Quick start

For experienced users. You need Python 3.10+ and a Discord bot with **Message Content Intent** turned on.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env                           # paste your bot token into .env
Copy-Item trigger-words.example.txt trigger-words.txt
Copy-Item insults.example.txt insults.txt             # then edit both lists
python bot.py
```

Before running, put your target user ID and category IDs in the config block at the top of `bot.py`. `.env`, `trigger-words.txt` and `insults.txt` are in `.gitignore`, so your token and real lists never end up in git. New to this? Follow the full walkthrough below.

## Setup from zero (step by step)

New to Python or Discord bots? This is the full walkthrough, with no knowledge assumed. It takes about 20 minutes. The Install section above is the short version of the same steps.

These commands are for Windows PowerShell. On Mac or Linux, activate the environment with `source .venv/bin/activate` and use `cp` instead of `Copy-Item`.

### Step 1: Install Python

1. Download Python 3.10 or newer from [python.org/downloads](https://www.python.org/downloads/).
2. In the installer, **tick "Add python.exe to PATH"** before you click Install. This is the step people forget.
3. Open PowerShell and check it worked:

```powershell
python --version
```

You should see something like `Python 3.14.x`.

### Step 2: Get the project and open a terminal in it

1. Download the project as a ZIP (on GitHub: **Code → Download ZIP**) and extract it, or clone it with git.
2. Open the extracted folder in File Explorer, click the address bar at the top, type `powershell` and press Enter. A terminal opens already inside the project folder.

### Step 3: Create the environment and install the dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

When it works, your prompt starts with `(.venv)`. If PowerShell says running scripts is disabled, run this once and try again:

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 4: Create your own bot on Discord

Every person needs their own bot. Never share a bot token (see the warning in Step 6).

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) and click **New Application**. Give it a name and click **Create**.
2. Open the **Bot** tab in the left sidebar.
3. Turn **Public Bot** off, so only you can add it to servers.
4. Scroll to **Privileged Gateway Intents** and turn **Message Content Intent** on. Without it the bot cannot read messages. Leave the other two intents off.
5. Click **Save Changes**.
6. If you see a red error saying a private application cannot have a default authorization link, open **Installation** in the left sidebar, set **Install Link** to **None**, save, and go back to the Bot tab.

### Step 5: Invite the bot to your server

1. In the Developer Portal, open **OAuth2**, then scroll to **OAuth2 URL Generator**.
2. Under **Scopes**, tick only **bot**.
3. Under **Bot Permissions**, tick **View Channels**, **Send Messages**, **Send Messages in Threads** and **Read Message History**. Tick nothing else, and especially not Administrator.
4. Copy the **Generated URL** at the bottom and open it in your browser.
5. Choose your server in the dropdown and click **Authorize**. You need the **Manage Server** permission in that server.

The bot now appears in your member list, shown as offline until you run it.

### Step 6: Put your bot token in `.env`

1. In the Developer Portal, open the **Bot** tab, click **Reset Token**, confirm, and click **Copy**. Discord shows the token **only once**.
2. Create your settings file and open it:

```powershell
Copy-Item .env.example .env
notepad .env
```

3. Replace everything after the `=` with your token, so the line looks like this, with no spaces and no quotes:

```text
DISCORD_TOKEN=paste-your-token-here
```

4. Save the file.

**Warning:** the token is the bot's password. Never post it in chat, in a screenshot, or on GitHub. The `.env` file is already listed in `.gitignore`, so git ignores it. If a token ever leaks, click **Reset Token** again and paste the new one. The old one stops working immediately.

### Step 7: Create your lists

```powershell
Copy-Item trigger-words.example.txt trigger-words.txt
Copy-Item insults.example.txt insults.txt
```

Open both files in Notepad or VS Code and replace the sample lines with your own. Keep the format: one entry per line, starting with a number, a dot and a space (`1. word`). Trigger words have no final dot, and insults end with theirs. Save both files as UTF-8. More details are in "Editing trigger words and insults" below.

### Step 8: Tell the bot who to watch and where

The bot needs three kinds of Discord IDs.

1. In Discord, open **User Settings → Advanced** and turn on **Developer Mode**.
2. Right-click the target person's name and choose **Copy User ID**.
3. Right-click each **category** (the group header in the channel list) the bot should watch, and choose **Copy Category ID**.
4. Open `bot.py` (`notepad bot.py` works) and replace the example numbers in the config block at the top:

```python
TARGET_USER_ID = 123456789012345678

ALLOWED_CATEGORY_IDS = frozenset({
    111111111111111111,
    222222222222222222,
})
```

Each category ID goes on its own line, followed by a comma. Save the file.

### Step 9: Run it

```powershell
python bot.py
```

Wait for these two lines:

```text
Loaded 3 trigger words and 3 insults
Ready: logged in as YourBot#1234 (id ...)
```

Your bot now shows as online in Discord. Test it by writing a trigger word as the target user in a channel under one of your categories. To test on your own, temporarily put your own user ID in `TARGET_USER_ID`, restart the bot, and change it back afterwards. Press `Ctrl+C` in the terminal to stop the bot.

Every time you want to run it later:

```powershell
cd path\to\roast-bot
.\.venv\Scripts\Activate.ps1
python bot.py
```

### Troubleshooting

| What you see | What to do |
|---|---|
| `python` is not recognized | Reinstall Python and tick "Add python.exe to PATH". Or try `py` instead of `python`. |
| Running scripts is disabled | Run `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`, then activate the environment again. |
| `Connection timeout to host https://discord.com` | Your network cannot reach Discord. In countries where Discord is blocked, turn on a VPN that covers the whole computer, then restart the bot. |
| `Improper token has been passed` | The token is wrong. Click Reset Token, copy the new one, and paste it after `DISCORD_TOKEN=` with no spaces or quotes. |
| `PrivilegedIntentsRequired` | Turn on **Message Content Intent** in the Developer Portal (Bot tab), click Save Changes, and restart the bot. |
| Error about a missing or empty list file | Do Step 7 and check that both files contain at least one numbered line. |
| The bot is online but never replies | Check that `TARGET_USER_ID` is right, that the channel is under a category in `ALLOWED_CATEGORY_IDS`, that the word is in `trigger-words.txt` without a final dot, and that the bot can see the channel. Then read the terminal for errors. |
| `403 Forbidden ... Missing Permissions` in the terminal | The bot is not allowed to post in that channel. Give it **Send Messages** in the channel's permission settings, or **Send Messages in Threads** for threads. |

## Usage

Start the bot:

```powershell
python bot.py
```

Leave the window open. Press `Ctrl+C` to stop the bot.

### Editing trigger words and insults

Both files use the same format: one entry per line, each starting with a number, a dot and a space.

`trigger-words.txt`:

```text
1. heck
2. darn
3. fiddlesticks
```

`insults.txt`:

```text
1. You type like a potato with Wi-Fi.
2. Even autocorrect has given up on you.
```

- **Add** an entry by adding a new line. **Remove** one by deleting its line. **Edit** one by changing its text.
- **The numbers are ignored.** They exist only to make the list readable, so they don't need to be in order or unique. Blank lines are skipped.
- **Case doesn't matter** for trigger words: `heck` matches `heck`, `Heck` and `HECK`.
- **Matching is whole-word only.** `ass` matches "ass!" but not "class". Punctuation around the word is fine.
- **Add spelling variants as separate lines.** The bot has no fuzzy matching, so `heck`, `hecking` and `hek` each need their own line.
- Insults are sent exactly as written, including the final period.
- **Save the files as UTF-8.** In Notepad, pick "UTF-8" in the Save As dialog. This also keeps emoji and accented letters intact.
- **Edits apply automatically.** Before using a list, the bot checks whether the file changed and reloads it if so, so you don't need to restart. If an edited file is empty or can't be read, the bot keeps the previous list and logs a warning.

### Changing which categories the bot watches

Open `bot.py` and find the config block at the top:

```python
ALLOWED_CATEGORY_IDS = frozenset({
    111111111111111111,
    222222222222222222,
})
```

Replace the numbers with your category IDs, one per line, each followed by a comma. To get a category ID, turn on **Developer Mode** in Discord (User Settings → Advanced), then right-click the category and choose **Copy Category ID**. Restart the bot after changing `bot.py`. Only the two list files reload automatically.

### Changing the target user

In the same config block, set `TARGET_USER_ID` to the person's user ID. With Developer Mode on, right-click their name and choose **Copy User ID**. Then restart the bot.

```python
TARGET_USER_ID = 123456789012345678
```

### Console output

```text
2026-10-16 18:02:11 INFO     roast-bot Loaded 3 trigger words and 3 insults
2026-10-16 18:02:13 INFO     roast-bot Ready: logged in as RoastBot#1234 (id 1234567890)
2026-10-16 18:05:40 INFO     roast-bot Replied in #general: matched 'heck', response time 287 ms
2026-10-16 18:07:02 INFO     roast-bot Reloaded Insults: 4 entries
```

The log records which word matched, never the message text.

## How it works

All the code is in `bot.py`.

| Piece | What it does |
|---|---|
| `parse_numbered_lines` / `load_list` | Reads a list file (UTF-8, including files Notepad saves with a byte-order mark), strips the `N. ` prefixes and skips blank lines. At startup, a missing or empty file stops the bot with a clear error. |
| `ReloadingList` | Holds one list and the file's last modification time. `refresh()` reloads the file only when that time has changed. If the reload fails or the file is empty, it keeps the old entries and logs one warning. |
| `build_trigger_pattern` | Escapes every trigger word with `re.escape` and joins them into one case-insensitive regex, `(?<!\w)(?:word1\|word2…)(?!\w)`. The lookarounds mean "no letter or digit directly before or after", which makes matching whole-word while still allowing punctuation. |
| `ShuffleBag` | Shuffles all insults and hands them out one at a time. When they run out it reshuffles, and if the next round would start with the insult just sent, it swaps that one with another. When the list is reloaded, a new round starts with the new insults. |
| `Roaster` | Joins the pieces. `match()` refreshes the trigger list (rebuilding the regex if it changed) and searches the message. `next_insult()` refreshes the insult list (refilling the shuffle bag if it changed) and draws one. |
| `on_message` | Checks, in order: is the author the target user and not a bot? Is the channel, or a thread's parent, in an allowed category? Does the message contain a trigger word? If yes to all, it sends one reply and logs the matched word and the response time. |

## Tests

```powershell
python -m pytest -v
```

| File | What it covers |
|---|---|
| `tests/test_parsing.py` | Numbered prefixes, blank lines, final periods, Windows line endings, the byte-order mark, missing and empty files. |
| `tests/test_matching.py` | Case-insensitivity, whole words only (`absolutely`, `class` and `bass` don't match), punctuation, regex escaping. |
| `tests/test_shufflebag.py` | Every round uses each insult exactly once. A new round never starts with the previous round's last insult, checked across many random seeds and with duplicate lines. |
| `tests/test_hot_reload.py` | Changed files reload and unchanged ones don't. Empty, badly encoded and deleted files keep the old list and log a warning. New triggers and insults take effect without a restart. |

## Measured response time

**_TBD_ ms**: the time between his message and the bot's reply, measured with Discord's own timestamps on both messages (`reply.created_at - message.created_at`) and logged for every reply.

## Customizing and extending

### Works today

- Adding, removing and editing trigger words and insults in the two list files, applied automatically while the bot runs.
- Changing the target user (`TARGET_USER_ID`) and the watched categories (`ALLOWED_CATEGORY_IDS`) in the config block at the top of `bot.py`, then restarting.

The bot watches exactly one user and has no cooldown.

### Planned (not implemented)

These are ideas for future work. **None of them exist in the code yet.**

- **Several target users**, each tracked separately.
- **Per-user lists:** different trigger words and insults for each user.
- **Per-user settings in a config file** (for example YAML or JSON) instead of constants in `bot.py`.
- **Replying in the language of the message**, such as Arabic or Hebrew, using separate insult lists per language.
- **Languages without spaces**, such as Chinese, where whole-word regex matching doesn't work and needs a different approach, such as word segmentation.
- **An optional cooldown**, off by default, to limit how often the bot replies.
- **An on/off command for admins** to pause and resume the bot from Discord.
- **Running as a hosted service**, so the bot stays online without a PC left running.
