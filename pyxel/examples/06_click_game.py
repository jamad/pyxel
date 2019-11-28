import math, random, pyxel
from pyxel import init,mouse,run,btnp,cls,quit,circ,text
SCREEN_WIDTH = SCREEN_HEIGHT = 256
B_MAX_V = 1.8
B_INIT_NUM = 50
B_EXP_NUM = 11
class Bubble:
    def __init__(self):
        self.r = random.uniform(3, 10)
        self.posX = random.uniform(self.r, SCREEN_WIDTH - self.r)
        self.posY = random.uniform(self.r, SCREEN_HEIGHT - self.r)
        self.velX=random.uniform(-B_MAX_V, B_MAX_V)
        self.velY=random.uniform(-B_MAX_V, B_MAX_V)
        self.color = random.randint(1, 15)
    def update(self):
        self.posX += self.velX
        self.posY += self.velY
        if self.velX < 0 and self.posX < self.r:self.velX *= -1
        if self.velX > 0 and self.posX > SCREEN_WIDTH - self.r:self.velX *= -1
        if self.velY < 0 and self.posY < self.r:self.velY *= -1
        if self.velY > 0 and self.posY > SCREEN_HEIGHT - self.r:self.velY *= -1
class App:
    def __init__(self):
        init(SCREEN_WIDTH, SCREEN_HEIGHT, caption="Pyxel Bubbles",scale=1)
        mouse(True)
        self.is_exploded = False
        self.bubbles = [Bubble() for _ in range(B_INIT_NUM)]
        run(self.update, self.draw)
    def update(self):
        if btnp(pyxel.KEY_Q):quit()
        bubble_count = len(self.bubbles)
        if btnp(pyxel.MOUSE_LEFT_BUTTON):
            for i in range(bubble_count):
                bubble = self.bubbles[i]
                dx = bubble.posX - mouse_x
                dy = bubble.posY - mouse_y
                if dx * dx + dy * dy < bubble.r * bubble.r:
                    self.is_exploded = True
                    new_r = math.sqrt(bubble.r * bubble.r / B_EXP_NUM)
                    for j in range(B_EXP_NUM):
                        angle = math.pi * 2 * j / B_EXP_NUM
                        new_bubble = Bubble()
                        new_bubble.r = new_r
                        new_bubble.posX = bubble.posX + (bubble.r + new_r) * math.cos(angle)
                        new_bubble.posY = bubble.posY + (bubble.r + new_r) * math.sin(angle)
                        new_bubble.velX = math.cos(angle) * B_MAX_V
                        new_bubble.velY = math.sin(angle) * B_MAX_V
                        self.bubbles.append(new_bubble)
                    del self.bubbles[i]
                    break
        for i in range(bubble_count - 1, -1, -1):
            bi = self.bubbles[i]
            bi.update()
            for j in range(i - 1, -1, -1):
                bj = self.bubbles[j]
                dx = bi.posX - bj.posX
                dy = bi.posY - bj.posY
                total_r = bi.r + bj.r
                if dx * dx + dy * dy < total_r * total_r:
                    new_bubble = Bubble()
                    new_bubble.r = math.sqrt(bi.r * bi.r + bj.r * bj.r)
                    new_bubble.posX = (bi.posX * bi.r + bj.posX * bj.r) / total_r
                    new_bubble.posY = (bi.posY * bi.r + bj.posY * bj.r) / total_r
                    new_bubble.velX = (bi.velX * bi.r + bj.velX * bj.r) / total_r
                    new_bubble.velY = (bi.velY * bi.r + bj.velY * bj.r) / total_r
                    self.bubbles.append(new_bubble)
                    del self.bubbles[i]
                    del self.bubbles[j]
                    bubble_count -= 1
                    break
    def draw(self):
        cls(0)
        for bubble in self.bubbles:circ(bubble.posX, bubble.posY, bubble.r, bubble.color)
        if not self.is_exploded and pyxel.frame_count % 20 < 10:text(96, 50, "CLICK ON BUBBLE", pyxel.frame_count % 15 + 1)
App()