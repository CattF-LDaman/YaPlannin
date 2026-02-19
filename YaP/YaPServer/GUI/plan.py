
from nicegui import ui, app, client
from YaP.YaPCore.datetime_util import is_iso_date, iso_today, format_minutes, now_time, time_ago
from YaP.YaPCore.version import VERSION_STRING_SIMPLE

from .task_tab import TaskTab
from .schedule_tab import ScheduleTab
from .dashboard_tab import DashboardTab

@ui.page("/plan/{plan_id}")
def plan_gui(plan_id, client: client.Client):
    PlanGUI(plan_id, client, app.storage.user.get('username', ""))

class PlanGUI:

    GUI = None

    def __init__(self, plan_id, nicegui_client, gui_user) -> None:

        self.plan_id = plan_id
        self.server = self.GUI.server
        self.nicegui_client = nicegui_client
        self.gui_user = gui_user
        self.server.log(f"[GUI] {self.gui_user} accessing {self.plan_id}.")
        self.add_gui_user_info()

        self.plan = None
        try:
            self.plan = self.server.database.plan_data[plan_id]
        except KeyError:
            ui.notify("Not found!", type="negative")

        self.task_list = None

        ui.colors(primary=self.server.config.gui.primary_color, secondary='#333')
        self.GUI.add_font()
        self.GUI.add_scrollbar_color()

        if self.plan:
            self.dashboard()
        
    def add_gui_user_info(self):

        ui.label(f"Logged in as {self.gui_user} on {VERSION_STRING_SIMPLE}").style("color: rgb(20, 20, 20); position: fixed; top: 0; right: 10px; z-index: 9999;  pointer-events: none;")


    def build_header(self):

        with ui.header().style("background-color:#252525"):
            ui.image(source="/static/logo.png").style("width: 90px; height: 90px;"+ ("filter:grayscale(1)" if not self.plan else ""))

            with ui.column():
                with ui.row():
                    ui.label(self.plan.name).style("font-weight: bold; font-size: 2.1em")
                    with ui.row():
                        ui.icon("person", size="1.4em")
                        ui.label(self.plan.user).style("font-size: 1em; color:#aaa")
                ui.label(self.plan.desc).style("color: #999")

                    # menu_btn = ui.button(icon='menu', color="rgb(37, 37, 37)")

            # menu_btn.on_click(lambda: btns.set_visibility(not btns.visible))

    async def work_edit(self, work_id: str = None):
        work = None
        if work_id:
            work = self.plan.get_work(work_id)

        with ui.dialog() as dialog, ui.card().style("max-width: 500px; width: 100%;"):
            with ui.row().classes('justify-center items-center'):
                ui.icon("hiking", size="2.3em")
                ui.label("Add work" if not work else "Edit work").style("font-weight: bold; font-size: 1.6em")
            
            task_options = {task['id']: task["name"] for task in self.plan.get_tasks()}
            task = ui.select(task_options, label="Task").style("min-width: 60%")

            subtask = ui.select({}, label="Subtask").style("min-width: 60%")
            def update_subtask_options(e):
                subtask_options = {st['id']: st["name"] for st in self.plan.get_subtasks_for_task(e.value)}
                subtask_options[None] = "< empty >"
                subtask.set_options(subtask_options, value=None)
            task.on_value_change(update_subtask_options)

            work_note = ui.input("Note", value=work["note"] if work else None).style("width: 100%;")
            
            work_date = ui.date_input("Date", value=(iso_today() if not work else work["day"]))
            if not work:
                today_switch = ui.switch("Change?", value=False)
                work_date.bind_enabled_from(today_switch, "value")
            
            minutes_worked = ui.number(label="Minutes Worked", min=1, value=1 if not work else work["minutes"], suffix="minutes").style("min-width: 60%")
            
            work_time = ui.time_input(value=now_time() if not work else work["start_time"]).style("min-width: 60%")
            now_switch = ui.switch("Now?", on_change=lambda e: work_time.set_visibility(not e.value))

            with ui.row():
                def submit_fnc():
                    if not is_iso_date(work_date.value):
                        ui.notify("Work date should be a date with format YYYY-MM-DD", type="negative")
                        return
                    if not task.value:
                        ui.notify("No task provided.", type="negative")
                        return
                    timestamp = work_time.value if not now_switch.value else time_ago(minutes_worked.value)
                    dialog.submit((task.value, subtask.value, work_note.value if work_note.value else "", work_date.value, minutes_worked.value, timestamp))
                ui.button("Create" if not work else "Save", color=self.server.config.gui.primary_color, on_click=submit_fnc)
                ui.button("Cancel", color="#333", on_click=lambda: dialog.submit(None))

        work_values = await dialog
        if work_values:
            task, subtask, work_note, work_date, minutes_worked, timestamp = work_values

            if not work:
                    # day: str,
                    # start_time: str,
                    # minutes: int,
                    # note: str = "",
                    # task_id: Optional[str] = None,
                    # subtask_id: Optional[str] = None,
                created_uuid = self.plan.add_work(day = work_date, start_time = timestamp, minutes = minutes_worked, note = work_note, task_id = task if not subtask else None, subtask_id = subtask)
                self.server.log(f"[GUI] [{self.gui_user}] Work created: {created_uuid}")
            # else:
            #     if not is_subtask:
            #         self.plan.update_task(task_id = task_id, name = task_name, description = task_desc, date_start = task_start, date_end = task_end if task_end else None, base_effort = req_effort or 0)
            #         self.server.log(f"[GUI] [{self.gui_user}] Task updated: {task_name}")
            #     else:
            #         self.plan.update_subtask(subtask_id = task_id, name = task_name, description = task_desc, date_end = task_end if task_end else None, target_effort = req_effort or 0)
            #         self.server.log(f"[GUI] [{self.gui_user}] Subtask for {parent_task['name']} updated: {task_name}")
            ui.notify(f"Work {'created' if not task else 'updated'}.", type="positive")
            self.schedule.refresh()
            self.task_list.refresh(task)

    async def task_edit(self, task_id: str = None, parent_task: str = None):
        task = None
        is_subtask = parent_task is not None

        if task_id:
            task = self.plan.get_task_full(task_id) if not is_subtask else self.plan.get_subtask(task_id)
        if is_subtask:
            parent_task = self.plan.get_task_full(parent_task)

        with ui.dialog() as dialog, ui.card().style("max-width: 500px; width: 100%;"):
            with ui.row().classes('justify-center items-center'):
                ui.icon("assignment", size="2.3em")
                ui.label(("New task" if not is_subtask else "New subtask") if not task else f"Edit '{task['name']}'").style("font-weight: bold; font-size: 1.6em")
            
            task_name = ui.input("Name", value=task["name"] if task else None)
            task_desc = ui.textarea("Description", value=task["description"] if task else "").style("width: 100%;")
            
            task_start = ui.date_input("Start", value=(iso_today() if not task else task["date_start"]) if not parent_task else parent_task["date_start"])
            if is_subtask:
                task_start.disable() # Subtasks don't have a start date, shared with parent
            # task_start.picker.props[":options"] = f'date => date >= "{iso_today()}"' # Ensure date not earlier then today
            
            task_end = ui.date_input("End", value=None if not task else task["date_end"]).props('clearable')
            # task_end.picker.props[":options"] = f'date => date >= "{iso_today()}"'
            
            req_effort = ui.number(label="Required Effort", min=0, value=0 if not task else task["base_effort" if not is_subtask else "target_effort"], suffix="minutes")
            
            with ui.row():
                def submit_fnc():
                    if not is_subtask and not is_iso_date(task_start.value):
                        ui.notify("Start should be a date with format YYYY-MM-DD", type="negative", position="center")
                        return
                    if task_end.value and not is_iso_date(task_end.value):
                        ui.notify("End should be empty or a date with format YYYY-MM-DD", type="negative", position="center")
                        return
                    dialog.submit((task_name.value, task_desc.value, task_start.value, task_end.value, req_effort.value))
                ui.button("Create" if not task else "Save", color=self.server.config.gui.primary_color, on_click=submit_fnc)
                ui.button("Cancel", color="#333", on_click=lambda: dialog.submit(None))

        task_values = await dialog
        if task_values:
            task_name, task_desc, task_start, task_end, req_effort = task_values

            if not task:
                if not is_subtask:
                    created_uuid = self.plan.add_task(name = task_name, description = task_desc, date_start = task_start, date_end = task_end if task_end else None, base_effort = req_effort or 0)
                    self.server.log(f"[GUI] [{self.gui_user}] Task created: {task_name} {created_uuid}")
                else:
                    created_uuid = self.plan.add_subtask(task_id=parent_task["id"], name = task_name, description = task_desc, date_end = task_end if task_end else None, target_effort = req_effort or 0)
                    self.server.log(f"[GUI] [{self.gui_user}] Subtask for {parent_task['name']} created: {task_name} {created_uuid}")
            else:
                if not is_subtask:
                    self.plan.update_task(task_id = task_id, name = task_name, description = task_desc, date_start = task_start, date_end = task_end if task_end else None, base_effort = req_effort or 0)
                    self.server.log(f"[GUI] [{self.gui_user}] Task updated: {task_name}")
                else:
                    self.plan.update_subtask(subtask_id = task_id, name = task_name, description = task_desc, date_end = task_end if task_end else None, target_effort = req_effort or 0)
                    self.server.log(f"[GUI] [{self.gui_user}] Subtask for {parent_task['name']} updated: {task_name}")
            ui.notify(f"{'Task' if not is_subtask else 'Subtask'} {task_name} {'created' if not task else 'updated'}.", type="positive")
            
            open_target = (task_id if task else created_uuid) if not is_subtask else parent_task["id"]
            self.task_list.refresh(open_target)
    
    def dashboard(self):


        self.build_header()
        ui.page_title(self.plan.name)


        with ui.fab('add', label='', color='#999', direction='down').classes('mx-auto'):
            ui.fab_action('assignment_add', label='Task', on_click=self.task_edit, color='#999')
            ui.fab_action('event', label='Event', color='#999')
            ui.fab_action('hiking', label='Work', on_click=self.work_edit, color='#999')


        with ui.tabs().classes('w-full') as tabs:
            dashboard_tab = ui.tab('Dashboard')
            tasks_tab = ui.tab('Tasks')
            schedule_tab = ui.tab('Schedule')

        with ui.tab_panels(tabs, value=dashboard_tab).classes('w-full').style("border-radius:10px;"):
            with ui.tab_panel(dashboard_tab):
                
                self.dashboard = DashboardTab(self).dashboard
                self.dashboard()

            with ui.tab_panel(tasks_tab):
                
                self.task_list = TaskTab(self).tasks_list
                self.task_list()

            with ui.tab_panel(schedule_tab):

                self.schedule = ScheduleTab(self).schedule
                self.schedule()