import os
import uuid
from typing import Optional, List, Dict, Any


def _uid() -> str:
    return str(uuid.uuid4())


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
        target_effort INTEGER NOT NULL DEFAULT 0,
        effort_done INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
    );

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
    def add_subtask(self, task_id: str, name: str, description: str, target_effort: int = 0) -> str:
        if not self.get_task(task_id):
            raise ValueError(f"Cannot create subtask: task not found {task_id}")

        subtask_id = _uid()
        self.conn.execute(
            """
            INSERT INTO subtasks (id, task_id, name, description, target_effort, effort_done)
            VALUES (?, ?, ?, ?, ?, 0)
            """,
            (subtask_id, task_id, name, description, int(target_effort)),
        )
        self.conn.commit()
        return subtask_id

    def update_subtask(self, subtask_id: str, name: Optional[str] = None, description: Optional[str] = None, target_effort: Optional[int] = None) -> None:
        sub = self.get_subtask(subtask_id)
        if not sub:
            raise ValueError(f"Subtask not found: {subtask_id}")

        self.conn.execute(
            """
            UPDATE subtasks
            SET name = ?, description = ?, target_effort = ?
            WHERE id = ?
            """,
            (
                name if name is not None else sub["name"],
                description if description is not None else sub["description"],
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
    def _apply_task_metrics(self, task: Dict[str, Any], subtasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        base_effort = int(task["base_effort"])
        base_done = int(task["effort_done"])

        sub_effort = sum(int(s["target_effort"]) for s in subtasks)
        sub_done = sum(int(s["effort_done"]) for s in subtasks)

        effort = base_effort + sub_effort
        total_done = base_done + sub_done

        percent = (total_done / effort) if effort > 0 else 0.0

        # Merge into one dict
        task = dict(task)  # copy
        task["subtasks"] = subtasks
        task["effort"] = effort
        task["total_effort_done"] = total_done
        task["percent_completed"] = percent

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

        # Efficient: fetch all subtasks once, then group them
        all_subtasks = self._fetchall("SELECT * FROM subtasks")
        sub_by_task: Dict[str, List[Dict[str, Any]]] = {}
        for s in all_subtasks:
            sub_by_task.setdefault(s["task_id"], []).append(s)

        # Attach metrics + subtasks
        return [
            self._apply_task_metrics(t, sub_by_task.get(t["id"], []))
            for t in tasks
        ]

    # ----------------------------
    # Cleanup
    # ----------------------------
    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass
