
from nicegui import ui, app, client

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

    def dashboard(self):


        self.build_header()
        ui.page_title(self.plan.name)


        with ui.fab('add', label='', color='#999', direction='down').classes('mx-auto'):
            ui.fab_action('assignment_add', label='Task', color='#999')
            ui.fab_action('event', label='Event', color='#999')
            ui.fab_action('hiking', label='Work', color='#999')


        with ui.tabs().classes('w-full') as tabs:
            tasks_tab = ui.tab('Tasks')
            schedule_tab = ui.tab('Schedule')

        with ui.tab_panels(tabs, value=tasks_tab).classes('w-full'):
            with ui.tab_panel(tasks_tab):
                
                pass

            with ui.tab_panel(schedule_tab):

                pass