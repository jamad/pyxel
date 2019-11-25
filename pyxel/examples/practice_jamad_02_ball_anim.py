from pyxel import init,cls,circ,circb,flip
x=y=30  # ボールの座標
u=v=5  # ボールの速度
c=1 # ball color
init(159, 119,scale=1)  # 160x120で画面を作成する
while 1:
    cls(1)  # fill screen by color 1
    x,y=x+u,y+v
    if not 7<x<152:u,c=-u,c+1# x reflect
    if not 7<y<112:v,c=-v,c+1# y reflect
    circ(min(max(x,7),152),min(max(y,7),112),7,c%16)  # draw ball
    circb(min(max(x,7),152),min(max(y,7),112),7,(c+1)%16)  # draw ball outline
    flip()  # draw screen