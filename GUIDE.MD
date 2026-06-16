# YaPlannin — Setup & Usage Guide

YaPlannin is a self-hosted planning tool for breaking big goals into tasks, tracking effort over time, and staying on schedule. You run it on your own computer (or server), open it in a browser, and manage your plans from there.

---

## What it does

YaPlannin helps you plan projects by effort and deadline, not just to-do lists.

- **Plans** — separate projects, each with its own tasks and data
- **Tasks & subtasks** — break work into chunks with start/end dates and required effort (in minutes)
- **Work sessions** — log time you actually spent on a task or subtask
- **Dashboard** — warnings for upcoming deadlines, lagging tasks, and a "pressure meter" when you're behind
- **Schedule** — week-by-week view of logged work
- **Accounts** — login-protected; each user has their own plans

The app runs as a local web server. After you start it, you use it at `http://localhost` in your browser.

---

## Requirements

- **Python 3.10+** (3.11 or 3.12 recommended)
- **Windows, macOS, or Linux**
- A browser (Chrome, Firefox, Edge, etc.)

On Windows, the server listens on **port 80**, which may require running the terminal as Administrator. See [Troubleshooting](#troubleshooting) if you hit permission errors.

---

## Installation

### 1. Get the code

Clone or download the repository, then open a terminal in the project folder:

```bash
git clone https://github.com/CattF-LDaman/YaPlannin.git
cd YaPlannin
```

### 2. Create a virtual environment (recommended)

**Windows (PowerShell):**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Optional — Conda:** If you use Conda, create an environment named `YaP` (to match `run_server.bat`), install Python 3.11+, then run `pip install -r requirements.txt`.

### 3. Start the server

**Windows:**

```powershell
python run_server.py
```

Or double-click `run_server.bat` (expects a Conda env named `YaP`).

**macOS / Linux:**

```bash
python run_server.py
```

You should see a log file path printed, then `You can now input commands.` The web UI starts automatically.

### 4. Open the app

Go to **http://localhost** in your browser.

---

## First-time setup: create a user

There are no default logins. Before anyone can use the GUI, an admin must create a user from the **server terminal** (the window where you ran `run_server.py`).

```text
createuser myusername mypassword
```

Rules:

- **Username** — letters, numbers, and underscores only (no spaces)
- **Password** — can include spaces and special characters

Then open **http://localhost/login** and sign in.

### Other admin commands

Type these in the server terminal (or enable **Logs** on the home page and use the command box there):

| Command | Description |
|---------|-------------|
| `help` | List all commands |
| `createuser <user> <pass>` | Create a login (alias: `cuser`) |
| `changepass <user> <pass>` | Change a password (alias: `cpass`) |
| `removeuser <user>` | Delete a user (alias: `remuser`) |
| `version` | Show version (alias: `build`) |
| `stop` | Shut down the server (alias: `exit`) |

Passwords are not echoed in logs when you use `createuser` or `changepass`.

You can also create additional users from the web UI: click your username → **Add**.

---

## How to use the app

### Home page — Plans

After logging in you land on the **Plans** page.

1. Click **New** to create a plan (name + short description).
2. Click **View** on a plan card to open it.

Plans belong to the logged-in user. Other accounts do not see your plans unless sharing is added in a future version.

### Inside a plan

Each plan has three tabs and a floating **+** button.

#### Dashboard

Overview of how the plan is going:

- **Pressure meter** — red if you're behind overall, green if ahead
- **Warnings** — deadlines today/this week, tasks lagging behind schedule
- **Work** — total effort done, this week, today, completion %
- **Progress** — per-task schedule status
- **Deadlines** — upcoming end dates for tasks and subtasks

#### Tasks

- Expand tasks to see description, effort, completion, and subtasks
- Add **tasks** (top-level work items) and **subtasks** (pieces of a task)
- Each task/subtask has:
  - **Start / end date** (end is optional)
  - **Required effort** in minutes
- Use the **+** menu → **Task** to add or edit tasks

#### Schedule

- Week view (Monday–Sunday) of logged work sessions
- Navigate with previous/next week controls
- See which task or subtask each session was for

#### Logging work

Use **+** → **Work** to record time spent:

1. Pick a **task** (and optional **subtask**)
2. Add a short **note**
3. Set the **date** (defaults to today)
4. Slide **minutes worked** — the max is limited by remaining effort on that task/subtask

Work updates effort-done metrics and feeds the dashboard and schedule.

### Account settings

Click your username in the header → **Account**:

- Change password
- Create another user
- Delete your account
- Log out

---

## Where your data is stored

YaPlannin does **not** keep plans inside the git repo. Everything is stored locally on the machine running the server:

| OS | Location |
|----|----------|
| Windows | `%LOCALAPPDATA%\YaPServer\` |
| macOS | `~/Library/Application Support/YaPServer/` |
| Linux | `~/.local/share/YaPServer/` |

Under that folder:

| Folder / file | Contents |
|---------------|----------|
| `users/` | Account files (hashed passwords) |
| `storage/YaP.db` | Plan metadata (SQLite) |
| `storage/<plan-id>/` | Per-plan databases (tasks, work, etc.) |
| `logs/` | Server log files |
| `configs/` | Server configuration |

**Back up** the whole `YaPServer` folder if you care about your plans. Copying the repo alone is not enough.

---

## Running on another machine or for others on your network

By default the app binds to port **80** on all interfaces. Others on your LAN can try `http://<your-computer-ip>/` once the server is running and your firewall allows it.

For internet exposure, use a reverse proxy (nginx, Caddy), HTTPS, and strong passwords. This project is aimed at personal/local use.

### Change the port

If port 80 is blocked or needs admin rights, edit `YaP/YaPServer/GUI/__init__.py` and change `port=80` in the `ui.run(...)` call near the bottom of the file (e.g. `port=8080`). Then open `http://localhost:8080`.

---

## Troubleshooting

### "Permission denied" or port 80 won't bind (Windows)

- Run PowerShell or Command Prompt **as Administrator**, then start the server again, **or**
- Change the port to something above 1024 (e.g. 8080) as described above

### Page won't load

- Confirm the server terminal is still running and shows no crash traceback
- Check the latest file in `%LOCALAPPDATA%\YaPServer\logs\` (Windows) for errors

### "Wrong credentials" at login

- Create the user first with `createuser` in the server terminal
- Usernames are case-sensitive and must match exactly

### `ModuleNotFoundError: No module named 'nicegui'`

Activate your virtual environment and run:

```bash
pip install -r requirements.txt
```

### Plans disappeared after reinstalling

User data lives in `%LOCALAPPDATA%\YaPServer` (or the macOS/Linux paths above), not in the project folder. Re-cloning the repo does not delete plans unless you removed that data directory.

---

## Quick reference

```text
# Start server
python run_server.py

# Create first user (in server terminal)
createuser alice s3cure_pass

# Browser
http://localhost

# Stop server (in server terminal)
stop
```

---

## Version

Current version: **0.0.1** (dev build). Run `version` in the server terminal to confirm what's running.

Made with ❤️ by Luwe Daman.
