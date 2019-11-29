import pyxel as P
from pyxel import init,image,run,cls,text,blt,btnp
class App:
    def __init__(self):
        init(160, 120, caption="Hello Pyxel",scale=1)
        image(0).load(0, 0, "assets/pyxel_logo_38x16.png")
        run(self.update, self.draw)

    def update(self):
        if btnp(P.KEY_Q):quit()

    def draw(self):
        cls(0)
        text(55, 41, "Hello, Pyxel!", P.frame_count % 16)
        blt(61, 66, 0, 0, 0, 38, 16)
App()
