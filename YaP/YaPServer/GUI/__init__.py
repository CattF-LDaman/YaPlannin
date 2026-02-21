
from YaP.YaPCore.threading import threaded_daemon
from YaP.YaPCore.version import VERSION_STRING

from YaP.YaPServer.GUI.logo_raw import LOGO_ICO, LOGO_PNG, LOGO_EDGE_PNG
from YaP.YaPServer.GUI.geo import get_flag_icon_from_ip
from YaP.YaPServer.GUI.account import AccountManager
from YaP.YaPServer.GUI.plan import PlanGUI
import YaP.YaPServer.GUI.auth

from nicegui import ui, app
import os
import inspect

FONT_HEAD = r"""<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@300..700&display=swap" rel="stylesheet">
"""

SCROLLBAR_HEAD = r"""<style>
html{
    scrollbar-color: hsl(0,0%,46%) transparent;
    overflow-y: scroll;
}</style>"""

BG_HTML = """
<style>
body::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;

    /* Path to your logo */
    background-image: url("/static/logo-edge.png");
    
    /* Center the image and prevent tiling */
    background-repeat: no-repeat;
    background-position: center;
    
    /* Scale the logo - adjust '50vw' to make it larger or smaller */


    /* "Very very slight visibility" - adjust opacity between 0.01 and 0.05 */
    filter: grayscale(1) opacity(0.01); 
    
    z-index: -1; 
    pointer-events: none; /* Ensures the background doesn't block clicks */
}
</style>
"""

class GUI:

    SERVER = None

    def __init__(self, server) -> None:
        
        self.server = GUI.SERVER = server
        
        self.static_dir = self.server.dirs["guistatic"]

        AccountManager.GUI = self
        PlanGUI.GUI = self

        # app.add_static_files("/downloads", self.server.dirs['downloads'])

        ui.page('/')(self.index)

    def create_logo_files(self):
        with open(os.path.join(self.static_dir, "logo.png"), "wb") as png:
            png.write(LOGO_PNG)
        with open(os.path.join(self.static_dir, "logo-edge.png"), "wb") as png:
            png.write(LOGO_EDGE_PNG)

    def add_font(self):

        font = '"Quicksand", sans-serif'
        ui.add_head_html(FONT_HEAD)

        classes = [cls for name, cls in inspect.getmembers(ui, inspect.isclass) if hasattr(cls, 'default_style') and callable(getattr(cls, 'default_style'))] 
        for eclass in classes:
            if eclass != ui.icon:
                eclass.default_style(f'font-family: {font}')

    def add_scrollbar_color(self):
        ui.add_head_html(SCROLLBAR_HEAD)

    async def confirm_action(self, action, message = "Are you sure?", title = "Confirm", icon = "warning"):

        with ui.dialog() as dialog, ui.card():
            with ui.row():
                ui.icon(icon, size="2.3em")
                ui.label(title).style("font-weight: bold; font-size: 1.6em")
            ui.label(message)
            sure = ui.checkbox("Yes, do it already!")
            with ui.row():
                ui.button("Do it!", color="#f33", on_click=lambda: dialog.submit(True)).bind_enabled_from(sure, 'value')
                ui.button("Cancel", color="#333", on_click=lambda: dialog.submit(False))
        should_do = await dialog

        if should_do:
            action()

    def plan_card(self, plan):
        with ui.card().classes('justify-center items-center'):
            ui.label(plan["name"]).style('font-weight: 900, color: #666; font-size: 2.5em;')
            ui.label(plan["description"]).style('color: #555')

            ui.separator()
            ui.button("View", color="#444", on_click=lambda: ui.navigate.to(f"/plan/{plan['id']}"))
    
    async def new_plan(self):

        with ui.dialog() as dialog, ui.card().style("max-width: 300px; width: 100%;").classes('justify-center items-center'):
            with ui.row():
                ui.icon("rocket_launch", size="2.3em")
                ui.label("Create a new plan").style("font-weight: bold; font-size: 1.6em")
            plan_name = ui.input("Name")
            plan_desc = ui.input("Short Description")
            with ui.row():
                submit_fnc = lambda: dialog.submit((plan_name.value, plan_desc.value))
                ui.button("Create", color=self.server.config.gui.primary_color, on_click=submit_fnc)
                ui.button("Cancel", color="#333", on_click=lambda: dialog.submit(None))
            plan_name.on("keydown.enter", submit_fnc)
            plan_desc.on("keydown.enter", submit_fnc)

        plan = await dialog

        if plan:
            plan_name, plan_desc = plan
            self.server.database.new_plan(app.storage.user["username"], plan_name, plan_desc)
            self.plans.refresh()

    @ui.refreshable
    def plans(self):
        with ui.row():
            try:
                for plan in self.server.database.plans[app.storage.user["username"]]:
                    self.plan_card(plan)
            except KeyError:
                pass
                


    def index(self):

        ui.colors(primary=self.server.config.gui.primary_color, secondary='#333')

        self.add_font()
        self.add_scrollbar_color()
        ui.add_head_html(BG_HTML)
        
        log_switch = self.build_header()

        with ui.row():
            ui.label("Plans").style("font-size: 2em")
            ui.button("New", icon='add', on_click=self.new_plan).props("push fab flat")
        self.plans()
        ui.timer(self.server.config.gui.plans_update_interval, self.plans.refresh)

        logs = ui.log(max_lines=32).classes("w-full h-120").bind_visibility_from(log_switch, 'value')
        self.server.logger.on_log(logs.push)
        cmd = ui.input("Command").style("width: 100%;").bind_visibility_from(log_switch, 'value')
        def run_cmd():
            if cmd.value:
                self.server.terminal.parse(cmd.value.strip())
                cmd.value = ""
        cmd.on("keydown.enter", run_cmd)

        with ui.footer().style("background: 0; padding: 0;"):
            ui.label("Made with ❤️ by Luwe Daman").style("width: 100%; text-align: center; font-size: 0.75em; font-weight: 100;")

    def build_header(self):
        with ui.header().style("background-color:#252525"):
            with ui.row().style("flex-wrap: nowrap"):
                ui.image(source="static/logo.png").style("width: 90px; height: 90px;").props('fit=scale-down')
                with ui.column():
                    ui.label(self.server.config.server.title).style("font-weight: bold; font-size: 2em")
                    ui.label(VERSION_STRING).style("color: #999")
            
            with ui.column():
                log_switch = ui.switch("Logs")
                ui.button(app.storage.user["username"], icon="manage_accounts", color="#444", on_click=lambda: ui.navigate.to('/account')).style("text-transform: none;")
        return log_switch
                    

    def start(self):

        self.create_logo_files()
        app.add_media_files("/static", self.static_dir)

        ui.run(reload=False, port=80, dark=True, title="YaPlannin", favicon="🧭", storage_secret=self.server.config.secret.browser_storage_secret)