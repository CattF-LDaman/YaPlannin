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

Choose one deployment path:

**Local Python**

- **Python 3.10+** (3.11 or 3.12 recommended)
- **Windows, macOS, or Linux**
- A browser (Chrome, Firefox, Edge, etc.)

On Windows, the server listens on **port 80** by default, which may require running the terminal as Administrator. See [Troubleshooting](#troubleshooting) if you hit permission errors.

**Docker**

- **Docker Engine** and **Docker Compose v2**
- A browser

Docker runs the app on **port 8080** by default. See [Docker deployment](#docker-deployment).

---

## Installation

### 1. Get the source

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

## Docker deployment

The recommended way to run YaPlannin on a server or without installing Python locally.

### Prerequisites

- Docker Engine
- Docker Compose v2 (`docker compose` command)

### First run

1. Clone the repository and enter the project folder (see [Installation](#installation) step 1).

2. Copy the example environment file and optionally set a bootstrap admin:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` if you want the first user created automatically on startup:

   ```env
   YAP_BOOTSTRAP_USER=admin
   YAP_BOOTSTRAP_PASSWORD=your-secure-password
   ```

3. Build and start the container:

   ```bash
   docker compose up -d --build
   ```

4. Open **http://localhost:8080/login** in your browser.

   Docker maps host port **8080** to the container by default. Change `YAP_HOST_PORT` in `.env` if that port is already in use.

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `YAP_HOST_PORT` | `8080` | Host port mapped to the container web UI |
| `YAP_PORT` | `8080` | Port the app listens on inside the container |
| `YAP_HOST` | `0.0.0.0` | Bind address inside the container |
| `YAP_DATA_DIR` | `/data/YaPServer` | Persistent data directory inside the container |
| `YAP_BOOTSTRAP_USER` | *(unset)* | Username to create on first startup if no users exist |
| `YAP_BOOTSTRAP_PASSWORD` | *(unset)* | Password for the bootstrap user |

See [`.env.example`](.env.example) for a copy-paste template.

### Create the first user (Docker)

There are no default logins. Use one of these approaches:

**Option A — Bootstrap env vars (recommended)**

Set `YAP_BOOTSTRAP_USER` and `YAP_BOOTSTRAP_PASSWORD` in `.env` before the first `docker compose up`. The user is created only if it does not already exist.

**Option B — Server terminal**

Attach to the running container and type `createuser` at the prompt. This requires an interactive TTY and is less convenient than bootstrap env vars:

```bash
docker compose exec -it yap sh
# Inside the container, the server process owns stdin; bootstrap env vars are easier.
```

**Option C — Web UI command box**

After logging in, enable **Logs** on the home page and run `createuser <user> <pass>` in the command input. This only works once you already have an account.

### Data persistence

Docker stores all server data in a named volume (`yap-data`), mounted at `/data/YaPServer` inside the container:

| Folder / file | Contents |
|---------------|----------|
| `users/` | Account files (hashed passwords) |
| `storage/YaP.db` | Plan metadata (SQLite) |
| `storage/<plan-id>/` | Per-plan databases |
| `logs/` | Server log files |
| `configs/` | Server configuration |

**Back up the volume** before upgrades or removal:

```bash
docker run --rm -v yaplannin_yap-data:/data alpine tar czf - YaPServer > yap-backup.tar.gz
```

Restore (with the stack stopped):

```bash
docker run --rm -i -v yaplannin_yap-data:/data alpine tar xzf - -C /data < yap-backup.tar.gz
```

### Day-to-day operations

```bash
docker compose logs -f          # follow server logs
docker compose restart          # restart the container
docker compose down             # stop (data volume is kept)
docker compose down -v          # stop and DELETE all plans/users (destructive)
```

The container includes a health check that polls the `/login` page every 30 seconds.

### Docker troubleshooting

**Container keeps restarting**

Check logs: `docker compose logs --tail 50`. Common causes: missing dependency (rebuild with `--build`), syntax error in mounted code if you bind-mount the repo.

**Port already in use**

Change `YAP_HOST_PORT` in `.env` (e.g. `8081`) and run `docker compose up -d` again. Open `http://localhost:8081/login`.

**Bootstrap user already exists**

If `YAP_BOOTSTRAP_USER` is set but that user already exists, startup continues normally and the message `already exists, skipping` appears in the logs. Log in with the existing password or use `changepass` after login via the web command box.

**Wrong credentials at login**

Ensure the bootstrap user was created on first run (check logs for `Bootstrap user '...' created`). Usernames are case-sensitive.

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
| Docker | Named volume `yap-data` → `/data/YaPServer` inside the container |

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

Use environment variables instead of editing source code.

**Local Python:**

```bash
YAP_PORT=8080 python run_server.py
```

Then open **http://localhost:8080**.

**Docker:**

Set `YAP_HOST_PORT` in `.env` (host-side mapping) and restart:

```env
YAP_HOST_PORT=8081
```

```bash
docker compose up -d
```

Open **http://localhost:8081/login**.

You can also set `YAP_PORT` inside the container if needed; Docker Compose passes it via `docker-compose.yml`.

---

## Troubleshooting

### "Permission denied" or port 80 won't bind (Windows / local)

- Run PowerShell or Command Prompt **as Administrator**, then start the server again, **or**
- Use a port above 1024: `YAP_PORT=8080 python run_server.py` (see [Change the port](#change-the-port))

### Docker container won't start or keeps restarting

- Run `docker compose logs --tail 50` and look for tracebacks
- Rebuild: `docker compose up -d --build`
- See [Docker troubleshooting](#docker-troubleshooting)

### Port already in use (Docker)

- Change `YAP_HOST_PORT` in `.env` and run `docker compose up -d` again

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

**Local Python**

```text
# Start server
python run_server.py

# Start on alternate port
YAP_PORT=8080 python run_server.py

# Create first user (in server terminal)
createuser alice s3cure_pass

# Browser
http://localhost

# Stop server (in server terminal)
stop
```

**Docker**

```text
# First run
cp .env.example .env
docker compose up -d --build

# Browser
http://localhost:8080/login

# Logs
docker compose logs -f

# Stop (keep data)
docker compose down

# Stop and delete all data
docker compose down -v
```

---

## Version

Current version: **0.0.1** (dev build). Run `version` in the server terminal to confirm what's running.

Made with ❤️ by Luwe Daman.
