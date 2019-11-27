from pyxel import init,run,cls,tri
init(128,128,scale=1)
run(lambda:None,lambda:[cls(5),tri(64,0,0,64,128,128,8)])