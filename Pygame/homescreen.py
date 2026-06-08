import pygame
import os
import sys


LEVELS_DIR = os.path.join(os.path.dirname(__file__), "levels")


def list_levels():
    return sorted(
        os.path.join(LEVELS_DIR, f)
        for f in os.listdir(LEVELS_DIR)
        if f.endswith(".json")
    )


class FloatingTile:
    def __init__(self, w, h):
        import random
        self.w = w
        self.h = h
        self.size = random.randint(30, 90)
        self.x = float(random.randint(0, w))
        self.y = float(random.randint(0, h))
        self.vx = random.uniform(-40, 40)
        self.vy = random.uniform(-40, 40)
        self.color = (120, 120, 160)
        self.alpha = random.randint(40, 120)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt

        if self.x < -self.size: self.x = self.w
        if self.x > self.w: self.x = -self.size
        if self.y < -self.size: self.y = self.h
        if self.y > self.h: self.y = -self.size

    def draw(self, surf):
        s = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        s.fill((*self.color, self.alpha))
        surf.blit(s, (int(self.x), int(self.y)))


class Launcher:
    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.sw, self.sh = self.screen.get_size()

        pygame.display.set_caption("Grid Puzzle Launcher")

        self.font_title = pygame.font.SysFont(None, 120)
        self.font = pygame.font.SysFont(None, 60)
        self.small = pygame.font.SysFont(None, 36)

        self.tiles = [FloatingTile(self.sw, self.sh) for _ in range(20)]

        self.buttons = {}
        self._build_buttons()

        self.levels = list_levels()
        self.show_levels = False
        self.level_rects = {}
        self.selected = 0

        self.running = True

    # ───────────────────────────────

    def _build_buttons(self):
        cx = self.sw // 2
        cy = self.sh // 2

        w = 320
        h = 70
        gap = 20

        labels = ["Play", "Editor", "Livelli", "Esci"]

        start_y = cy - (len(labels) * (h + gap)) // 2

        for i, label in enumerate(labels):
            rect = pygame.Rect(
                cx - w // 2,
                start_y + i * (h + gap),
                w,
                h
            )
            self.buttons[label] = rect

    # ───────────────────────────────

    def run(self):
        clock = pygame.time.Clock()

        while self.running:
            dt = clock.tick(60) / 1000

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False

                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        if self.show_levels:
                            self.show_levels = False
                        else:
                            self.running = False

                if e.type == pygame.MOUSEBUTTONDOWN:
                    self.click(e.pos)

            for t in self.tiles:
                t.update(dt)

            self.draw()
            pygame.display.flip()

        pygame.quit()
        sys.exit()

    # ───────────────────────────────

    def click(self, pos):

        if self.show_levels:
            for i, r in self.level_rects.items():
                if r.collidepoint(pos):
                    self.launch_game(i)
                    return

        else:
            if self.buttons["Play"].collidepoint(pos):
                self.launch_game(self.selected)

            elif self.buttons["Editor"].collidepoint(pos):
                self.launch_editor()

            elif self.buttons["Livelli"].collidepoint(pos):
                self.show_levels = True

            elif self.buttons["Esci"].collidepoint(pos):
                self.running = False

    # ───────────────────────────────

    def launch_game(self, level):
        pygame.quit()
        os.execv(sys.executable, [
            sys.executable,
            "main.py",
            str(level)
        ])

    def launch_editor(self):
        pygame.quit()
        os.execv(sys.executable, [sys.executable, "editor.py"])

    # ───────────────────────────────

    def draw(self):
        self.screen.fill((18, 18, 28))

        for t in self.tiles:
            t.draw(self.screen)

        # titolo
        title = self.font_title.render("GRID PUZZLE", True, (255, 255, 255))
        self.screen.blit(title, title.get_rect(center=(self.sw // 2, self.sh // 4)))

        # bottoni
        for label, rect in self.buttons.items():
            color = (80, 120, 180) if label == "Play" else (70, 70, 100)

            if rect.collidepoint(pygame.mouse.get_pos()):
                color = tuple(min(255, c + 30) for c in color)

            pygame.draw.rect(self.screen, color, rect, border_radius=12)

            txt = self.font.render(label, True, (255, 255, 255))
            self.screen.blit(txt, txt.get_rect(center=rect.center))

        if self.show_levels:
            self.draw_levels()

    # ───────────────────────────────

    def draw_levels(self):
        overlay = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Rect(self.sw//2 - 250, self.sh//2 - 250, 500, 500)
        pygame.draw.rect(self.screen, (40, 40, 60), panel, border_radius=15)

        title = self.font.render("Seleziona Livello", True, (255, 255, 255))
        self.screen.blit(title, title.get_rect(center=(self.sw//2, panel.y + 40)))

        self.level_rects = {}

        y = panel.y + 100

        for i, path in enumerate(self.levels[:8]):
            name = os.path.basename(path).replace(".json", "")

            rect = pygame.Rect(panel.x + 50, y, 400, 50)

            color = (120, 120, 180) if i == self.selected else (70, 70, 90)

            pygame.draw.rect(self.screen, color, rect, border_radius=8)

            txt = self.small.render(name, True, (255, 255, 255))
            self.screen.blit(txt, txt.get_rect(center=rect.center))

            self.level_rects[i] = rect
            y += 60


if __name__ == "__main__":
    Launcher().run()