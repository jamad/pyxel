import pyxel

class App:
    def __init__(self):
        # ゲームの設定。widthとheightの単位はドット
        # init(width, height, [caption], [fps])
        pyxel.init(128,128,caption="パックマンぽいゲーム", fps=25,scale=2)

        # 作成したドット絵やタイルマップの情報を読み込む
        pyxel.load('pacman.pyxres')
        # 毎フレーム毎にupdateとdrawを呼び出す
        pyxel.run(self.update, self.draw)

    # ゲーム内で扱う情報を更新したり、キー入力の処理などを行う
    def update(self):
        # qキーが押されたらゲームを終了する。
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

    # ゲーム内で描画されるドット絵の処理をする
    def draw(self):
        # 真っ黒に背景をする
        pyxel.cls(0)
        # タイルマップを描画する
        self.tilemap_draw()

    # タイルマップの描画処理
    def tilemap_draw(self):
        base_x = 0
        base_y = 0
        tm = 0
        u = 0
        v = 0
        w = 16
        h = 16
        # 指定したtm(template)番号の(u,v)座標から
        # サイズ(w,h)の大きさを(base_x,base_y)座標に描画する
        pyxel.bltm(base_x,base_y,tm,u,v,w,h)
App()
