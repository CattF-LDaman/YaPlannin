
from nicegui import ui, app, client
from YaP.YaPCore.datetime_util import is_iso_date, iso_today, format_minutes, now_time, time_ago
from YaP.YaPCore.version import VERSION_STRING_SIMPLE

from datetime import date, timedelta

class ScheduleTab:

    def __init__(self, plan_gui):
        
        self.plan_gui = plan_gui
        self.plan = plan_gui.plan
        self.GUI = plan_gui.GUI

        self.selected_week = self._get_week_days(date.today())

    def _get_week_days(self, d: date):
        """
        Returns list of 7 days (YYYY-MM-DD) for the week containing date d.
        Week starts on Monday.
        """
        monday = d - timedelta(days=d.weekday())
        return [(monday + timedelta(days=i)).isoformat() for i in range(7)]


    def previous_week(self):
        """
        Shifts selected_week back by 7 days.
        """
        first_day = date.fromisoformat(self.selected_week[0])
        new_day = first_day - timedelta(days=7)
        self.selected_week = self._get_week_days(new_day)
        self.schedule.refresh()
        return self.selected_week


    def next_week(self):
        """
        Shifts selected_week forward by 7 days.
        """
        first_day = date.fromisoformat(self.selected_week[0])
        new_day = first_day + timedelta(days=7)
        self.selected_week = self._get_week_days(new_day)
        self.schedule.refresh()
        return self.selected_week

    def task_reference(self, task_id: str = None, subtask_id: str = None):
        
        subtask = None
        if task_id:
            task_info = self.plan.get_task_full(task_id)
        elif subtask_id:
            subtask = self.plan.get_subtask(subtask_id)
            task_info = self.plan.get_task_full(subtask["task_id"])

        task_name = task_info["name"]
        if subtask:
            task_name += f": {subtask['name']}"


        with ui.button(task_info["name"], icon='assignment', on_click = None).props("flat rounded size=xs"):
            with ui.tooltip().classes('bg-transparent'):
                with ui.card().style("max-width: 500px; width: 100%;"):
                    with ui.row().classes('justify-center items-center'):
                        ui.icon("assignment", size="2.3em")
                        ui.label(task_name).style("font-weight: bold; font-size: 1.6em")
                    

    def day_summary(self, day):
        
        date_obj = date.fromisoformat(day)
        short_day = date_obj.strftime("%a")
        day_month = date_obj.strftime("%d/%m")

        work_for_day = self.plan.get_work_for_day(day)
        total_work_done = sum([work["minutes"] for work in work_for_day])

        today = day == iso_today()

        with ui.column().classes('w-full').classes('items-center').style(f"border-left: 1px dashed #333; border-right: 1px dashed #333;" + ("border-radius: 0 0 10px 10px; padding-bottom: 1em; border-bottom: 3px dashed #999;" if today else "")):
            with ui.column().style("gap: 0;"):
                ui.label(short_day).style("font-size: 0.9em; color:#888;")
                ui.label(day_month).style("font-size: 0.9em; color:#bbb;")

            ui.separator()

            ui.label("Work done").style("color:#aaa; font-size:0.8em; text-transform: uppercase; font-weight: 100; border-bottom: 1px dashed #333;")
            ui.label(f"Total: {format_minutes(total_work_done)}").style("color:#888; font-size:0.75em; ")
            if not work_for_day:
                ui.label("No work done.").style("color:#777")

            for work in work_for_day:
                with ui.grid(columns=2):
                    ui.label(f'{work["start_time"]} — {work[("end_time")]}').style("font-size: 0.9em; color:#666; text-align: right;")
                    self.task_reference(task_id=work['task_id'] if work["task_id"] else None, subtask_id=work['subtask_id'] if work["subtask_id"] else None)
                        # ui.label(f'{round(task["percent_completed"]*100, 2)}% completed').style("font-size: 0.9em; color:#aaa")

    @ui.refreshable
    def schedule(self):

        with ui.row().classes('w-full').classes('items-center justify-center'):
            ui.button("<<", on_click = self.previous_week).props("flat rounded size=sm").style("color: #555;")
            ui.label(f"{self.selected_week[0]} — {self.selected_week[-1]}")
            ui.button(">>", on_click = self.next_week).props("flat rounded size=sm").style("color: #555;")

        with ui.grid(columns="1fr "*7).classes('w-full gap-0'):
            for day in self.selected_week:
                self.day_summary(day)