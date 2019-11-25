from pyxel import circ,cls,flip,init
t,s=0,128
R=range(0,s,4)
init(s,s,scale=2)
while 1:
 cls(0)
 for x in R:
  for y in R:
   d=((x-64)**2+(y-64)**2)**.5
   b=__import__('math').sin((t+d)/5)*4
   circ(x+b,y+b,1,d/4%16)
 t+=1
 flip()