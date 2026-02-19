
from nicegui import ui, app, client
from YaP.YaPCore.datetime_util import is_within_next_week, iso_today, format_minutes
from YaP.YaPCore.version import VERSION_STRING_SIMPLE

import math

class DashboardTab:

    def __init__(self, plan_gui):
        
        self.plan_gui = plan_gui
        self.plan = plan_gui.plan
        self.GUI = plan_gui.GUI

    def warning(self, title = "Warning", content = "", highlighted = "", critical=False):
        with ui.card().style(f"background-color: #f33" if critical else f"border: 4px dashed #e6b800;") as w_card:
            with ui.row():
                ui.icon("warning", size="2.3em")
                ui.label(title).style("font-weight: bold; font-size: 1.6em")
            ui.label(content).style("white-space: pre-wrap;")
            if highlighted:
                ui.label(highlighted).style("font-weight: bold; white-space: pre-wrap;")

        return w_card

    def warnings(self):

        tasks = self.plan.get_tasks_full()
        subtasks_and_tasks = []
        for task in tasks:
            subtasks_and_tasks.extend([task]+task["subtasks"])


        with ui.row().style('width: 100%; border-bottom: 2px dashed #444; padding-bottom: 1em;'):
            deadlines_today = [task for task in subtasks_and_tasks if task["date_end"] == iso_today()]
            if deadlines_today:
                self.warning(title="Deadlines today", content="You have deadlines ending today:", critical=True, highlighted="\n".join(f'{task["full_name" if "full_name" in task else "name"]} ends {task['date_end']}' for task in deadlines_today))

            deadlines_this_week = [task for task in subtasks_and_tasks if is_within_next_week(task["date_end"]) and task["date_end"] != iso_today()]
            if deadlines_this_week:
                self.warning(title="Deadlines coming up", content="You have deadlines ending soon:", highlighted="\n".join(f'{task["full_name" if "full_name" in task else "name"]} ends {task['date_end']}' for task in deadlines_this_week))

            lagging_tasks = {}
            for task in subtasks_and_tasks:
                name = task["full_name" if "full_name" in task else "name"]
                # If effort behind is more than should be approximately done per week
                if task["effort_behind"] > math.ceil(task["weekly_effort"]):
                    lagging_tasks[name] = task
            if lagging_tasks:
                with self.warning(title="Lagging behind", content="If you don't put more work in for these (sub)tasks, you will likely not finish in time:", highlighted=""):
                    with ui.grid(columns=2).style("gap: 2px;").style("width: 100%"):
                        for task_name, task in lagging_tasks.items():
                            tlabel = ui.label(task_name)
                            if "full_name" in task:
                                tlabel.style("margin-left: 1.5em;") # subtask indent
                            bad_lag = task["effort_behind"] > task["weekly_effort"]*2
                            ui.label(f"{format_minutes(task["effort_behind"])} behind").style(f"color: {"#999" if not bad_lag else "#F22"};").tooltip(f"Target weekly: {format_minutes(math.ceil(task["weekly_effort"]))}")

    @ui.refreshable
    def dashboard(self):

        self.warnings()
