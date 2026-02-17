
from nicegui import ui, app, client
from YaP.YaPCore.datetime_util import is_iso_date, iso_today, format_minutes, now_time, time_ago
from YaP.YaPCore.version import VERSION_STRING_SIMPLE

class TaskTab:

    def __init__(self, plan_gui):
        
        self.plan_gui = plan_gui
        self.plan = plan_gui.plan
        self.GUI = plan_gui.GUI

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

                    ui.label("Effort behind")
                    ui.label(format_minutes(task["effort_behind"])).style('color: #999;') 

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
                                            on_click=lambda s=subtask, t=task: self.plan_gui.task_edit(s['id'], parent_task=t['id'])
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

                ui.button("Add subtask", icon='add', on_click = lambda: self.plan_gui.task_edit(parent_task=task["id"])).props("flat rounded size=sm")

            with ui.row().style("display: flex; align-items: center; justify-content: flex-end; gap: 10px; ;margin-left: auto;border-radius: 10px;background: rgba(255, 255, 255, 0.02);border: 1px solid rgba(255, 255, 255, 0.04);"):
                ui.button(icon='edit', on_click=lambda: self.plan_gui.task_edit(task['id'])).props("flat rounded size=sm color=grey").tooltip("Edit task")

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

