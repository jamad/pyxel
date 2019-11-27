import math
import pyxel
from pyxel import init,image,tilemap,mouse,run,btn,cls,KEY_SPACE,btnp,KEY_Q,quit,text,clip,pix,line,rect,rectb,circ,circb,blt,bltm,pal
class App:
    def __init__(self):
        init(256, 256, caption="Pyxel Draw API",scale=2)
        image(0).load(0, 0, "assets/cat_16x16.png")
        image(1).load(0, 0, "assets/tileset_24x32.png")
        tilemap(0).set( 0,0, ["022000002004001000060061062000040", "042003020021022003000001002003060"],)
        tilemap(0).refimg = 1
        self.pal_test_is_enabled = 0
        self.clip_test = 0
        mouse(1)
        run(self.update, self.draw)
    def update(self):
        self.pal_test_is_enabled = (pyxel.frame_count // 30) % 10 >= 5
        self.clip_test = btn(KEY_SPACE)
        if btnp(KEY_Q):quit()
    def draw(self):
        fc=pyxel.frame_count
        if self.pal_test_is_enabled:_,__,___=pal(2,3),pal(4,7),pal(7,10) # pallet swap - test_pal1
        _,__=cls(2),text(6,6, "cls(col)",7) #self.test_cls(6, 6)
        
        self.test_clip()
        
        text(6, 20, "pix(x,y,col)", 7)
        for i in range(16):pix(10 + i*2, 30, i)

        text(106, 6, "line(x1,y1,x2,y2,col)", 7)
        for i in range(3):line(110, 15 + i * 8, 158, 15 + i * 8, 5+i)
        for i in range(4):line(110 + i*16, 15,110 + i * 16,31, 8+i)
        for i in range(4):line(110 + i*16, 15,110+ (3 - i) * 16,31, 12+i)
        
        text(6, 38, "rect(x,y,w,h,col)", 7)
        for i in range(8):rect(10 + i * 8, 54 - i, i + 1, i + 1, i + 8)

        text(106, 38, "rectb(x,y,w,h,col)", 7)
        for i in range(8):rectb(110+i*8,54- i, i + 1, i + 1, i + 8)

        text(6,61, "circ(x,y,r,col)", 7)
        for i in range(8):circ(10+ i * 8,76, i, i + 8)
        
        text(106, 61, "circb(x,y,r,col)", 7)
        for i in range(8):circb(110+i*8,76,i,i+8)

        text(6,88, "blt(x,y,img,u,v,\n    w,h,[colkey])", 7)
        x,y=6,103
        blt(x, y, 0, 0, 0, 16, 16)
        blt(x + math.sin(fc * 0.1) * 2 + 19, y, 0, 0, 0, 16, 16, 5)
        blt(x + 38, y, 0, 0, 0, -16, 16, 5)
        blt(x + 57, y, 0, 0, 0, 16, -16, 5)
        blt(x + 76, y, 0, 0, 0, -16, -16, 5)

        text(106, 88, "bltm(x,y,tm,u,v,\n w,h,[colkey])", 7)
        bltm(106, 103, 0, 0, 0, 11, 2, 2)

        text(6, 124, "text(x,y,s,col)", 7)
        x,y=10,132
        s = "Elapsed frame count is {}\n" "Current mouse position is ({},{})".format(fc, pyxel.mouse_x, pyxel.mouse_y    )
        text(x+1,y,s,1)# shadow
        text(x,y,s,9)

        _,__=text(106, 124, "pal(col1,col2)", 4),pal()# test_pal2 

    def test_clip(self):
        if not self.clip_test:return
        fc=pyxel.frame_count
        clip()
        x,y,w,h=math.sin(fc*0.02)*39+40,math.sin(fc*0.03)*29+30,120,90
        text(x,y-8,"clip(x,y,w,h)",14)
        rectb(x-1,y-1,w+2,h+2,14)
        clip(x,y,w,h)
App()