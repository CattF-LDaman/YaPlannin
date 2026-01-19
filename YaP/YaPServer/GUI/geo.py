import requests
from functools import lru_cache
from nicegui import ui

@lru_cache
def get_country_code_from_ip(ip):
    response = requests.get(f"http://ip-api.com/json/{ip}")
    data = response.json()
    return data.get("countryCode")  # e.g., 'US'

def country_code_to_emoji(code):
    if not code:
        return ""
    return "".join(chr(ord(c) + 127397) for c in code.upper())

def country_code_to_icon(code, size=16):
    return ui.image(source=f"https://flagsapi.com/{code}/flat/{size}.png").props(f"no-transition loading=immediate width={size}px height={size}px")
    
def get_flag_emoji_from_ip(ip):
    code = get_country_code_from_ip(ip)
    return country_code_to_emoji(code)
    
def get_flag_icon_from_ip(ip, size=16):
    code = get_country_code_from_ip(ip)
    return country_code_to_icon(code)