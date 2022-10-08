import numpy as np
from utils import update_batch, allocate_spots

BLACK = (61, 60, 66)
WHITE = (255, 255, 255)
GRAY = (207, 210, 207)
COLOR = (84, 186, 185), (255, 91, 0)


class Env:
    def __init__(self, graphics=False, fps: int = None, batch_size=128):
        self.graphics = graphics
        self.fps = fps
        self.batch_size = batch_size
        self.state = np.zeros((self.batch_size, 4, 6, 6), dtype=int)
        self.turns = 0
        self.mode = 'train'

        if self.graphics:
            import pygame as pg

            pg.init()
            pg.display.init()
            pg.display.set_caption('Pop it!')
            screen_size = np.array([1440, 1440])
            self.window = pg.display.set_mode(screen_size)
            self.screen = pg.Surface(screen_size, pg.SRCALPHA)

            self.grid = pg.Surface(screen_size, pg.SRCALPHA)
            pg.draw.line(self.grid, GRAY, (0, 722), (1440, 722), width=5)
            pg.draw.line(self.grid, GRAY, (720, 0), (720, 1440), width=5)
            for i in range(13):
                x = 120 * i
                pg.draw.line(self.grid, GRAY, (0, x), (1440, x), width=3)
                pg.draw.line(self.grid, GRAY, (x, 0), (x, 1440), width=3)

            self.canvas = [pg.Surface((720, 720), pg.SRCALPHA) for _ in range(4)]
            self.rect = [canvas.get_rect() for canvas in self.canvas]
            for i, rect in enumerate(self.rect):
                rect.topleft = (i % 2 * 720, i // 2 * 720)

            self.clock = pg.time.Clock()
            self.font = pg.font.Font(pg.font.get_default_font(), 17)
            self.render(self.state[:4])

    def reset(self):
        self.state = np.zeros((self.batch_size, 4, 6, 6), dtype=int)
        self.turns = 0
        return self.state, np.full(self.batch_size, False), None

    def step(self, state, action):
        update_batch(state, action)
        self.turns += 1
        pieces = state[:, :2].sum(axis=(2, 3))
        done = ~pieces.all(axis=1) if self.turns > 2 else np.full(len(state), False)
        rewards = np.where(pieces[:, 0] > 0, 1, -1) if np.all(done) else None
        return state, done, rewards

    def render(self, state):
        if not self.graphics: return
        import pygame as pg

        self.screen.fill(WHITE)

        for n, state in enumerate(state):
            canvas, rect = self.canvas[n], self.rect[n]
            self.screen.blit(canvas, rect)
            for player in (0, 1):
                for i, row in enumerate(state[player]):
                    for j, num in enumerate(row):
                        cx, cy = j * 120 + 60 + rect.x, i * 120 + 60 + rect.y
                        spots = allocate_spots(num)
                        for d in spots:
                            pg.draw.circle(self.screen, COLOR[player], (cx + d[0], cy + d[1]), 14)

        self.screen.blit(self.grid, (0, 0))
        size = np.array(self.window.get_rect().size)
        if self.mode == 'interactive':
            size *= 2
        self.window.blit(pg.transform.scale(self.screen, size), (0, 0))
        pg.event.pump()
        pg.display.update()
        if self.fps and self.mode == 'train': self.clock.tick(self.fps)

    def paint_canvas(self, p):
        if not self.graphics: return
        import pygame as pg

        for j, p in enumerate(p):
            canvas = self.canvas[j]
            for i, alpha in enumerate(p):
                pg.draw.rect(canvas, (220, 214, 247, alpha * 255),
                             pg.Rect(i % 6 * 120, i // 6 * 120, 120, 120))

    def render_text(self, p, q, n):
        if not self.graphics: return

        for j, (p, q, n) in enumerate(zip(p, q, n)):
            canvas = self.canvas[j]
            for i, (_p, _q, _n) in enumerate(zip(p, q, n)):
                texts = f'π: {_p: .4f}', f'Q: {_q: .4f}', f'SEL: {_n: .0f}'
                c = (i % 6 * 120 + 60, i // 6 * 120 + 60)
                position = (c[0], c[1] - 50), (c[0], c[1] - 35), (c[0], c[1] + 50)
                for text, pos in zip(texts, position):
                    text = self.font.render(text, True, BLACK)
                    rect = text.get_rect()
                    rect.center = pos
                    canvas.blit(text, rect)

    @staticmethod
    def wait():
        import pygame as pg
        while True:
            for event in pg.event.get():
                if event.type == pg.MOUSEBUTTONDOWN:
                    action = event.pos[1] // 240 * 6 + event.pos[0] // 240
                    return np.array([action])

    def close(self):
        if not self.graphics: return
        import pygame as pg
        pg.display.quit()
        pg.quit()
