from random import randint as RDI
from pyxel import init,load,playm,run,btnp,KEY_Q,btn,KEY_LEFT,GAMEPAD_1_LEFT,KEY_RIGHT,GAMEPAD_1_RIGHT,play,cls,blt,text
import pyxel

W=160
H=120
score = pVY = 0
pX=72
pY=-16
p_alive = 1
far_cloud = [(-10, 75), (40, 65), (90, 60)]
near_cloud = [(10, 25), (70, 35), (H, 15)]
floor = [(i * 60, RDI(8, 104), 1) for i in range(4)]
fruit = [(i * 60, RDI(0, 104), RDI(0, 2), 1) for i in range(4)]

init(W, H, caption="Pyxel Jump",scale=2)
load("assets/jump_game.pyxres")

playm(0, loop=1)

def update():
    global pY,pVY,p_alive,score
    if btnp(KEY_Q):quit()
    for i, v in enumerate(floor):floor[i] = update_floor(*v)
    for i, v in enumerate(fruit):fruit[i] = update_fruit(*v)

    if btn(KEY_LEFT) or btn(GAMEPAD_1_LEFT):pX = max(pX - 2, 0)
    if btn(KEY_RIGHT) or btn(GAMEPAD_1_RIGHT):pX = min(pX + 2, pyxel.width - 16)
    pY += pVY
    pVY = min(pVY + 1, 8)

    if pY > pyxel.height:
        if p_alive:
            p_alive = 0
            play(3, 5)

        if pY > 600:
            score = 0
            pX = 72
            pY = -16
            pVY = 0
            p_alive = 1

def update_floor( x, y, a):
    global pVY,score
    if a:
        if x-16 <= pX <= x + 40  and y-16 <= pY <= y + 8 and pVY > 0:
            a = 0
            score += 10
            pVY = -12
            play(3, 3)
    else:y+=6
    x-=4
    if x<-40: x,y,a=x+240,RDI(8,104),1
    return x, y, a

def update_fruit( x, y, k, a):
    global score,pVY
    if a and abs(x - pX) < 12 and abs(y - pY) < 12:
        a = 0
        score += (k + 1) * 100
        pVY = min(pVY, -8)
        play(3, 4)
    x -= 2
    if x < -40:
        x += 240
        y = RDI(0, 104)
        k = RDI(0, 2)
        a = 1
    return (x, y, k, a)

def draw():
    fcount=pyxel.frame_count
    cls(12)# background color
    blt(0, 88, 0, 0, 88, W, 32)# sky
    blt(0, 88, 0, 0, 64, W, 24, 12)# draw mountain
    for i in range(2): blt(i*W-fcount%W, 104, 0, 0, 48, W, 16, 12)# draw forest

    for i in range(2):
        for x, y in far_cloud:blt(x+i*W-(fcount // 16) % W, y, 0, 64, 32, 32, 8, 12)# draw clouds

    for i in range(2):
        for x, y in near_cloud:blt(x+i*W-(fcount // 8) % W, y, 0, 0, 32, 56, 8, 12)

    for x, y, a in floor:blt(x,y,0, 0, 16, 40, 8, 12)# draw floors
    
    for x, y, k, a in fruit:
        if a:blt(x, y, 0, 32 + k*16, 0, 16, 16, 12)# draw fruits
    
    blt(pX, pY, 0,  16*(0<pVY),      0,16, 16, 12, )# draw player

    s = "SCORE {:>4}".format(score)# draw score
    text(5, 4, s, 1)
    text(4, 4, s, 7)

run(update, draw)