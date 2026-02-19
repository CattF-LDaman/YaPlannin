import os
import uuid
import math
from typing import Optional, List, Dict, Any
from datetime import date

def _uid() -> str:
    return str(uuid.uuid4())


def _parse_time_to_seconds(t: str) -> int:
    """
    Convert HH:MM into seconds since midnight.
    """
    parts = t.split(":")
    if len(parts) != 2:
        raise ValueError("start_time must be HH:MM")

    h, m = parts
    h, m = int(h), int(m)

    if h < 0 or h > 23:
        raise ValueError("Hour must be 0-23")
    if m < 0 or m > 59:
        raise ValueError("Minute must be 0-59")

    return h * 3600 + m * 60


def _seconds_to_time(sec: int) -> str:
    """
    Convert seconds since midnight into HH:MM.
    Wraps around at 24h.
    """
    sec = sec % (24 * 3600)
    h = sec // 3600
    sec %= 3600
    m = sec // 60
    return f"{h:02d}:{m:02d}"


def _calc_end_time(start_time: str, minutes: int) -> str:
    """
    Returns computed end_time HH:MM:SS from start_time + duration minutes.
    """
    start_sec = _parse_time_to_seconds(start_time)
    end_sec = start_sec + (int(minutes) * 60)
    return _seconds_to_time(end_sec)


