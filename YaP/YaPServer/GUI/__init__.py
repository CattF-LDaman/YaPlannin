
from YaP.YaPCore.threading import threaded_daemon
from YaP.YaPCore.version import VERSION_STRING

from YaP.YaPServer.GUI.logo_raw import LOGO_ICO, LOGO_PNG
from YaP.YaPServer.GUI.geo import get_flag_icon_from_ip
from YaP.YaPServer.GUI.account import AccountManager
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
}</style>"""

class GUI:

    SERVER = None

    def __init__(self, server) -> None:
        
        self.server = GUI.SERVER = server
        
        self.static_dir = self.server.dirs["guistatic"]

        AccountManager.GUI = self

        # app.add_static_files("/downloads", self.server.dirs['downloads'])

        ui.page('/')(self.index)

    def create_logo_files(self):
        with open(os.path.join(self.static_dir, "logo.png"), "wb") as png:
            png.write(LOGO_PNG)

    def add_font(self):

        font = '"Quicksand", sans-serif'
        ui.add_head_html(FONT_HEAD)
        classes = [cls for name, cls in inspect.getmembers(ui, inspect.isclass) if hasattr(cls, 'default_style') and callable(getattr(cls, 'default_style'))] 
        for eclass in classes:
            if eclass != ui.icon:
                eclass.default_style(f'font-family: {font}')

    def add_scrollbar_color(self):
        ui.add_head_html(SCROLLBAR_HEAD)

    def index(self):

        ui.colors(primary=self.server.config.gui.primary_color, secondary='#333')

        self.add_font()
        self.add_scrollbar_color()
        
        log_switch = self.build_header()

        # Index content here

        logs = ui.log(max_lines=32).classes("w-full h-120").bind_visibility_from(log_switch, 'value')
        self.server.logger.on_log(logs.push)
        cmd = ui.input("Command").style("width: 100%;").bind_visibility_from(log_switch, 'value')
        def run_cmd():
            if cmd.value:
                self.server.terminal.parse(cmd.value.strip())
                cmd.value = ""
        cmd.on("keydown.enter", run_cmd)

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

        ui.run(reload=False, dark=True, title="YaPlannin", favicon="🧭", storage_secret=self.server.config.secret.browser_storage_secret)