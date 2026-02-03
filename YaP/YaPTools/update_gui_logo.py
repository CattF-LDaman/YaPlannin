
import base64

fs = "LOGO_PNG = {}\nLOGO_ICO = {}\nLOGO_EDGE_PNG = {}"

def update_logo():

    with open("YaP/YaPServer/GUI/logo_raw.py","w",encoding="utf-8") as f:
        with open("logo.png","rb") as png:
            with open("logo.ico","rb") as ico:
                with open("logo-edge.png","rb") as png_e:
                    f.write(fs.format(str(png.read()), str(ico.read()), str(png_e.read())))

if __name__ == "__main__":
    update_logo()