from random import randint as RDI
from pyxel import init,load,playm,run,btnp,KEY_Q,btn,KEY_LEFT,GAMEPAD_1_LEFT,KEY_RIGHT,GAMEPAD_1_RIGHT,play,cls,blt,text
import pyxel

W=160
H=120
class App:
    def __init__(self):
        init(W, H, caption="Pyxel Jump",scale=2)
        load("assets/jump_game.pyxres")

        self.score = self.pVY = 0
        self.pX=72
        self.pY=-16
        self.p_alive = 1
        self.far_cloud = [(-10, 75), (40, 65), (90, 60)]
        self.near_cloud = [(10, 25), (70, 35), (H, 15)]
        self.floor = [(i * 60, RDI(8, 104), 1) for i in range(4)]
        self.fruit = [(i * 60, RDI(0, 104), RDI(0, 2), 1) for i in range(4)]

        playm(0, loop=1)

        run(self.update, self.draw)

    def update(self):
        if btnp(KEY_Q):quit()
        for i, v in enumerate(self.floor):self.floor[i] = self.update_floor(*v)
        for i, v in enumerate(self.fruit):self.fruit[i] = self.update_fruit(*v)

        if btn(KEY_LEFT) or btn(GAMEPAD_1_LEFT):self.pX = max(self.pX - 2, 0)
        if btn(KEY_RIGHT) or btn(GAMEPAD_1_RIGHT):self.pX = min(self.pX + 2, pyxel.width - 16)
        self.pY += self.pVY
        self.pVY = min(self.pVY + 1, 8)

        if self.pY > pyxel.height:
            if self.p_alive:
                self.p_alive = 0
                play(3, 5)

            if self.pY > 600:
                self.score = 0
                self.pX = 72
                self.pY = -16
                self.pVY = 0
                self.p_alive = 1

    def update_floor(self, x, y, a):
        if a:
            if (
                self.pX + 16 >= x
                and self.pX <= x + 40
                and self.pY + 16 >= y
                and self.pY <= y + 8
                and self.pVY > 0
            ):
                a = 0
                self.score += 10
                self.pVY = -12
                play(3, 3)
        else:y+=6
        x-=4
        if x<-40: x,y,a=x+240,RDI(8,104),1
        return x, y, a

    def update_fruit(self, x, y, k, a):
        if a and abs(x - self.pX) < 12 and abs(y - self.pY) < 12:
            a = 0
            self.score += (k + 1) * 100
            self.pVY = min(self.pVY, -8)
            play(3, 4)
        x -= 2
        if x < -40:
            x += 240
            y = RDI(0, 104)
            k = RDI(0, 2)
            a = 1
        return (x, y, k, a)

    def draw(self):
        fcount=pyxel.frame_count
        cls(12)# background color
        blt(0, 88, 0, 0, 88, W, 32)# sky
        blt(0, 88, 0, 0, 64, W, 24, 12)# draw mountain
        for i in range(2): blt(i*W-fcount%W, 104, 0, 0, 48, W, 16, 12)# draw forest

        for i in range(2):
            for x, y in self.far_cloud:blt(x+i*W-(fcount // 16) % W, y, 0, 64, 32, 32, 8, 12)# draw clouds

        for i in range(2):
            for x, y in self.near_cloud:blt(x+i*W-(fcount // 8) % W, y, 0, 0, 32, 56, 8, 12)

        for x, y, a in self.floor:blt(x,y,0, 0, 16, 40, 8, 12)# draw floors
        
        for x, y, k, a in self.fruit:
            if a:blt(x, y, 0, 32 + k*16, 0, 16, 16, 12)# draw fruits
        
        blt(self.pX, self.pY, 0,  16*(0<self.pVY),      0,16, 16, 12, )# draw player

        s = "SCORE {:>4}".format(self.score)# draw score
        text(5, 4, s, 1)
        text(4, 4, s, 7)
App()