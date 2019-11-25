from pyxel import init,load,run,btnp,KEY_Q,cls,bltm

class App:
    def __init__(self):
        init(128,128,caption="pacman-ish", fps=25,scale=2)
        load('pacman.pyxres')
        run(self.update, self.draw)# 毎フレーム毎にupdateとdrawを呼び出す

    def update(self):# ゲーム内情報更新、キー入力処理
        if btnp(KEY_Q):quit()# qキーで終了

    def draw(self):# ゲーム内描画処理
        cls(0)# 真っ黒背景塗りつぶし

        # タイルマップの描画処理
        x=y=u=v=tm=0#template番号
        w=h=16# block size
        bltm(x,y,tm,u,v,w,h)# 指定したtemplate番号のuv座標をxy座標にマップして描画する
App()
