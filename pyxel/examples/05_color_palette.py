from pyxel import init,run,btnp,quit,cls,DEFAULT_PALETTE,rect,text,rectb
import pyxel as P
class App:
    def __init__(self):
        init(255, 81, caption="Pyxel Color Palette",scale=2)
        run(self.update, self.draw)
    def update(self):
        if btnp(P.KEY_Q):quit()
        if btnp(P.KEY_Z):pass # need to know to change scale from 1 to 2
    def draw(self):
        cls(0)
        for i in range(16):
            x, y, col=2+i%4*64, 4+i//4*20, i
            v = DEFAULT_PALETTE[col]
            if col:rect(x, y, 13, 13, col)
            else:rectb(x, y, 13, 13, 5)
            text(x+16, y+1, "#{:06X}".format(v), 7)
            text(x+16, y+8, f"{v>>16},{(v>>8)&0xFF},{v&0xFF}",7)
            text(x+5-col//10*2, y+4, f"{col}",7*(col<6))
App()