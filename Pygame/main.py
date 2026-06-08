# Credit to "@sturdy-robot" for the tile-based movement
import pygame
import sys
import json
import os

print("Made by: Keijo11.\nCredit to @sturdy-robot for the tile-based movement.\nHere the GitHub: https://gist.github.com/sturdy-robot")

from tiles import EMPTY, WALL, PLAYER, BLOCK, SPIKE, FLAG, TILE_COLORS

TILE_SIZE = 64
COLS = 10
ROWS = 10
GAME_W = TILE_SIZE * COLS
GAME_H = TILE_SIZE * ROWS + 60
LEVELS_DIR = os.path.join(os.path.dirname(__file__), "levels")
SPEED = 400


def load_level(path):
    with open(path) as f:
        data = json.load(f)
    return data["name"], [row[:] for row in data["grid"]]


def list_levels():
    files = sorted(f for f in os.listdir(LEVELS_DIR) if f.endswith(".json"))
    return [os.path.join(LEVELS_DIR, f) for f in files]


def draw_spike(surface, x, y):
    color_base = (150, 150, 160)
    color_tip  = (220, 220, 230)
    n = 3
    w = TILE_SIZE // n
    for i in range(n):
        bx = x + i * w
        tip = (bx + w // 2, y + 6)
        bl  = (bx + 2,      y + TILE_SIZE - 6)
        br  = (bx + w - 2,  y + TILE_SIZE - 6)
        pygame.draw.polygon(surface, color_base, [tip, bl, br])
        pygame.draw.polygon(surface, color_tip,  [tip, (bx + w//2 - 2, y + TILE_SIZE - 6),
                                                        (bx + w//2 + 2, y + TILE_SIZE - 6)], 2)


def draw_flag(surface, x, y):
    pole_x = x + TILE_SIZE // 2
    pygame.draw.line(surface, (60, 60, 60), (pole_x, y + 8), (pole_x, y + TILE_SIZE - 8), 3)
    flag_pts = [(pole_x, y + 8), (pole_x + 22, y + 20), (pole_x, y + 32)]
    pygame.draw.polygon(surface, (255, 50, 50), flag_pts)


def draw_tile(surface, tile_type, px, py):
    color = TILE_COLORS.get(tile_type, (200, 200, 200))
    rect  = pygame.Rect(px, py, TILE_SIZE, TILE_SIZE)
    pygame.draw.rect(surface, color, rect)
    pygame.draw.rect(surface, (30, 30, 30), rect, 1)
    if tile_type == SPIKE:
        draw_spike(surface, px, py)
    elif tile_type == FLAG:
        draw_flag(surface, px, py)


# ── Entità mobili ─────────────────────────────────────────────────────────────

class MovingEntity:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.px  = float(col * TILE_SIZE)
        self.py  = float(row * TILE_SIZE)
        self.target_px = self.px
        self.target_py = self.py
        self.moving = False

    def start_move(self, dr, dc):
        self.row += dr
        self.col += dc
        self.target_px = float(self.col * TILE_SIZE)
        self.target_py = float(self.row * TILE_SIZE)
        self.moving = True

    def update(self, dt):
        if not self.moving:
            return
        pos    = pygame.math.Vector2(self.px, self.py)
        target = pygame.math.Vector2(self.target_px, self.target_py)
        pos    = pos.move_towards(target, SPEED * dt)
        self.px, self.py = pos.x, pos.y
        if pos == target:
            self.moving = False

    def draw(self, surface, color, hud_offset):
        rect = pygame.Rect(int(self.px), int(self.py) + hud_offset, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(surface, color, rect)
        pygame.draw.rect(surface, (30, 30, 30), rect, 1)


# ── World ─────────────────────────────────────────────────────────────────────

class World:
    HUD = 60

    def __init__(self):
        self.levels    = list_levels()
        self.level_idx = 0
        self.font      = pygame.font.SysFont(None, 32)
        self.big_font  = pygame.font.SysFont(None, 64)
        self._load()

    def _load(self):
        self.level_name, self.grid = load_level(self.levels[self.level_idx])
        self.player   = None
        self.blocks   = []
        self.state    = "playing"
        self.key_held = False

        for r in range(ROWS):
            for c in range(COLS):
                t = self.grid[r][c]
                if t == PLAYER:
                    self.player = MovingEntity(r, c)
                    self.grid[r][c] = EMPTY
                elif t == BLOCK:
                    self.blocks.append(MovingEntity(r, c))
                    self.grid[r][c] = EMPTY

    def _get_tile(self, r, c):
        if 0 <= r < ROWS and 0 <= c < COLS:
            return self.grid[r][c]
        return WALL

    def _block_at(self, r, c):
        for b in self.blocks:
            if b.row == r and b.col == c:
                return b
        return None

    def _try_move(self, dr, dc):
        nr = self.player.row + dr
        nc = self.player.col + dc
        target = self._get_tile(nr, nc)

        if target == WALL:
            return

        block = self._block_at(nr, nc)
        if block:
            bnr = nr + dr
            bnc = nc + dc
            beyond_tile  = self._get_tile(bnr, bnc)
            beyond_block = self._block_at(bnr, bnc)

            if beyond_tile == WALL or beyond_block:
                return

            if beyond_tile == SPIKE:
                self.grid[bnr][bnc] = EMPTY
                self.blocks.remove(block)
            elif beyond_tile == FLAG:
                self.blocks.remove(block)
            else:
                block.start_move(dr, dc)

        if target == SPIKE:
            self.player.start_move(dr, dc)
            self.state = "gameover"
            return

        if target == FLAG:
            self.player.start_move(dr, dc)
            self.state = "win"
            return

        self.player.start_move(dr, dc)

    def handle_input(self):
        keys = pygame.key.get_pressed()
        any_dir = (keys[pygame.K_UP] or keys[pygame.K_DOWN] or
                   keys[pygame.K_LEFT] or keys[pygame.K_RIGHT])

        if self.key_held:
            if not any_dir:
                self.key_held = False
            return

        if self.player.moving:
            return

        if keys[pygame.K_UP]:
            self._try_move(-1, 0); self.key_held = True
        elif keys[pygame.K_DOWN]:
            self._try_move(1,  0); self.key_held = True
        elif keys[pygame.K_LEFT]:
            self._try_move(0, -1); self.key_held = True
        elif keys[pygame.K_RIGHT]:
            self._try_move(0,  1); self.key_held = True

    def update(self, dt):
        self.player.update(dt)
        for b in self.blocks:
            b.update(dt)

    def draw(self, surface):
        for r in range(ROWS):
            for c in range(COLS):
                draw_tile(surface, self.grid[r][c], c * TILE_SIZE, r * TILE_SIZE + self.HUD)

        for b in self.blocks:
            b.draw(surface, TILE_COLORS[BLOCK], self.HUD)

        self.player.draw(surface, TILE_COLORS[PLAYER], self.HUD)

        pygame.draw.rect(surface, (30, 30, 30), (0, 0, GAME_W, self.HUD))
        name = self.font.render(
            f"{self.level_name}  [{self.level_idx+1}/{len(self.levels)}]", True, (255, 255, 255))
        surface.blit(name, (10, 18))

        if self.state in ("win", "gameover"):
            overlay = pygame.Surface((GAME_W, GAME_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            surface.blit(overlay, (0, 0))
            txt = self.big_font.render(
                "HAI VINTO!" if self.state == "win" else "GAME OVER",
                True, (255, 220, 0) if self.state == "win" else (255, 60, 60))
            surface.blit(txt, txt.get_rect(center=(GAME_W // 2, GAME_H // 2)))
            sub = self.font.render("Invio: continua  R: riavvia", True, (220, 220, 220))
            surface.blit(sub, sub.get_rect(center=(GAME_W // 2, GAME_H // 2 + 55)))

    def next_level(self):
        self.level_idx = (self.level_idx + 1) % len(self.levels)
        self._load()

    def restart(self):
        self._load()

    def reload_levels(self):
        self.levels = list_levels()
        self._load()


# ── Menu laterale ─────────────────────────────────────────────────────────────

class SideMenu:
    BTN_W  = 180
    BTN_H  = 50
    MARGIN = 16

    def __init__(self, font, small_font):
        self.font         = font
        self.small_font   = small_font
        self.open         = False
        self.buttons      = ["Editor", "Reset", "Quit"]
        self._rects       = {}
        self._lvl_rects   = {}
        self._fs_rects    = {}
        self.tab_rect     = pygame.Rect(0, 0, 1, 1)
        self.levels       = []
        self._current_idx = 0

    def toggle(self):
        self.open = not self.open

    def set_levels(self, levels, current_idx):
        self.levels = levels
        self._current_idx = current_idx

    def draw(self, surface, tab_x, tab_y):
        tab_w, tab_h = 90, 80
        self.tab_rect = pygame.Rect(tab_x, tab_y, tab_w, tab_h)
        pygame.draw.rect(surface, (50, 50, 60), self.tab_rect, border_radius=10)
        pygame.draw.rect(surface, (80, 80, 100), self.tab_rect, 2, border_radius=10)
        arrow = "◀" if self.open else "▶"
        a_surf = self.font.render(arrow, True, (220, 220, 220))
        surface.blit(a_surf, a_surf.get_rect(center=(tab_x + tab_w // 2, tab_y + 28)))
        m_surf = self.font.render("MENU", True, (160, 160, 180))
        surface.blit(m_surf, m_surf.get_rect(center=(tab_x + tab_w // 2, tab_y + 58)))

        if not self.open:
            return

        panel_x = tab_x
        panel_y = tab_y + tab_h + 10
        panel_w = self.BTN_W + self.MARGIN * 2

        panel_h = len(self.buttons) * (self.BTN_H + self.MARGIN) + self.MARGIN
        pygame.draw.rect(surface, (40, 40, 50), (panel_x, panel_y, panel_w, panel_h), border_radius=10)
        pygame.draw.rect(surface, (80, 80, 100), (panel_x, panel_y, panel_w, panel_h), 2, border_radius=10)

        self._rects = {}
        for i, label in enumerate(self.buttons):
            bx = panel_x + self.MARGIN
            by = panel_y + self.MARGIN + i * (self.BTN_H + self.MARGIN)
            br = pygame.Rect(bx, by, self.BTN_W, self.BTN_H)
            colors = {"Editor": (60, 100, 180), "Reset": (60, 160, 60), "Quit": (180, 60, 60)}
            pygame.draw.rect(surface, colors[label], br, border_radius=8)
            t = self.font.render(label, True, (255, 255, 255))
            surface.blit(t, t.get_rect(center=br.center))
            self._rects[label] = br

        lvl_y = panel_y + panel_h + 20
        hdr = self.small_font.render("LIVELLI", True, (180, 180, 200))
        pygame.draw.rect(surface, (40, 40, 50), (panel_x, lvl_y, panel_w, 28), border_radius=6)
        surface.blit(hdr, (panel_x + self.MARGIN, lvl_y + 6))
        lvl_y += 34

        self._lvl_rects = {}
        for i, path in enumerate(self.levels):
            name = os.path.basename(path).replace(".json", "").replace("_", " ").title()
            br = pygame.Rect(panel_x + self.MARGIN, lvl_y, self.BTN_W, 40)
            is_current = (i == self._current_idx)
            bg = (80, 110, 180) if is_current else (55, 55, 70)
            pygame.draw.rect(surface, bg, br, border_radius=6)
            pygame.draw.rect(surface, (100, 100, 130), br, 1, border_radius=6)
            t = self.small_font.render(name, True, (255, 255, 255))
            surface.blit(t, t.get_rect(center=br.center))
            self._lvl_rects[i] = br
            lvl_y += 46

    def draw_fullscreen(self, surface, sw, sh):
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        panel_w = 300
        btn_h   = 60
        margin  = 20
        buttons = ["Riprendi", "Editor", "Reset", "Quit"]
        colors  = {
            "Riprendi": (60, 160, 60),
            "Editor":   (60, 100, 180),
            "Reset":    (180, 140, 40),
            "Quit":     (180, 60, 60),
        }
        panel_h = len(buttons) * (btn_h + margin) + margin + 60
        px = (sw - panel_w) // 2
        py = (sh - panel_h) // 2

        pygame.draw.rect(surface, (40, 40, 55), (px, py, panel_w, panel_h), border_radius=16)
        pygame.draw.rect(surface, (80, 80, 110), (px, py, panel_w, panel_h), 2, border_radius=16)

        title = self.font.render("PAUSA", True, (220, 220, 255))
        surface.blit(title, title.get_rect(center=(sw // 2, py + 30)))

        self._fs_rects = {}
        for i, label in enumerate(buttons):
            bx = px + margin
            by = py + 60 + margin + i * (btn_h + margin)
            br = pygame.Rect(bx, by, panel_w - margin * 2, btn_h)
            pygame.draw.rect(surface, colors[label], br, border_radius=10)
            t = self.font.render(label, True, (255, 255, 255))
            surface.blit(t, t.get_rect(center=br.center))
            self._fs_rects[label] = br

    def handle_click(self, pos):
        if self.tab_rect.collidepoint(pos):
            return "toggle"
        for label, r in self._rects.items():
            if r.collidepoint(pos):
                return label
        for idx, r in self._lvl_rects.items():
            if r.collidepoint(pos):
                return f"level:{idx}"
        return None

    def handle_click_fullscreen(self, pos):
        for label, r in self._fs_rects.items():
            if r.collidepoint(pos):
                return label
        return None


# ── Game ─────────────────────────────────────────────────────────────────────

class Game:
    def __init__(self):
        pygame.init()
        info = pygame.display.Info()
        self.screen_w = info.current_w
        self.screen_h = info.current_h
        self.window = pygame.display.set_mode(
            (self.screen_w, self.screen_h), pygame.FULLSCREEN)
        pygame.display.set_caption("Grid Puzzle")
        self.clock      = pygame.time.Clock()
        self.font       = pygame.font.SysFont(None, 32)
        self.small_font = pygame.font.SysFont(None, 24)
        self.world      = World()
        self.canvas     = pygame.Surface((GAME_W, GAME_H))
        self.menu       = SideMenu(self.font, self.small_font)
        self.paused     = False
        self.running    = True

    def _scaled_canvas_rect(self):
        sw, sh = self.window.get_size()
        margin = 20
        available_w = sw - margin * 2
        available_h = sh - margin * 2
        aspect = GAME_W / GAME_H
        scaled_h = available_h
        scaled_w = int(scaled_h * aspect)
        if scaled_w > available_w:
            scaled_w = available_w
            scaled_h = int(scaled_w / aspect)
        x = (sw - scaled_w) // 2
        y = (sh - scaled_h) // 2
        return pygame.Rect(x, y, scaled_w, scaled_h)

    def _restart_pygame(self):
        pygame.quit()
        os.system(f"{sys.executable} {os.path.join(os.path.dirname(__file__), 'editor.py')}")
        pygame.init()
        info = pygame.display.Info()
        self.screen_w = info.current_w
        self.screen_h = info.current_h
        self.window = pygame.display.set_mode(
            (self.screen_w, self.screen_h), pygame.FULLSCREEN)
        self.font       = pygame.font.SysFont(None, 32)
        self.small_font = pygame.font.SysFont(None, 24)
        self.menu       = SideMenu(self.font, self.small_font)
        self.world.reload_levels()

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000
            sw, sh = self.window.get_size()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.paused = not self.paused
                        self.menu.open = False
                    if not self.paused:
                        if event.key == pygame.K_r:
                            self.world.restart()
                        if event.key == pygame.K_RETURN:
                            if self.world.state == "win":
                                self.world.next_level()
                            elif self.world.state == "gameover":
                                self.world.restart()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.paused:
                        action = self.menu.handle_click_fullscreen(event.pos)
                        if action == "Riprendi":
                            self.paused = False
                        elif action == "Editor":
                            self.paused = False
                            self._restart_pygame()
                        elif action == "Reset":
                            self.world.restart()
                            self.paused = False
                        elif action == "Quit":
                            self.running = False
                    else:
                        action = self.menu.handle_click(event.pos)
                        if action == "toggle":
                            self.menu.toggle()
                        elif action == "Editor":
                            self.menu.open = False
                            self._restart_pygame()
                        elif action == "Reset":
                            self.world.restart()
                            self.menu.open = False
                        elif action == "Quit":
                            self.running = False
                        elif action and action.startswith("level:"):
                            idx = int(action.split(":")[1])
                            self.world.level_idx = idx
                            self.world.restart()
                            self.menu.open = False

            if self.world.state == "playing" and not self.menu.open and not self.paused:
                self.world.handle_input()

            self.world.update(dt)

            # Disegno
            self.window.fill((20, 20, 28))
            canvas_rect = self._scaled_canvas_rect()
            self.canvas.fill((200, 200, 200))
            self.world.draw(self.canvas)
            scaled = pygame.transform.smoothscale(self.canvas, canvas_rect.size)
            pygame.draw.rect(self.window, (60, 60, 75), canvas_rect.inflate(6, 6), border_radius=18)
            self.window.blit(scaled, canvas_rect.topleft)

            self.menu.set_levels(self.world.levels, self.world.level_idx)
            self.menu.draw(self.window, 20, 20)

            if self.paused:
                self.menu.draw_fullscreen(self.window, sw, sh)

            pygame.display.update()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    import sys

    game = Game()

    # se il launcher passa un livello
    if len(sys.argv) > 1:
        game.world.level_idx = int(sys.argv[1])
        game.world.restart()

    game.run()