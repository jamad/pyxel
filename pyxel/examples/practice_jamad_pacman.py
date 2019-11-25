from pyxel import init,load,run,btnp,KEY_Q,cls,bltm,btn,KEY_W,KEY_S,KEY_D,KEY_A,tilemap
import pyxel

class Pacman:#pacman自体を生成するクラス
    def __init__(self):
        self.P=[8,8]
        self.V=[0,0]# パックマンの進む方向の情報 unit: タイル
        self.T=[1,1]# 今いるタイルを座標化する
        self.ori=0# 0方向なし, 1 上, 2を右,3を下,4を左
        self.pattern = 0# どのパックマンをプロットするかの情報
        self.score = 0# スコア

class App:
    def __init__(self):
        init(128,128,caption="pacman-ish", fps=25,scale=2)
        load('pacman.pyxres')

        self.pacman=Pacman() #################  抜けてるだろ！
        self.tilemap_state=tilemap(0)#################  抜けてるだろ！ 超重要！！！

        run(self.update, self.draw)# 毎フレーム毎にupdateとdrawを呼び出す

    def update(self):# ゲーム内情報更新、キー入力処理
        if btnp(KEY_Q):quit()# qキーで終了
        if self.pacman.P[0]%8==0 and self.pacman.P[1]%8==0:# 移動判定
            if self.tilemap_state.get(self.pacman.T[0]+self.pacman.V[0],self.pacman.T[1]+self.pacman.V[1])==33:# 進行方向を確認 壁に行こうとしてたら
                self.pacman.V[0] = self.pacman.V[1] = 0# stop
            elif btn(KEY_W) and self.tilemap_state.get(self.pacman.T[0],self.pacman.T[1]-1)!=33:self.pacman.V= [0,-1] # 上に行くように設定
            elif btn(KEY_S) and self.tilemap_state.get(self.pacman.T[0],self.pacman.T[1]+1)!=33:self.pacman.V =[0,1] # 描画する向きを下に設定
            elif btn(KEY_D) and self.tilemap_state.get(self.pacman.T[0]+1,self.pacman.T[1])!=33:self.pacman.V= [1,0]# 描画する向きを右に設定
            elif btn(KEY_A) and self.tilemap_state.get(self.pacman.T[0]-1,self.pacman.T[1])!=33:self.pacman.V =[-1,0]# 描画する向きを左に設定

            self.pacman.T=[x+y for x,y in zip(self.pacman.T,self.pacman.V)]# タイルの座標を進行方向に合わせて変える

        self.pacman.P=[x+y for x,y in zip(self.pacman.P,self.pacman.V)]# 毎フレーム毎に描画する座標を変更していく

    def draw(self):# ゲーム内描画処理
        cls(0)# 真っ黒背景塗りつぶし
        
        # タイルマップの描画処理
        x=y=u=v=tm=0#template番号
        w=h=16# block size
        bltm(x,y,tm,u,v,w,h)# 指定したtemplate番号のuv座標をxy座標にマップして描画する

        # pacmanの描画処理
        if self.pacman.V[0]  or self.pacman.V[1]:self.pacman.pattern={(0,-1):8,(0,1):24,(1,0):16,(-1,0):32}[tuple(self.pacman.V)]# 移動する場合、向きに応じた口パターンをゲット
        if pyxel.frame_count%2==0:self.pacman.pattern = 0# 口の動きを表現するために、2フレームに１回丸の状態を表示する
        # イメージ０に登録されている(self.pacman.pattern,0)の座標から 8×8サイズを参照にして、(self.pacman.P[0],self.pacman.P[1])の座標に描画する
        pyxel.blt(self.pacman.P[0],self.pacman.P[1],0,self.pacman.pattern,0,8,8)

App()
