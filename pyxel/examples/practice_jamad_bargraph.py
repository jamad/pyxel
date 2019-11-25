from pyxel import init,line,rect,show
A=[4, 7, 5, 2, 10, 5, 4, 2]  # グラフデータ
init(64,64,scale=2)# 128x128画面
line(0, 60, 63, 60, 8)  # グラフ下直線
for i,h in enumerate(A):rect(i*7+6, 60-h*5, 5, h*5, 8+i) # 色を変え矩形描画
show()