
import base64

fs = "LOGO_PNG = {}\nLOGO_ICO = {}"

def update_logo():

    with open("YaP/YaPServer/GUI/logo_raw.py","w",encoding="utf-8") as f:
        with open("logo.png","rb") as png:
            with open("logo.ico","rb") as ico:
                f.write(fs.format(str(png.read()), str(ico.read())))

if __name__ == "__main__":
    update_logo()