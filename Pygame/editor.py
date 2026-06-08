# Level Editor
import pygame
import sys
import json
import os

from tiles import EMPTY, WALL, PLAYER, BLOCK, SPIKE, FLAG, TILE_COLORS, TILE_NAMES

TILE_SIZE = 64
COLS = 10
ROWS = 10
PANEL_W = 220
WINDOW_W = TILE_SIZE * COLS + PANEL_W
WINDOW_H = TILE_SIZE * ROWS + 60
LEVELS_DIR = os.path.join(os.path.dirname(__file__), "levels")

ALL_TILES = [EMPTY, WALL, PLAYER, BLOCK, SPIKE, FLAG]


def empty_grid():
    grid = [[EMPTY] * COLS for _ in range(ROWS)]
    for c in range(COLS):
        grid[0][c] = WALL
        grid[ROWS - 1][c] = WALL
    for r in range(ROWS):
        grid[r][0] = WALL
        grid[r][COLS - 1] = WALL
    return grid


def draw_tile(surface, tile_type, col, row, offset_x=0, offset_y=60):
    x = col * TILE_SIZE + offset_x
    y = row * TILE_SIZE + offset_y
    color = TILE_COLORS.get(tile_type, (200, 200, 200))
    rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
    pygame.draw.rect(surface, color, rect)
    pygame.draw.rect(surface, (30, 30, 30), rect, 1)

    if tile_type == SPIKE:
        cx = x + TILE_SIZE // 2
        top = y + 8
        bl = (x + 10, y + TILE_SIZE - 10)
        br = (x + TILE_SIZE - 10, y + TILE_SIZE - 10)
        pygame.draw.polygon(surface, (255, 80, 80), [(cx, top), bl, br])
    elif tile_type == FLAG:
        pole_x = x + TILE_SIZE // 2
        pygame.draw.line(surface, (60, 60, 60), (pole_x, y + 10), (pole_x, y + TILE_SIZE - 10), 3)
        flag_pts = [(pole_x, y + 10), (pole_x + 22, y + 22), (pole_x, y + 34)]
        pygame.draw.polygon(surface, (255, 50, 50), flag_pts)


