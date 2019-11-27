from pyxel import init,run, cls, tri
class App:
    def __init__(self):
        init(200, 110,scale=1)
        run(self.update, self.draw)
    def update(self):pass
    def draw(self):
        cls(5)
        tri(100, 0, 0, 100, 199, 100, 8)
App()