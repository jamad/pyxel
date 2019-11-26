from random import randint as RDI
from pyxel import init,load,playm,run,btnp,KEY_Q,btn,KEY_LEFT,GAMEPAD_1_LEFT,KEY_RIGHT,GAMEPAD_1_RIGHT,play,cls,blt,text
import pyxel
W=H=160
score=pVY=0
pX,pY,p_alive=72,-16,1
cl_far,cl_near=[(-10, 75),(40, 65),(90, 60)],[(10, 25),(70, 35),(H, 15)]
floor=[(i*60,RDI(8,104), 1) for i in range(4)]
fruit=[(i*60,RDI(0,104), RDI(0,2),1) for i in range(4)]
_,__,___=init(W,H,caption="Pyxel Jump",scale=2),load("assets/jump_game.pyxres"),playm(0,loop=1)
def update():
    global pX,pY,pVY,p_alive,score
    if btnp(KEY_Q):quit()
    for i,(x,y,a)in enumerate(floor):# update_floor
        if a and x-16<=pX<=x+40 and y-16<=pY<=y+8 and 0<pVY:a,score,pVY,_=0,score+10,-12,play(3, 3)
        y+=not a and 6
        x-=4
        if x<-40:x,y,a=x+240,RDI(8,104),1
        floor[i]=x,y,a
    for i, (x,y,k,a) in enumerate(fruit):
        if a and abs(x-pX)<12 and abs(y-pY)<12:a,score,pVY,_=0,score+(k+1)*100,min(pVY,-8),play(3,4)
        x-=2
        if x<-40:x,y,k,a=x+240,RDI(0,104),RDI(0,2),1
        fruit[i]=x,y,k,a
    if btn(KEY_LEFT)or btn(GAMEPAD_1_LEFT):pX=max(pX-2,0)
    if btn(KEY_RIGHT)or btn(GAMEPAD_1_RIGHT):pX=min(pX+2,pyxel.width-16)
    pY+=pVY
    pVY=min(pVY+1,8)
    if pY > pyxel.height:
        if p_alive:(p_alive,_)=(0,play(3, 5))# play sound could be merged !
        if pY > 600: score,pX,pY,pVY,p_alive=0,72,-16,0,1
def draw():
    fcount=pyxel.frame_count
    cls(12)# background color
    blt(0, 88, 0, 0, 88, W, 32)# sky
    blt(0, 88, 0, 0, 64, W, 24, 12)# draw mountain
    for i in range(2): blt(i*W-fcount%W, 104, 0, 0, 48, W, 16, 12)# draw forest
    [blt(x+i*W-(fcount//16) % W, y, 0, 64, 32, 32, 8, 12)for i in range(2)for x, y in cl_far]# draw clouds
    [blt(x+i*W-(fcount//8) % W, y, 0, 0, 32, 56, 8, 12)for i in range(2)for x, y in cl_near]
    for x, y, a in floor:blt(x,y,0, 0, 16, 40, 8, 12)# draw floors
    for x, y, k, a in fruit:_=a and blt(x, y, 0, 32 + k*16, 0, 16, 16, 12)# draw fruits
    blt(pX,pY,0,16*(0<pVY),0,16, 16, 12)# draw player
    s="SCORE {:>4}".format(score)# score
    _,__=text(5,4,s,1),text(4,4,s,7)# score draw
run(update, draw)