class Editor:
    def __init__(self):
        pygame.init()
        self.window = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        pygame.display.set_caption("Level Editor")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 28)
        self.small_font = pygame.font.SysFont(None, 22)

        self.grid = empty_grid()
        self.selected_tile = WALL
        self.current_file = None
        self.level_name = "Nuovo Livello"
        self.message = ""
        self.message_timer = 0
        self.running = True

    def _grid_pos_from_mouse(self, mx, my):
        gx = mx
        gy = my - 60
        if 0 <= gx < COLS * TILE_SIZE and 0 <= gy < ROWS * TILE_SIZE:
            return gx // TILE_SIZE, gy // TILE_SIZE
        return None

    def _save(self):
        existing = sorted(f for f in os.listdir(LEVELS_DIR) if f.endswith(".json"))
        if self.current_file:
            path = self.current_file
        else:
            idx = len(existing) + 1
            path = os.path.join(LEVELS_DIR, f"level_{idx}.json")
            self.current_file = path

        data = {"name": self.level_name, "grid": self.grid}
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        self.message = f"Salvato: {os.path.basename(path)}"
        self.message_timer = 180

    def _load(self, path):
        with open(path) as f:
            data = json.load(f)
        self.level_name = data["name"]
        self.grid = [row[:] for row in data["grid"]]
        self.current_file = path
        self.message = f"Caricato: {os.path.basename(path)}"
        self.message_timer = 180

    def _new(self):
        self.grid = empty_grid()
        self.current_file = None
        self.level_name = "Nuovo Livello"
        self.message = "Nuovo livello creato"
        self.message_timer = 180

    def _draw_panel(self):
        panel_x = COLS * TILE_SIZE
        pygame.draw.rect(self.window, (40, 40, 40), (panel_x, 0, PANEL_W, WINDOW_H))

        title = self.font.render("EDITOR", True, (255, 255, 255))
        self.window.blit(title, (panel_x + 10, 10))

        y = 50
        self.window.blit(self.font.render("Tile:", True, (200, 200, 200)), (panel_x + 10, y))
        y += 28
        self._tile_rects = {}
        for tile in ALL_TILES:
            color = TILE_COLORS[tile]
            r = pygame.Rect(panel_x + 10, y, 32, 32)
            pygame.draw.rect(self.window, color, r)
            if tile == self.selected_tile:  # ← riga corretta
                pygame.draw.rect(self.window, (255, 255, 0), r, 3)
            else:
                pygame.draw.rect(self.window, (120, 120, 120), r, 1)
            label = self.small_font.render(TILE_NAMES[tile], True, (220, 220, 220))
            self.window.blit(label, (panel_x + 50, y + 8))
            self._tile_rects[tile] = r
            y += 40

        y += 10
        buttons = [
            ("N  Nuovo",    (60, 120, 60)),
            ("S  Salva",    (60, 60, 180)),
            ("L  Carica 1", (120, 80, 40)),
        ]
        self._btn_rects = {}
        for label, color in buttons:
            br = pygame.Rect(panel_x + 10, y, PANEL_W - 20, 36)
            pygame.draw.rect(self.window, color, br, border_radius=4)
            surf = self.font.render(label, True, (255, 255, 255))
            self.window.blit(surf, surf.get_rect(center=br.center))
            self._btn_rects[label[0]] = br
            y += 46

        y += 6
        self.window.blit(self.small_font.render("Premi 1-9 per caricare livello", True, (160, 160, 160)), (panel_x + 10, y))
        y += 20
        levels = sorted(f for f in os.listdir(LEVELS_DIR) if f.endswith(".json"))
        for i, lf in enumerate(levels[:8]):
            color = (255, 220, 80) if os.path.join(LEVELS_DIR, lf) == self.current_file else (160, 160, 160)
            self.window.blit(self.small_font.render(f"{i+1}. {lf}", True, color), (panel_x + 10, y))
            y += 18

        if self.message_timer > 0:
            msg = self.font.render(self.message, True, (100, 255, 100))
            self.window.blit(msg, (panel_x + 10, WINDOW_H - 40))

    def _draw_hud(self):
        pygame.draw.rect(self.window, (20, 20, 20), (0, 0, COLS * TILE_SIZE, 60))
        name_surf = self.font.render(f"Modifica: {self.level_name}", True, (255, 255, 255))
        hint = self.small_font.render("Click sinistro: piazza  |  Click destro: cancella  |  ESC: esci", True, (140, 140, 140))
        self.window.blit(name_surf, (10, 8))
        self.window.blit(hint, (10, 36))

    def _draw_grid(self):
        for r in range(ROWS):
            for c in range(COLS):
                draw_tile(self.window, self.grid[r][c], c, r)
        mx, my = pygame.mouse.get_pos()
        pos = self._grid_pos_from_mouse(mx, my)
        if pos:
            c, r = pos
            hover_rect = pygame.Rect(c * TILE_SIZE, r * TILE_SIZE + 60, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(self.window, (255, 255, 0), hover_rect, 2)

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    if event.key == pygame.K_s:
                        self._save()
                    if event.key == pygame.K_n:
                        self._new()
                    if event.key == pygame.K_l:
                        levels = sorted(f for f in os.listdir(LEVELS_DIR) if f.endswith(".json"))
                        if levels:
                            self._load(os.path.join(LEVELS_DIR, levels[0]))
                    for i in range(1, 10):
                        if event.key == getattr(pygame, f"K_{i}"):
                            levels = sorted(f for f in os.listdir(LEVELS_DIR) if f.endswith(".json"))
                            if i - 1 < len(levels):
                                self._load(os.path.join(LEVELS_DIR, levels[i - 1]))

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    for tile, r in self._tile_rects.items():
                        if r.collidepoint(mx, my):
                            self.selected_tile = tile
                    for key, r in self._btn_rects.items():
                        if r.collidepoint(mx, my):
                            if key == "N":
                                self._new()
                            elif key == "S":
                                self._save()
                            elif key == "L":
                                levels = sorted(f for f in os.listdir(LEVELS_DIR) if f.endswith(".json"))
                                if levels:
                                    self._load(os.path.join(LEVELS_DIR, levels[0]))

            btns = pygame.mouse.get_pressed()
            if btns[0] or btns[2]:
                mx, my = pygame.mouse.get_pos()
                pos = self._grid_pos_from_mouse(mx, my)
                if pos:
                    c, r = pos
                    if btns[0]:
                        self.grid[r][c] = self.selected_tile
                    else:
                        self.grid[r][c] = EMPTY

            self.window.fill((60, 60, 60))
            self._draw_grid()
            self._draw_hud()
            self._draw_panel()

            if self.message_timer > 0:
                self.message_timer -= 1

            pygame.display.update()
            self.clock.tick(60)

        pygame.quit()


if __name__ == "__main__":
    editor = Editor()
    editor.run()