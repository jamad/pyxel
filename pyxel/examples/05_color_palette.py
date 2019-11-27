from pyxel import init,run,btnp,quit,cls,DEFAULT_PALETTE,rect,text,rectb
import pyxel
class App:
    def __init__(self):
        init(255, 81, caption="Pyxel Color Palette",scale=1)
        run(self.update, self.draw)
    def update(self):
        if btnp(pyxel.KEY_Q):quit()
        if btnp(pyxel.KEY_Z):pass # need to know to change scale from 1 to 2
    def draw(self):
        cls(0)
        for i in range(16):
            x, y, col=(2 + (i % 4) * 64, 4 + (i // 4) * 20, i)
            col_val = DEFAULT_PALETTE[col]
            hex_col = "#{:06X}".format(col_val)
            rgb_col = "{},{},{}".format( col_val >> 16, (col_val >> 8) & 0xFF, col_val & 0xFF)
            rect(x, y, 13, 13, col)
            text(x + 16, y + 1, hex_col, 7)
            text(x + 16, y + 8, rgb_col, 7)
            text(x + 5 - (col // 10) * 2, y + 4, "{}".format(col), 7 if col < 6 else 0      )
            if col == 0:rectb(x, y, 13, 13, 5)
App()