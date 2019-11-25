from pyxel import init,load,run,btnp,KEY_Q,cls,bltm,btn,KEY_W,KEY_S,KEY_D,KEY_A
import pyxel

class Pacman:#pacman自体を生成するクラス
    def __init__(self):
        self.posX = self.posY = 8
        self.V=[0,0]# パックマンの進む方向の情報 unit: タイル
        self.ori = 0# 0方向なし, 1 上, 2を右,3を下,4を左
        self.tile_x = self.tile_y = 1# 今いるタイルを座標化する
        self.pattern = 0# どのパックマンをプロットするかの情報
        self.score = 0# スコア

class TilemapState:#################  抜けてるだろ！
    def get(self,x,y):
#        print(x,y)
        return 64

class App:
    def __init__(self):
        init(128,128,caption="pacman-ish", fps=25,scale=2)
        load('pacman.pyxres')

        self.pacman=Pacman() #################  抜けてるだろ！
        self.tilemap_state=TilemapState()

        run(self.update, self.draw)# 毎フレーム毎にupdateとdrawを呼び出す

    def update(self):# ゲーム内情報更新、キー入力処理
        if btnp(KEY_Q):quit()# qキーで終了
        
        if self.pacman.posX % 8 == 0 and self.pacman.posY % 8 == 0:# 移動判定
            # 進行方向を確認 壁に行こうとしてたら
            tilePX=self.pacman.tile_x
            tilePY=self.pacman.tile_y
            if self.tilemap_state.get(tilePX + self.pacman.V[0], tilePY + self.pacman.V[1]) == 33:
                self.pacman.V[0] = self.pacman.V[1] = 0# stop
            elif btn(KEY_W):
#                if self.tilemap_state.get(tilePX, tilePY - 1) in(5,64,65):# 次に移動する先が、背景、クッキー、パワークッキーなら
                    self.pacman.V[0] =  0
                    self.pacman.V[1] = -1# 上に行くように設定
                    self.pacman.ori = 1# 描画する向きを上に設定
            elif btn(KEY_S):
#                if self.tilemap_state.get(tilePX, tilePY + 1) in(5,64,65):    # 下に行くように設定
                    self.pacman.V[0] =  0
                    self.pacman.V[1] =  1
                    # 描画する向きを下に設定
                    self.pacman.ori = 2
            # Dキーが押されていた場合に
            elif btn(KEY_D):
#                if self.tilemap_state.get(tilePX+1, tilePY) in(5,64,65):    # 右に行くように設定
                    self.pacman.V[0] =  1
                    self.pacman.V[1] =  0
                    # 描画する向きを右に設定
                    self.pacman.ori = 3
            # Aキーが押されていた場合に
            elif btn(KEY_A):
#                if self.tilemap_state.get(tilePX-1, tilePY) in(5,64,65):    # 左にいくように設定
                    self.pacman.V[0] = -1
                    self.pacman.V[1] =  0
                    # 描画する向きを左に設定
                    self.pacman.ori = 4

            # タイルの座標を進行方向に合わせて変える
            tilePX += self.pacman.V[0]
            tilePY += self.pacman.V[1]

        # 毎フレーム毎に描画する座標を変更していく
        self.pacman.posX += self.pacman.V[0]
        self.pacman.posY += self.pacman.V[1]

    def draw(self):# ゲーム内描画処理
        cls(0)# 真っ黒背景塗りつぶし
        
        # タイルマップの描画処理
        x=y=u=v=tm=0#template番号
        w=h=16# block size
        bltm(x,y,tm,u,v,w,h)# 指定したtemplate番号のuv座標をxy座標にマップして描画する

        # pacmanの描画処理
        if self.pacman.V[0]  or self.pacman.V[1]:self.pacman.pattern={1:8,2:24,3:16,4:32}[self.pacman.ori]# 移動する場合、向きに応じた口パターンをゲット
        if pyxel.frame_count%2==0:self.pacman.pattern = 0# 口の動きを表現するために、2フレームに１回丸の状態を表示する
        # イメージ０に登録されている(self.pacman.pattern,0)の座標から 8×8サイズを参照にして、(self.pacman.posX,self.pacman.posY)の座標に描画する
        pyxel.blt(self.pacman.posX,self.pacman.posY,0,self.pacman.pattern,0,8,8)

App()
