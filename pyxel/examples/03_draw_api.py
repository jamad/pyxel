import math
import pyxel
from pyxel import init,image,tilemap,mouse,run,btn,cls,KEY_SPACE,btnp,KEY_Q,quit,text,clip,pix,line,rect,rectb,circ,circb,blt,bltm,pal

class App:
    def __init__(self):
        init(256, 256, caption="Pyxel Draw API",scale=1)
        image(0).load(0, 0, "assets/cat_16x16.png")
        image(1).load(0, 0, "assets/tileset_24x32.png")
        tilemap(0).set( 0,0, ["022000002004001000060061062000040", "042003020021022003000001002003060"],)
        tilemap(0).refimg = 1
        self.pal_test_is_enabled = False
        self.clip_test = False
        mouse(True)
        run(self.update, self.draw)

    def update(self):
        self.pal_test_is_enabled = (pyxel.frame_count // 30) % 10 >= 5
        self.clip_test = btn(KEY_SPACE)
        if btnp(KEY_Q):quit()

    def draw(self):
        self.test_pal1()# what's pal ?
        self.test_cls(6, 6)
        self.test_clip()
        self.test_pix(6, 20)
        self.test_line(106, 6)
        self.test_rect(6, 38)
        self.test_rectb(106, 38)
        self.test_circ(6, 61)
        self.test_circb(106, 61)
        self.test_blt(6, 88)
        self.test_bltm(106, 88)
        self.test_text(6, 124)
        self.test_pal2(106, 124)

    def test_pal1(self):
        if self.pal_test_is_enabled:
            pal(2, 3)
            pal(4, 7)
            pal(7, 10)

    def test_pal2(self, x, y):
        text(x, y, "pal(col1,col2)", 4)
        pal()

    def test_cls(self, x, y):
        cls(2)
        text(x, y, "cls(col)", 7)

    def test_clip(self):
        fc=pyxel.frame_count
        clip()
        if not self.clip_test:return
        x = math.sin(fc * 0.02) * 39 + 40
        y = math.sin(fc * 0.03) * 29 + 30
        w = 120
        h = 90
        text(x, y - 8, "clip(x,y,w,h)", 14)
        rectb(x - 1, y - 1, w + 2, h + 2, 14)
        clip(x, y, w, h)

    def test_pix(self, x, y):
        text(x, y, "pix(x,y,col)", 7)
        x += 4
        y += 10
        for i in range(16):pix(x + i * 2, y, i)

    def test_line(self, x, y):
        text(x, y, "line(x1,y1,x2,y2,col)", 7)
        x += 4
        y += 9
        col = 5

        for i in range(3):
            line(x, y + i * 8, x + 48, y + i * 8, col)
            col += 1

        for i in range(4):
            line(x + i * 16, y, x + i * 16, y + 16, col)
            col += 1

        for i in range(4):
            line(x + i * 16, y, x + (3 - i) * 16, y + 16, col)
            col += 1

    def test_rect(self, x, y):
        text(x, y, "rect(x,y,w,h,col)", 7)

        x += 4
        y += 16

        for i in range(8):
            rect(x + i * 8, y - i, i + 1, i + 1, i + 8)

    def test_rectb(self, x, y):
        text(x, y, "rectb(x,y,w,h,col)", 7)
        x += 4
        y += 16
        for i in range(8):
            rectb(x + i * 8, y - i, i + 1, i + 1, i + 8)

    def test_circ(self, x, y):
        text(x, y, "circ(x,y,r,col)", 7)
        x += 4
        y += 15
        for i in range(8):
            circ(x + i * 8, y, i, i + 8)

    def test_circb(self, x, y):
        text(x, y, "circb(x,y,r,col)", 7)
        x += 4
        y += 15
        for i in range(8):circb(x + i * 8, y, i, i + 8)

    def test_blt(self, x, y):
        fc=pyxel.frame_count
        text(x, y, "blt(x,y,img,u,v,\n    w,h,[colkey])", 7)
        y += 15
        offset = math.sin(fc * 0.1) * 2

        blt(x, y, 0, 0, 0, 16, 16)
        blt(x + offset + 19, y, 0, 0, 0, 16, 16, 5)
        blt(x + 38, y, 0, 0, 0, -16, 16, 5)
        blt(x + 57, y, 0, 0, 0, 16, -16, 5)
        blt(x + 76, y, 0, 0, 0, -16, -16, 5)

    def test_bltm(self, x, y):
        text(x, y, "bltm(x,y,tm,u,v,\n     w,h,[colkey])", 7)
        y += 15
        bltm(x, y, 0, 0, 0, 11, 2, 2)

    def test_text(self, x, y):
        fc=pyxel.frame_count
        text(x, y, "text(x,y,s,col)", 7)
        x += 4
        y += 8
        s = "Elapsed frame count is {}\n" "Current mouse position is ({},{})".format(fc, pyxel.mouse_x, pyxel.mouse_y    )
        text(x + 1, y, s, 1)
        text(x, y, s, 9)
App()