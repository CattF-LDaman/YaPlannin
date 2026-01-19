from typing import Optional

from fastapi import Request
from fastapi.responses import RedirectResponse, PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware

from nicegui import app, ui

from YaP.YaPServer.Data.userdata import UserData

unrestricted_page_routes = {'/login', '/static/logo.png'}

class AuthMiddleware(BaseHTTPMiddleware):
    """This middleware restricts access to all NiceGUI pages.

    It redirects the user to the login page if they are not authenticated.
    """

    async def dispatch(self, request: Request, call_next):
        from YaP.YaPServer.GUI import GUI
        if not GUI.SERVER:
            return RedirectResponse(f'/login?redirect_to={request.url.path}')
        if request.client.host in GUI.SERVER.config.banned.banned_hosts:
            GUI.SERVER.log(f"Request from banned host '{request.client.host}' blocked.", 3) # Log the blocked attempt
            return PlainTextResponse("Access Denied: Your IP address has been banned.", status_code=403)
        if not app.storage.user.get('authenticated', False):
            if not request.url.path.startswith('/_nicegui') and request.url.path not in unrestricted_page_routes:
                GUI.SERVER.log(f"[GUI] No auth, redirecting to login @ < {request.client.host}:{request.client.port} > {request.method} {request.url.path}")
                return RedirectResponse(f'/login?redirect_to={request.url.path}')
        elif not GUI.SERVER.uds.exists(app.storage.user.get('username', "")):
            GUI.SERVER.log(f"Request for '{request.url.path}' from '{request.client.host}'  blocked, user '{app.storage.user.get('username', "")}' not found.", 3)
            app.storage.user.clear()
            return RedirectResponse(f'/login?redirect_to={request.url.path}')
        if not (request.url.path.startswith("/_nicegui") or request.url.path.startswith("/static")):
            GUI.SERVER.log(f"[GUI] {app.storage.user.get('username', "")} @ < {request.client.host}:{request.client.port} > {request.method} {request.url.path}")
        return await call_next(request)


app.add_middleware(AuthMiddleware)


BG_HTML = """<style>
@keyframes rotate-background {
    0% {
        background-position: 0% 0%;
    }
    100% {
        background-position: 100% 100%;
    }
}

body::before {
    content: '';
    position: fixed;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;

    background-image: url("/static/logo.png");
    background-repeat: repeat;
    background-size: 100px 100px;

    filter: grayscale(1) opacity(0.05);
    z-index: -1;

    animation: rotate 60s linear infinite;
    transform-origin: center center;
}

@keyframes rotate {
    from {
        transform: rotate(0deg);
    }
    to {
        transform: rotate(360deg);
    }
}
</style>

"""

@ui.page('/login')
def login(redirect_to: str = '/') -> Optional[RedirectResponse]:
    from YaP.YaPServer.GUI import GUI
    if not GUI.SERVER:
        ui.label("Server broken: no server.")
        return
    
    ui.colors(primary='#f99', secondary='#333')
    ui.add_head_html(BG_HTML)

    def try_login() -> None:

        if GUI.SERVER.uds.exists(username.value) and GUI.SERVER.uds.load(username.value).check_password(password.value):
            app.storage.user.update({'username': username.value, 'authenticated': True})
            GUI.SERVER.uds.load(username.value).login()
            ui.navigate.to(redirect_to)
            GUI.SERVER.log(f"User '{username.value}' logged in to GUI.", 2)
        else:
            ui.notify('Wrong credentials.', color='negative')
            GUI.SERVER.log(f"Someone failed to log in to GUI using following username: {username.value}", 3)

    if app.storage.user.get('authenticated', False):
        return RedirectResponse('/')
    with ui.card().classes('absolute-center'):
        ui.label(GUI.SERVER.config.server.title).style("font-family: 'Courier New', monospace; text-align:center;")
        username = ui.input('Username').on('keydown.enter', try_login).style("font-family: 'Courier New', monospace;")
        password = ui.input('Password', password=True, password_toggle_button=True).on('keydown.enter', try_login).style("font-family: 'Courier New', monospace;")
        ui.button('Log in', on_click=try_login).style("font-family: 'Courier New', monospace;")
    return None

@ui.page("/logout")
def logout():
    app.storage.user.clear()
    ui.navigate.to('/login')
