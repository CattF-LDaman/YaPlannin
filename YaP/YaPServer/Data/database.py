import sqlite3
from pathlib import Path
import os
import uuid

from .plandata import PlanData

def connect(db_path: str) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path: str, schema: str):
    conn = connect(db_path)
    conn.executescript(schema)
    conn.commit()
    conn.close()

class YaPDB:

    FILENAME = "YaP.db"
    SCHEMA = """
        CREATE TABLE IF NOT EXISTS plans (
            id TEXT PRIMARY KEY,
            user TEXT NOT NULL,
            description TEXT NOT NULL,
            name TEXT NOT NULL
        );
    """

    def __init__(self, server):
        
        self.server = server
        self.location = os.path.join(server.dirs["storage"], YaPDB.FILENAME)

        init_db(self.location, YaPDB.SCHEMA)
        self.conn = connect(self.location)

        self.server.log(f"Database: {self.location}")

        self.plan_data = {} 
        self.plans = self.get_plans()

    def get_plans(self):
        plan_rows = self.conn.execute("SELECT * FROM plans").fetchall()
        plans = {}
        for plan in plan_rows:
            if plan["user"] not in plans:
                plans[plan["user"]] = []
            plan_info = {"id":plan["id"], "name":plan["name"], "description":plan["description"], "user":plan["user"]}
            if plan["id"] not in self.plan_data:
                self.plan_data[plan["id"]] = PlanData(self.server, plan["id"], plan_info)
            plans[plan["user"]].append(plan_info)
        return  plans
    
    def new_plan(self, user: str, name: str, description: str) -> str:
        """Create a new plan and return its id."""
        plan_id = str(uuid.uuid4())

        self.conn.execute(
            """
            INSERT INTO plans (id, user, description, name)
            VALUES (?, ?, ?, ?)
            """,
            (plan_id, user, description, name),
        )
        self.conn.commit()

        # Keep cached list updated
        self.plans = self.get_plans()
        self.server.log(f"New plan for user {user} created: '{name}'")

        return plan_id