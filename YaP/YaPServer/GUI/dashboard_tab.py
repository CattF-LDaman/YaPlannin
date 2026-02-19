
from nicegui import ui, app, client
from YaP.YaPCore.datetime_util import is_within_next_week, iso_today, format_minutes, this_week, has_passed
from YaP.YaPCore.version import VERSION_STRING_SIMPLE

import math

class DashboardTab:

    def __init__(self, plan_gui):
        
        self.plan_gui = plan_gui
        self.plan = plan_gui.plan
        self.GUI = plan_gui.GUI

    def warning(self, title = "Warning", content = "", highlighted = "", critical=False):
        with ui.card().style(f"border: 4px dashed #f33;" if critical else f"border: 4px dashed #e6b800;") as w_card:
            with ui.row():
                ui.icon("warning", size="2.3em")
                ui.label(title).style("font-weight: bold; font-size: 1.6em")
            ui.label(content).style("white-space: pre-wrap;")
            if highlighted:
                ui.label(highlighted).style("font-weight: bold; white-space: pre-wrap;")

        return w_card

    def dashboard_card(self, title):
        with ui.card().style("border: 2px solid #444; min-width: 33vw;").props("flat") as d_card:
            ui.label(title).style("text-transform: uppercase; font-weight: 100; color: #DDD; font-size: 1em; width: 100%; text-align: center; border-bottom: 2px dashed #444;")

        return d_card

    def metric(self, title, content, info = "A metric."):
        with ui.column().style("gap: 0; cursor: help; border-left: 1px solid #444; padding-left: 0.5em;").tooltip(info):
            ui.label(title).style("text-transform: uppercase; font-weight: 100; color: #DDD; font-size: 1em;")
            ui.label(content).style("text-transform: uppercase; font-weight: bold; color: #DDD; font-size: 2em;")

    def warnings(self):

        tasks = self.plan.get_tasks_full()
        subtasks_and_tasks = []
        for task in tasks:
            subtasks_and_tasks.extend([task]+task["subtasks"])


        with ui.row().style('width: 100%; border-bottom: 2px dashed #444; padding-bottom: 1em;'):
            deadlines_today = [task for task in subtasks_and_tasks if task["date_end"] == iso_today()]
            if deadlines_today:
                with self.warning(title="Deadlines today", content="You have deadlines ending today:", critical=True, highlighted="Make sure they're finished!"):
                    with ui.grid(columns=2).style("gap: 2px;").style("width: 100%"):
                        for task in deadlines_today:
                            tlabel = ui.label(task["full_name" if "full_name" in task else "name"])
                            if "full_name" in task:
                                tlabel.style("margin-left: 1.5em;") # subtask indent
                            ui.label(f"ends {task["date_end"]}").style(f"color: #999;")

            deadlines_this_week = [task for task in subtasks_and_tasks if is_within_next_week(task["date_end"]) and task["date_end"] != iso_today()]
            if deadlines_this_week:
                with self.warning(title="Deadlines coming up", content="You have deadlines ending soon:", highlighted=""):
                    #"\n".join(f'{task["full_name" if "full_name" in task else "name"]} ends {task['date_end']}' for task in deadlines_this_week)
                    with ui.grid(columns=2).style("gap: 2px;").style("width: 100%"):
                        for task in deadlines_this_week:
                            tlabel = ui.label(task["full_name" if "full_name" in task else "name"])
                            if "full_name" in task:
                                tlabel.style("margin-left: 1.5em;") # subtask indent
                            ui.label(f"ends {task["date_end"]}").style(f"color: #999;")

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

    def pressure_meter(self):

        pressure, total_effort = self.plan.get_plan_pressure()
        if pressure > 0:
            pstyle = " color='red'"
        else:
            pstyle = " color='green' reverse"
        
        with ui.column().style("gap: 0; width: 100%;"):
            ui.label("Pressure Meter").style("text-transform: uppercase; font-weight: 100; color: #DDD; font-size: 0.7em; width: 100%; text-align: center;")
            ui.label(f"{'+' if pressure >  0 else '-'} {abs(pressure)}").style(f"width: 100%; text-align: center; font-size: 2em; font-weight: bold; color: {'#f33' if pressure > 0 else '#3f3'}")
            ui.linear_progress(abs(pressure)/max(total_effort, 1), show_value=False).props("size=xl stripe track-color='grey-8' size='20px'"+pstyle).style("width: 100%;")

    def work_card(self):

        tasks = self.plan.get_tasks_full()

        curr_week = this_week()
        work_this_week = self.plan.get_work_minutes_between(curr_week[0], curr_week[-1])
        work_today = self.plan.get_work_minutes_between(iso_today(), iso_today())
        with self.dashboard_card("Work"):
            with ui.row():
                self.metric("Work done", format_minutes(sum(task["total_effort_done"] for task in tasks)), info="Total amount of work done.")
                self.metric("This week", format_minutes(work_this_week), info="All the work done this week.")
                self.metric("Today", format_minutes(work_today), info="All the work done today.")

            with ui.row():
                self.metric("Plan total", format_minutes(sum(task["effort"] for task in tasks)), info="Sum of all the effort required by tasks.")

    def deadline_card(self):

        tasks = self.plan.get_tasks_full()
        subtasks_and_tasks = []
        for task in tasks:
            subtasks_and_tasks.extend([task]+task["subtasks"])

        with self.dashboard_card("Deadlines"):
            with ui.grid(columns=2).style("gap: 2px;").style("min-width: 80%"):
                for task in subtasks_and_tasks:
                    if task["date_end"] and not has_passed(task["date_end"]):

                        tlabel = ui.label(task["name"])
                        if "full_name" in task:
                            tlabel.style("margin-left: 1.5em;") # subtask indent
                        with ui.row():
                            ui.label(f"ends {task["date_end"]}").style(f"color: #999;")
                            if task["date_end"] == iso_today():
                                ui.icon("priority_high", color="#f33").tooltip("Ends soon!")
                            elif is_within_next_week(task["date_end"]):
                                ui.icon("priority_high", color="#ffcc00").tooltip("Ends today!")
    @ui.refreshable
    def dashboard(self):
        self.pressure_meter()

        self.warnings()

        with ui.row():
            self.work_card()
            self.deadline_card()