class PlanData:

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        date_start TEXT NOT NULL,
        date_end TEXT,
        base_effort INTEGER NOT NULL DEFAULT 0,
        effort_done INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS subtasks (
        id TEXT PRIMARY KEY,
        task_id TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        date_end TEXT,
        target_effort INTEGER NOT NULL DEFAULT 0,
        effort_done INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS schedule_days (
        id TEXT PRIMARY KEY,
        day TEXT NOT NULL UNIQUE,
        note TEXT NOT NULL DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS work_log (
        id TEXT PRIMARY KEY,
        day_id TEXT NOT NULL,

        start_time TEXT NOT NULL, -- HH:MM
        minutes INTEGER NOT NULL DEFAULT 0,
        note TEXT NOT NULL DEFAULT '',

        task_id TEXT,
        subtask_id TEXT,

        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(day_id) REFERENCES schedule_days(id) ON DELETE CASCADE,
        FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE,
        FOREIGN KEY(subtask_id) REFERENCES subtasks(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_work_day_id ON work_log(day_id);
    CREATE INDEX IF NOT EXISTS idx_work_task_id ON work_log(task_id);
    CREATE INDEX IF NOT EXISTS idx_work_subtask_id ON work_log(subtask_id);

    CREATE INDEX IF NOT EXISTS idx_subtasks_task_id ON subtasks(task_id);
    """

    def __init__(self, server, plan_id: str, info: dict):
        self.server = server
        self.plan_id = plan_id

        self.info = info
        self.name = info["name"]
        self.description = self.desc = info["description"]
        self.user = info["user"]

        self.location = os.path.join(server.dirs["storage"], plan_id + ".db")

        from .database import init_db, connect
        init_db(self.location, PlanData.SCHEMA)
        self.conn = connect(self.location)

        self.server.log(f"Plan: {self.location}")

    def _fetchone(self, query: str, params=()) -> Optional[Dict[str, Any]]:
        row = self.conn.execute(query, params).fetchone()
        return dict(row) if row else None

    def _fetchall(self, query: str, params=()) -> List[Dict[str, Any]]:
        rows = self.conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def _attach_end_time(self, work: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adds computed end_time to work row dict.
        """
        w = dict(work)
        w["end_time"] = _calc_end_time(w["start_time"], int(w["minutes"]))
        return w

    # ----------------------------
    # TASKS CRUD
    # ----------------------------
    def add_task(self, name: str, description: str, date_start: str, date_end: Optional[str] = None, base_effort: int = 0) -> str:
        task_id = _uid()
        self.conn.execute(
            """
            INSERT INTO tasks (id, name, description, date_start, date_end, base_effort, effort_done)
            VALUES (?, ?, ?, ?, ?, ?, 0)
            """,
            (task_id, name, description, date_start, date_end, int(base_effort)),
        )
        self.conn.commit()
        return task_id

    def update_task(self, task_id: str, name: Optional[str] = None, description: Optional[str] = None, date_start: Optional[str] = None, date_end: Optional[str] = None, base_effort: Optional[int] = None,) -> None:
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        self.conn.execute(
            """
            UPDATE tasks
            SET name = ?, description = ?, date_start = ?, date_end = ?, base_effort = ?
            WHERE id = ?
            """,
            (
                name if name is not None else task["name"],
                description if description is not None else task["description"],
                date_start if date_start is not None else task["date_start"],
                date_end if date_end is not None else task["date_end"],
                int(base_effort) if base_effort is not None else task["base_effort"],
                task_id,
            ),
        )
        self.conn.commit()

    def delete_task(self, task_id: str) -> None:
        self.conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self._fetchone("SELECT * FROM tasks WHERE id = ?", (task_id,))

    def get_tasks(self) -> List[Dict[str, Any]]:
        return self._fetchall("SELECT * FROM tasks ORDER BY date_start ASC")

    def add_task_effort_done(self, task_id: str, minutes: int) -> None:
        if minutes < 0:
            raise ValueError("minutes must be >= 0")
        self.conn.execute(
            "UPDATE tasks SET effort_done = effort_done + ? WHERE id = ?",
            (int(minutes), task_id),
        )
        self.conn.commit()

    # ----------------------------
    # SUBTASKS CRUD
    # ----------------------------
    def add_subtask(self, task_id: str, name: str, description: str, date_end: Optional[str] = None, target_effort: int = 0) -> str:
        if not self.get_task(task_id):
            raise ValueError(f"Cannot create subtask: task not found {task_id}")

        subtask_id = _uid()
        self.conn.execute(
            """
            INSERT INTO subtasks (id, task_id, name, description, date_end, target_effort, effort_done)
            VALUES (?, ?, ?, ?, ?, ?, 0)
            """,
            (subtask_id, task_id, name, description, date_end, int(target_effort)),
        )
        self.conn.commit()
        return subtask_id

    def update_subtask(self, subtask_id: str, name: Optional[str] = None, description: Optional[str] = None, date_end: Optional[str] = None, target_effort: Optional[int] = None) -> None:
        sub = self.get_subtask(subtask_id)
        if not sub:
            raise ValueError(f"Subtask not found: {subtask_id}")

        self.conn.execute(
            """
            UPDATE subtasks
            SET name = ?, description = ?, date_end = ?, target_effort = ?
            WHERE id = ?
            """,
            (
                name if name is not None else sub["name"],
                description if description is not None else sub["description"],
                date_end if date_end is not None else sub["date_end"],
                int(target_effort) if target_effort is not None else sub["target_effort"],
                subtask_id,
            ),
        )
        self.conn.commit()

    def delete_subtask(self, subtask_id: str) -> None:
        self.conn.execute("DELETE FROM subtasks WHERE id = ?", (subtask_id,))
        self.conn.commit()

    def get_subtask(self, subtask_id: str) -> Optional[Dict[str, Any]]:
        return self._fetchone("SELECT * FROM subtasks WHERE id = ?", (subtask_id,))

    def get_subtasks_for_task(self, task_id: str) -> List[Dict[str, Any]]:
        return self._fetchall(
            "SELECT * FROM subtasks WHERE task_id = ? ORDER BY name ASC",
            (task_id,),
        )

    def add_subtask_effort_done(self, subtask_id: str, minutes: int) -> None:
        if minutes < 0:
            raise ValueError("minutes must be >= 0")

        self.conn.execute(
            "UPDATE subtasks SET effort_done = effort_done + ? WHERE id = ?",
            (int(minutes), subtask_id),
        )
        self.conn.commit()

    # ----------------------------
    # Seamless metrics (integrated)
    # ----------------------------
    def get_task_progress(self, task, subtasks):
        # Parse the strings into date objects
        start = date.fromisoformat(task["date_start"])
        end = date.fromisoformat(task["date_end"])
        today = date.today()

        # 1. Get the total amount of days
        # This represents the full duration of the task
        total_duration = (end - start).days

        # 2. Get the progress percentage (0 to 1)
        if total_duration <= 0:
            # Avoid division by zero: if start and end are the same day
            progress = 1.0 if today >= end else 0.0
        else:
            elapsed = (today - start).days
            # Use max/min to clamp the value between 0.0 and 1.0
            # (e.g., if today is before the start date or after the end date)
            progress = max(0.0, min(1.0, elapsed / total_duration))

        subtask_progresses = {}
        for subtask in subtasks:
            sub_end = date.fromisoformat(subtask["date_end"]) if subtask["date_end"] else end
            total_sub_duration = (sub_end - start).days

            # 2. Get the progress percentage (0 to 1)
            if total_sub_duration <= 0:
                # Avoid division by zero: if start and end are the same day
                sub_progress = 1.0 if today >= sub_end else 0.0
            else:
                sub_elapsed = (today - start).days
                # Use max/min to clamp the value between 0.0 and 1.0
                # (e.g., if today is before the start date or after the end date)
                sub_progress = max(0.0, min(1.0, sub_elapsed / total_sub_duration))
            subtask_progresses[subtask["id"]] = total_sub_duration, sub_progress

        return total_duration, progress, subtask_progresses

    def _apply_task_metrics(self, task: Dict[str, Any], subtasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        base_effort = int(task["base_effort"])
        base_done = int(task["effort_done"])

        sub_effort = sum(int(s["target_effort"]) for s in subtasks)
        sub_done = sum(int(s["effort_done"]) for s in subtasks)

        effort = base_effort + sub_effort
        total_done = base_done + sub_done

        percent = (total_done / effort) if effort > 0 else 0.0

        if task["date_end"]:
            base_duration_days, base_progress_necessary, subtask_progresses = self.get_task_progress(task, subtasks)
            base_effort_necessary = math.ceil(base_progress_necessary*base_effort)
            base_effort_behind = max(base_effort_necessary - base_done, 0)
            base_daily_effort = base_effort/base_duration_days
            base_weekly_effort = base_daily_effort * 7
        else:
            base_effort_behind = base_effort_necessary = base_progress_necessary = base_duration_days = base_daily_effort = base_weekly_effort = 0
            subtask_progresses = None

        total_effort_behind = base_effort_behind

        for subtask in subtasks:
            subtask["date_start"] = task["date_start"]
            subtask["full_name"] = f"{task['name']}: {subtask['name']}"

            if subtask_progresses:
                sub_duration_days, sub_progress_necessary = subtask_progresses[subtask["id"]]
                sub_effort_necessary = math.ceil(sub_progress_necessary*subtask["target_effort"])
                sub_effort_behind = max(sub_effort_necessary - subtask["effort_done"], 0)
                sub_daily_effort = subtask["target_effort"]/sub_duration_days
                sub_weekly_effort = sub_daily_effort*7

                subtask["duration_days"] = sub_duration_days
                subtask["progress_necessary"] = sub_progress_necessary
                subtask["effort_necessary"] = sub_effort_necessary
                subtask["effort_behind"] = sub_effort_behind
                subtask["daily_effort"] = sub_daily_effort
                subtask["weekly_effort"] = sub_weekly_effort

                total_effort_behind += sub_effort_behind
            else:
                subtask["duration_days"] = subtask["progress_necessary"] = subtask["effort_necessary"] = subtask["effort_behind"] = subtask["daily_effort"] = subtask["weekly_effort"] = 0


        task = dict(task)
        task["subtasks"] = subtasks
        task["effort"] = effort
        task["total_effort_done"] = total_done
        task["percent_completed"] = percent
        task["duration_days"] = base_duration_days
        task["progress_necessary"] = base_progress_necessary
        task["effort_necessary"] = base_effort_necessary
        task["effort_behind"] = base_effort_behind
        task["total_effort_behind"] = total_effort_behind
        task["daily_effort"] = base_daily_effort
        task["weekly_effort"] = base_weekly_effort

        return task

    def get_task_full(self, task_id: str) -> Optional[Dict[str, Any]]:
        task = self.get_task(task_id)
        if not task:
            return None
        subtasks = self.get_subtasks_for_task(task_id)
        return self._apply_task_metrics(task, subtasks)

    def get_tasks_full(self) -> List[Dict[str, Any]]:
        tasks = self.get_tasks()
        if not tasks:
            return []

        all_subtasks = self._fetchall("SELECT * FROM subtasks")
        sub_by_task: Dict[str, List[Dict[str, Any]]] = {}
        for s in all_subtasks:
            sub_by_task.setdefault(s["task_id"], []).append(s)

        return [
            self._apply_task_metrics(t, sub_by_task.get(t["id"], []))
            for t in tasks
        ]

    # ----------------------------
    # Schedule days
    # ----------------------------
    def get_day(self, day: str) -> Optional[Dict[str, Any]]:
        return self._fetchone("SELECT * FROM schedule_days WHERE day = ?", (day,))

    def ensure_day(self, day: str) -> str:
        existing = self.get_day(day)
        if existing:
            return existing["id"]

        day_id = _uid()
        self.conn.execute(
            "INSERT INTO schedule_days (id, day) VALUES (?, ?)",
            (day_id, day),
        )
        self.conn.commit()
        return day_id

    def get_days(self) -> List[Dict[str, Any]]:
        return self._fetchall("SELECT * FROM schedule_days ORDER BY day ASC")

    # ----------------------------
    # Work
    # ----------------------------
    def add_work(
        self,
        day: str,
        start_time: str,
        minutes: int,
        note: str = "",
        task_id: Optional[str] = None,
        subtask_id: Optional[str] = None,
    ) -> str:
        """
        Adds a work_log row and updates effort_done on task/subtask.

        start_time must be HH:MM
        minutes must be > 0
        Exactly one of task_id/subtask_id must be provided.
        """

        if minutes <= 0:
            raise ValueError("minutes must be > 0")

        _parse_time_to_seconds(start_time)  # validates format

        if (task_id is None and subtask_id is None) or (task_id is not None and subtask_id is not None):
            raise ValueError("Exactly one of task_id or subtask_id must be provided")

        if task_id is not None and not self.get_task(task_id):
            raise ValueError(f"Task not found: {task_id}")

        if subtask_id is not None and not self.get_subtask(subtask_id):
            raise ValueError(f"Subtask not found: {subtask_id}")

        day_id = self.ensure_day(day)
        work_id = _uid()

        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO work_log (id, day_id, start_time, minutes, note, task_id, subtask_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (work_id, day_id, start_time, int(minutes), note, task_id, subtask_id),
            )

            if task_id is not None:
                cur.execute(
                    "UPDATE tasks SET effort_done = effort_done + ? WHERE id = ?",
                    (int(minutes), task_id),
                )

            if subtask_id is not None:
                cur.execute(
                    "UPDATE subtasks SET effort_done = effort_done + ? WHERE id = ?",
                    (int(minutes), subtask_id),
                )

            self.conn.commit()
            return work_id

        except Exception:
            self.conn.rollback()
            raise

    def get_work(self, work_id: str) -> Optional[Dict[str, Any]]:
        work = self._fetchone("SELECT * FROM work_log WHERE id = ?", (work_id,))
        if not work:
            return None
        return self._attach_end_time(work)

    def get_work_for_day(self, day: str) -> List[Dict[str, Any]]:
        """
        Returns work sessions for a day ordered by start_time.
        Each row includes computed end_time.
        """
        rows = self._fetchall(
            """
            SELECT w.*, d.day
            FROM work_log w
            JOIN schedule_days d ON d.id = w.day_id
            WHERE d.day = ?
            ORDER BY w.start_time ASC
            """,
            (day,),
        )
        return [self._attach_end_time(r) for r in rows]

    def get_work_for_task(self, task_id: str) -> List[Dict[str, Any]]:
        rows = self._fetchall(
            """
            SELECT w.*, d.day
            FROM work_log w
            JOIN schedule_days d ON d.id = w.day_id
            WHERE w.task_id = ?
            ORDER BY d.day ASC, w.start_time ASC
            """,
            (task_id,),
        )
        return [self._attach_end_time(r) for r in rows]

    def get_work_for_subtask(self, subtask_id: str) -> List[Dict[str, Any]]:
        rows = self._fetchall(
            """
            SELECT w.*, d.day
            FROM work_log w
            JOIN schedule_days d ON d.id = w.day_id
            WHERE w.subtask_id = ?
            ORDER BY d.day ASC, w.start_time ASC
            """,
            (subtask_id,),
        )
        return [self._attach_end_time(r) for r in rows]

    def delete_work(self, work_id: str) -> None:
        """
        Deletes a work row and subtracts its minutes from the related task/subtask.
        """
        work = self._fetchone("SELECT * FROM work_log WHERE id = ?", (work_id,))
        if not work:
            raise ValueError(f"Work not found: {work_id}")

        minutes = int(work["minutes"])
        task_id = work["task_id"]
        subtask_id = work["subtask_id"]

        cur = self.conn.cursor()
        try:
            if task_id:
                cur.execute(
                    "UPDATE tasks SET effort_done = effort_done - ? WHERE id = ?",
                    (minutes, task_id),
                )

            if subtask_id:
                cur.execute(
                    "UPDATE subtasks SET effort_done = effort_done - ? WHERE id = ?",
                    (minutes, subtask_id),
                )

            cur.execute("DELETE FROM work_log WHERE id = ?", (work_id,))

            self.conn.commit()

        except Exception:
            self.conn.rollback()
            raise

    def update_work(
        self,
        work_id: str,
        start_time: Optional[str] = None,
        minutes: Optional[int] = None,
        note: Optional[str] = None,
    ) -> None:
        """
        Update a work_log row.
        If minutes changes, adjusts effort_done accordingly.
        """

        work = self._fetchone("SELECT * FROM work_log WHERE id = ?", (work_id,))
        if not work:
            raise ValueError(f"Work not found: {work_id}")

        old_minutes = int(work["minutes"])
        new_minutes = old_minutes if minutes is None else int(minutes)

        if new_minutes <= 0:
            raise ValueError("minutes must be > 0")

        new_start_time = work["start_time"] if start_time is None else start_time
        _parse_time_to_seconds(new_start_time)  # validate

        delta = new_minutes - old_minutes

        task_id = work["task_id"]
        subtask_id = work["subtask_id"]

        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                UPDATE work_log
                SET start_time = ?, minutes = ?, note = ?
                WHERE id = ?
                """,
                (
                    new_start_time,
                    new_minutes,
                    note if note is not None else work["note"],
                    work_id,
                ),
            )

            if delta != 0:
                if task_id:
                    cur.execute(
                        "UPDATE tasks SET effort_done = effort_done + ? WHERE id = ?",
                        (delta, task_id),
                    )
                if subtask_id:
                    cur.execute(
                        "UPDATE subtasks SET effort_done = effort_done + ? WHERE id = ?",
                        (delta, subtask_id),
                    )

            self.conn.commit()

        except Exception:
            self.conn.rollback()
            raise

    def get_work_minutes_between(self, day_start: str, day_end: str) -> int:
        row = self._fetchone(
            """
            SELECT SUM(w.minutes) AS total
            FROM work_log w
            JOIN schedule_days d ON d.id = w.day_id
            WHERE d.day >= ? AND d.day <= ?
            """,
            (day_start, day_end),
        )
        return int(row["total"] or 0)

    def get_total_work_done(self) -> int:
        row = self._fetchone(
            """
            SELECT SUM(minutes) AS total
            FROM work_log
            """
        )
        return int(row["total"] or 0)

    # ----------------------------
    # Cleanup
    # ----------------------------
    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass
