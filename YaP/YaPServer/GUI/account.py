
from nicegui import app, ui
import time

@ui.page("/account")
def account():
    user = app.storage.user["username"]
    AccountManager(user)

BG_HTML = """<style>
@keyframes diagonal-scroll {
    from {
        background-position: 0% 0%; /* Start at top-left */
    }
    to {
        background-position: 0% 100%; /* Move to bottom-right (repeating) */
    }
}
body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;

            background-image: url("/static/logo.png");
            background-repeat: repeat;
            background-size: 10vw 10vw;

            filter: grayscale(1) opacity(0.05); /* Apply grayscale and reduce opacity for subtlety */
            z-index: -1; /* Place it behind the actual body content */
            animation: diagonal-scroll 60s linear infinite;
        }
</style>
"""

class AccountManager:

    GUI = None
    NEW_USERNAME_RULES = {"Too long! Max 32 characters.": lambda inp: len(inp) < 32, "Can only contain alphanumerics and underscores.": lambda inp: all(char.upper() in "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_" for char in inp)}

    def __init__(self, user):
        
        self.gui_user = user
        self.server = self.GUI.server

        self.user_data = self.server.uds.load(self.gui_user)

        ui.page_title(f"YaPlannin: {self.gui_user}")
        ui.colors(primary=self.server.config.gui.primary_color, secondary='#333')
        self.GUI.add_font()
        ui.add_head_html(BG_HTML)

        self.build()

    def format_time(self, t):
        return time.strftime("%c", time.localtime(t))

    async def change_pass_diag(self):
        with ui.dialog() as dialog, ui.card().style("max-width: 300px; width: 100%;").classes('justify-center items-center'):
            with ui.row():
                ui.icon("edit", size="2.3em")
                ui.label("Edit Password").style("font-weight: bold; font-size: 1.6em")
            P1 = ui.input("Password", password=True, password_toggle_button=True)
            P2 = ui.input("Password again", password=True, password_toggle_button=True, validation={"Doesn't match.": lambda inp: inp == P1.value})
            def submit_pass():
                if P1.value != P2.value:
                    ui.notify("Passwords don't match.", type="negative")
                else:
                    dialog.submit(P1.value)
            with ui.row():
                ui.button("Change", color=self.server.config.gui.action_color, on_click=submit_pass)
                ui.button("Cancel", color="#333", on_click=lambda: dialog.submit(False))
            P1.on("keydown.enter", lambda: submit_pass)
            P2.on("keydown.enter", lambda: submit_pass)
        passw = await dialog

        if passw:
            self.server.log(f"Changed password for user '{self.gui_user}'")
            self.user_data.change_password(passw)
            ui.notify("Password changed.", type="positive")

    async def add_account_diag(self):
        with ui.dialog() as dialog, ui.card().style("max-width: 300px; width: 100%;").classes('justify-center items-center'):
            with ui.row():
                ui.icon("person_add", size="2.3em")
                ui.label("Add Account").style("font-weight: bold; font-size: 1.6em")
            U = ui.input("Username", validation=AccountManager.NEW_USERNAME_RULES)
            P1 = ui.input("Password", password=True, password_toggle_button=True)
            P2 = ui.input("Password again", password=True, password_toggle_button=True, validation={"Doesn't match.": lambda inp: inp == P1.value})
            def submit_cred():
                if P1.value != P2.value:
                    ui.notify("Passwords don't match.", type="negative")
                else:
                    dialog.submit((U.value, P1.value))
            with ui.row():
                ui.button("Create", color=self.server.config.gui.action_color, on_click=submit_cred)
                ui.button("Cancel", color="#333", on_click=lambda: dialog.submit(False))
            P1.on("keydown.enter", lambda: submit_cred)
            P2.on("keydown.enter", lambda: submit_cred)
        cred = await dialog

        if cred:
            user, passw = cred
            self.server.log(f"User '{self.gui_user}' has created a new user: '{user}'")
            try:
                self.server.uds.new(user, passw)
                ui.notify(f"User '{user}' created.", type="positive")
            except ValueError as e:
                ui.notify(f"Failed: {e}", type="negative")

    async def delete_account(self):

        with ui.dialog() as dialog, ui.card():
            with ui.row():
                ui.icon("warning", size="2.3em")
                ui.label("Delete my account.").style("font-weight: bold; font-size: 1.6em")
            ui.label("This will permanently delete this account and you will no longer be able to log in with your credentials.")
            sure = ui.checkbox("Yes, do it already!")
            with ui.row():
                ui.button("Do it!", color=self.server.config.gui.action_color, on_click=lambda: dialog.submit(True)).bind_enabled_from(sure, 'value')
                ui.button("Cancel", color="#333", on_click=lambda: dialog.submit(False))
        should_do = await dialog

        if should_do:
            self.user_data.delete()
            ui.navigate.to('/')

    def build(self):

        with ui.card().classes('absolute-center justify-center items-center').style("min-width: 90vw;"):
            ui.image(source="/static/logo.png").style("width: 90px; height: 90px;")
            with ui.column().style("align-items: center;"):
                ui.label(self.gui_user).style("font-size: 3em;")
                with ui.column():
                    ui.label(f'Created: {self.format_time(self.user_data.created)}').style("color: #999")
                    ui.label(f'Last login: {self.format_time(self.user_data.last_login)}').style("color: #999")
                    ui.label(f'Last changed: {self.format_time(self.user_data.last_write)}').style("color: #999")
                with ui.row():
                    ui.button(icon="edit", text="Edit", on_click=self.change_pass_diag, color="#444").style('width: 10em;')
                    ui.button("Logout", icon="logout", on_click=lambda: ui.navigate.to('/logout')).style('width: 10em;')
                with ui.row():
                    ui.button(icon="person_add", text="Add", on_click=self.add_account_diag, color="#444").style('width: 10em;')
                    ui.button(icon="person_remove", text="Delete", on_click=self.delete_account).style('width: 10em;')
                ui.button(icon="keyboard_return", text="Back", on_click=lambda: ui.navigate.to("/"), color="#444").style('width: 22em;')

