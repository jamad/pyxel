import pyxel,math
from pyxel import init,image,sound,run,play,stop,cls,btnp,text,rect,rectb,pal,play_pos,blt,quit
class App:
    def __init__(self):
        init(200, 150, caption="Pixel Sound API",scale=1)
        image(0).set(0,0,[ "00011000", "00010100", "00010010","00010010","00010100","00010000","01110000","01100000"])
        sound(0).set( "e2e2c2g1 g1g1c2e2 d2d2d2g2 g2g2rr" "c2c2a1e1 e1e1a1c2 b1b1b1e2 e2e2rr","p","6","vffn fnff vffs vfnn",25)
        sound(1).set("r a1b1c2 b1b1c2d2 g2g2g2g2 c2c2d2e2" "f2f2f2e2 f2e2d2c2 d2d2d2d2 g2g2r r ","s","6","nnff vfff vvvv vfff svff vfff vvvv svnn",  25 )
        sound(2).set("c1g1c1g1 c1g1c1g1 b0g1b0g1 b0g1b0g1" "a0e1a0e1 a0e1a0e1 g0d1g0d1 g0d1g0d1","t", "7", "n", 25, )
        sound(3).set( "f0c1f0c1 g0d1g0d1 c1g1c1g1 a0e1a0e1" "f0c1f0c1 f0c1f0c1 g0d1g0d1 g0d1g0d1","t","7","n",25,)
        sound(4).set("f0ra4r f0ra4r f0ra4r f0f0a4r", "n", "6622 6622 6622 6422", "f", 25        )
        self.play_music(1, 1, 1)
        run(self.update, self.draw)
    def play_music(self, ch0, ch1, ch2):
        if ch0: play(0,[0, 1], loop=1)
        else: stop(0)
        if ch1: play(1,[2, 3], loop=1)
        else: stop(1)
        if ch2: play(2,4, loop=1)
        else: stop(2)
    def update(self):
        if btnp(pyxel.KEY_Q): quit()
        if btnp(pyxel.KEY_1): self.play_music(1, 1, 1)
        if btnp(pyxel.KEY_2): self.play_music(1, 0, 0)
        if btnp(pyxel.KEY_3): self.play_music(0, 1, 0)
        if btnp(pyxel.KEY_4): self.play_music(0, 0, 1)
        if btnp(pyxel.KEY_5): self.play_music(0, 0, 0)
    def draw(self):
        cls(1)
        text(6, 6, "sound(snd).set(note,tone,volume,effect,speed)", 7)
        rect(12, 14, 177, 35, 2)
        text(16, 17, "note  :[CDEFGAB] + [ #-] + [0-4] or [R]", 9)
        text(16, 25, "tone  :[T]riangle [S]quare [P]ulse [N]oise", 9)
        text(16, 33, "volume:[0-7]", 9)
        text(16, 41, "effect:[N]one [S]lide [V]ibrato [F]adeOut", 9)
        text(6, 53, "music(msc).set(ch0,ch1,ch2,ch3)", 7)
        text(6, 62, "play(ch,snd,loop=0)", 7)
        text(6, 71, "playm(msc,loop=0)", 7)
        text(6, 80, "stop([ch])", 7)
        rectb(6, 97, 188, 47, 14)
        rect(6, 91, 29, 7, 14)
        text(7, 92, "CONTROL", 1)
        text(12, 102, "1: Play all channels", 14)
        text(12, 110, "2: Play channel #0 (Melody)", 14)
        text(12, 118, "3: Play channel #1 (Bass)", 14)
        text(12, 126, "4: Play channel #2 (Drums)", 14)
        text(12, 134, "5: Stop playing", 14)
        text(137, 107, "play_pos(ch)", 15)
        for i in range(3):
            x = 140 + i * 16
            y = 123 + math.sin(pyxel.frame_count * 0.1 + i * 2.1) * 5
            col = 15 if play_pos(i) >= 0 else 13
            pal(1, col)
            blt(x, y, 0, 0, 0, 8, 8, 0)
        pal()
App()