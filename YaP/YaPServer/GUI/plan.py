
from nicegui import ui, app, client
from YaP.YaPCore.datetime_util import is_iso_date, iso_today, format_minutes, now_time, time_ago
from YaP.YaPCore.version import VERSION_STRING_SIMPLE

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
            task = ui.select(task_options, label="Task")

            subtask = ui.select({}, label="Subtask")
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
            
            minutes_worked = ui.number(label="Minutes Worked", min=1, value=1 if not work else work["minutes"], suffix="minutes")
            
            work_time = ui.time_input(value=now_time() if not work else work["start_time"])
            now_switch = ui.switch("Now?", on_change=lambda e: work_time.set_visibility(not e.value))

            with ui.row():
                def submit_fnc():
                    if not is_iso_date(work_date.value):
                        ui.notify("Work date should be a date with format YYYY-MM-DD", type="negative", position="center")
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
            self.tasks_list.refresh(open_target)
            
    def task_view(self, task, opened = False):

        def task_view_title(content):
            ui.label(content).style("text-transform: uppercase; font-weight: 100; color: #DDD; font-size: 0.7em;")

        with ui.expansion(group="task_list").classes('w-full').style(f"border-left: 5px dashed #222; border-radius: 12px;") as task_exp:
            with task_exp.add_slot('header'):
                with ui.column().style("gap: 2px"):
                    ui.label(task["name"]).style("font-weight: bold; font-size: 1.3em")
                    with ui.row():
                        ui.label(f'{task['date_start']} — {task['date_end'] if task['date_end'] else "indefinite"}').style("font-size: 0.9em; color:#666")
                        ui.label(f'{round(task["percent_completed"]*100, 2)}% completed').style("font-size: 0.9em; color:#aaa")
                    # ui.label(task_summary).style("font-size: 0.9em; color:#aaa")
                ui.space()
            
            if task["description"]:
                with ui.column().style("gap: 0;"):
                    task_view_title("description")
                    ui.label(task["description"]).style('white-space: pre-wrap') 

            with ui.column().style("gap: 0;"):
                task_view_title("completion")
                with ui.grid(columns=2):
                    ui.label("Work required")
                    ui.label(format_minutes(task["effort"])).style('color: #999;') 

                    ui.label("Work done")
                    with ui.row():
                        ui.label(format_minutes(task["total_effort_done"])).style('color: #999;')
                        ui.label(f'({format_minutes(task["effort"] - task["total_effort_done"])} left)').style('color: #999;')

                ui.label(f"{round(task["percent_completed"]*100, 2)}% completed").style("text-transform: uppercase; font-weight: 100; color: #AAA; font-size: 0.7em; letter-spacing: 1px;")
                ui.linear_progress(task["percent_completed"], show_value=False).props("size=md stripe track-color='grey-8'").style("width: 100%;")

            with ui.column().style("gap: 0; margin-top: 1em; width: 100%;"):
                task_view_title("subtasks")
                for subtask in task["subtasks"]:
                    with ui.expansion(group=task['id']).style("min-width: 280px; width: 50%;") as subtask_exp:
                        with subtask_exp.add_slot('header'):
                            # with ui.column().style("gap: 2px"):

                            with ui.row():
                                if subtask["target_effort"]:
                                    prog = subtask["effort_done"]/subtask["target_effort"]
                                    ui.circular_progress(value=prog, size="sm", show_value=None).props("rounded track-color='grey-8'").tooltip(f"{round(prog*100,2)}% completed")

                                ui.label(subtask["name"]).style("font-size: 1em")
                            
                            ui.space()

                        with ui.column().style("border-left: 1px solid gray; padding-left: 0.5em; width: 100%;"):

                            if subtask["description"]:
                                ui.label(subtask["description"]).style('white-space: pre-wrap; color: #999;') 


                            with ui.row().style("width: 100%;"):

                                if subtask["target_effort"]:
                                    ui.label(f"{format_minutes(subtask['effort_done'])} / {format_minutes(subtask['target_effort'])}").style("color: #666").tooltip("Work done / Time required")
                                    ui.label(f"{round(subtask['effort_done']/subtask['target_effort']*100)}%").style("color: #666").tooltip("Percent completed")

                                if subtask["date_end"]:
                                    ui.label(f"due {subtask["date_end"]}").style("color: #666").tooltip("Deadline")

                                with ui.row().style("display: flex; align-items: center; justify-content: flex-end; gap: 10px; ;margin-left: auto;border-radius: 10px;background: rgba(255, 255, 255, 0.02);border: 1px solid rgba(255, 255, 255, 0.04);"):
                                    ui.button(icon='edit', 
                                            on_click=lambda s=subtask, t=task: self.task_edit(s['id'], parent_task=t['id'])
                                            ).props("flat rounded size=xs color=grey").tooltip("Edit subtask")

                                    def delete_subtask(s=subtask): 
                                        self.plan.delete_subtask(s["id"])
                                        self.tasks_list.refresh(task['id'])
                                        ui.notify(f"{s['name']} deleted.", type="warning")

                                    ui.button(icon='delete', 
                                            on_click=lambda f=delete_subtask, s=subtask: self.GUI.confirm_action(
                                                f, 
                                                message=f"Are you sure you want to permanently delete '{s['name']}'?", 
                                                title=f"Delete '{s['name']}'", 
                                                icon="delete")
                                            ).props("flat rounded size=xs color=negative").tooltip("Delete subtask")

                ui.button("Add subtask", icon='add', on_click = lambda: self.task_edit(parent_task=task["id"])).props("flat rounded size=sm")

            with ui.row().style("display: flex; align-items: center; justify-content: flex-end; gap: 10px; ;margin-left: auto;border-radius: 10px;background: rgba(255, 255, 255, 0.02);border: 1px solid rgba(255, 255, 255, 0.04);"):
                ui.button(icon='edit', on_click=lambda: self.task_edit(task['id'])).props("flat rounded size=sm color=grey").tooltip("Edit task")

                def delete_task():
                    self.plan.delete_task(task["id"])
                    self.tasks_list.refresh()
                    ui.notify(f"{task['name']} deleted.", type="warning")
                ui.button(icon='delete', on_click=lambda: self.GUI.confirm_action(delete_task, message=f"Are you sure you want to permanently delete '{task['name']}'?", title=f"Delete '{task['name']}'", icon="delete")).props("flat rounded size=sm color=negative").tooltip("Delete task")

        ui.separator()

        if opened: # For task_list refresh after an edit/addition
            task_exp.open()

    @ui.refreshable
    def tasks_list(self, opened: str = None):

        if not (tasks := self.plan.get_tasks_full()):
            ui.label("No tasks found, create one with the + button above.")
            return
        
        for task_n, task in enumerate(tasks):
            self.task_view(task, 
                           opened = True if task['id'] == opened else False, 
                           )


    def dashboard(self):


        self.build_header()
        ui.page_title(self.plan.name)


        with ui.fab('add', label='', color='#999', direction='down').classes('mx-auto'):
            ui.fab_action('assignment_add', label='Task', on_click=self.task_edit, color='#999')
            ui.fab_action('event', label='Event', color='#999')
            ui.fab_action('hiking', label='Work', on_click=self.work_edit, color='#999')


        with ui.tabs().classes('w-full') as tabs:
            tasks_tab = ui.tab('Tasks')
            schedule_tab = ui.tab('Schedule')

        with ui.tab_panels(tabs, value=tasks_tab).classes('w-full').style("border-radius:10px;"):
            with ui.tab_panel(tasks_tab):
                
                self.tasks_list()

            with ui.tab_panel(schedule_tab):

                pass