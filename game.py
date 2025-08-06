"""
Bucle principal, render y gestión de estado.  Importa los módulos lógicos
pero deja la inicialización de Pygame y el loop de eventos aquí.
"""
import sys, pygame
import constants as C
import utils as U
import bots as B
import math
from recorder import Recorder

pygame.init()
FONT  = pygame.font.SysFont(None, 28)
SMALL = pygame.font.SysFont(None, 20)

class SumoSensorsGame:
    def __init__(self):
        self.scr   = pygame.display.set_mode((C.SCREEN_W, C.SCREEN_H))
        pygame.display.set_caption("Sumo-Sensors (modular)")
        self.clock = pygame.time.Clock()
        self.two_players = False
        self.replay_mode = False
        self.rec   = Recorder()
        self.reset()

    # ── ciclos de vida ───────────────────────────────────────────
    def reset(self):
        self.player = B.PlayerBot((C.CENTER[0]-120, C.CENTER[1]), C.PLAYER_C)
        self.player.heading_deg = 0
        self.opponent = (B.Player2Bot if self.two_players else B.CpuBot)(
            (C.CENTER[0]+120, C.CENTER[1]),
            C.P2_C if self.two_players else C.CPU_C)
        self.opponent.heading_deg = 180
        self.game_over = False
        self.winner    = ""
        self.replay_mode = False
        self.replay_idx  = 0
        self.rec.frames.clear()

    def toggle_two_players(self): self.two_players = not self.two_players; self.reset()
    def start_replay(self): self.replay_mode = bool(self.rec.frames); self.replay_idx = 0

    # ── helpers de dibujo ────────────────────────────────────────
    def _ring(self):
        pygame.draw.circle(self.scr, C.RING_FILL, C.CENTER, C.DOJO_RADIUS)
        pygame.draw.circle(self.scr, C.RING_EDGE_C, C.CENTER, C.DOJO_RADIUS, C.RING_EDGE)

    def _draw_bot(self, bot):
        pygame.draw.circle(self.scr, bot.colour,
                           (int(bot.pos.x), int(bot.pos.y)), C.BOT_RADIUS)
        vx, vy = U.unit_vec(bot.heading_deg)
        tip = (bot.pos.x + vx*C.BOT_RADIUS, bot.pos.y + vy*C.BOT_RADIUS)
        pygame.draw.line(self.scr, (255,255,255), bot.pos, tip, 2)

    # ping fans (idénticos a versión monolítica) → reutilizamos los de bots.py
    def _draw_pings(self, bot):
        if not bot.ping: return
        fan = pygame.Surface((C.SCREEN_W, C.SCREEN_H), pygame.SRCALPHA)
        self._draw_fan(fan, bot.ping.origin, bot.ping.dir_det, bot.ping.out, C.PING_C)
        if bot.ping.echo_dir is not None:
            col = C.ECHO_C if bot.ping.target_src=="ring" else C.IMPACT_C
            self._draw_fan(fan, bot.ping.hit_pt, bot.ping.echo_dir, bot.ping.echo, col)
        self.scr.blit(fan, (0,0))

    def _draw_fan(self, surf, centre, det_angle, prog, colour):
        arc = (-det_angle) % C.TAU
        half = math.radians(C.FOV_DEG/2)
        kmax = int(prog//C.CREST_GAP_PX) + 2
        for k in range(kmax):
            r = prog - k*C.CREST_GAP_PX
            if r <= 0: continue
            alpha = max(0, 210 - k*32)
            pygame.draw.arc(surf, (*colour,alpha),
                            pygame.Rect(centre[0]-r, centre[1]-r, r*2, r*2),
                            arc-half, arc+half, 2)

    # ── draw modos ───────────────────────────────────────────────
    def draw_game(self, now):
        self.scr.fill(C.GREY_BG); self._ring()
        for b in (self.player, self.opponent):
            self._draw_bot(b); self._draw_pings(b)

        # Acelerómetros & HUD (igual que antes, omito por brevedad)
        # ...

        help1 = "ESC salir  |  R reiniciar  |  TAB CPU/2P  |  T replay  |  C CSV"
        self.scr.blit(SMALL.render(help1, True, C.TXT_C), (10, C.SCREEN_H-40))

        if self.game_over:
            msg = FONT.render(f"¡GANA {self.winner}! (R para reiniciar)",
                              True, C.IMPACT_C)
            self.scr.blit(msg, (C.SCREEN_W//2 - msg.get_width()//2, 30))
        pygame.display.flip()

    def draw_replay(self):
        self.scr.fill((245,245,245)); self._ring()
        fr = self.rec.frames[self.replay_idx]
        p1 = (fr["p1x"], fr["p1y"]); p2 = (fr["p2x"], fr["p2y"])
        pygame.draw.circle(self.scr, C.PLAYER_C, p1, C.BOT_RADIUS)
        pygame.draw.circle(self.scr,
                           C.P2_C if self.two_players else C.CPU_C,
                           p2, C.BOT_RADIUS)
        # barra de tiempo + etiqueta
        # ...
        pygame.display.flip()

    # ── bucle principal ──────────────────────────────────────────
    def run(self):
        running = True
        while running:
            dt   = self.clock.tick(60) * C.TIME_SCALE
            now  = pygame.time.get_ticks()
            for e in pygame.event.get():
                if e.type == pygame.QUIT or \
                   (e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE):
                    running=False
                if e.type==pygame.KEYDOWN:
                    if e.key==pygame.K_r:   self.reset()
                    if e.key==pygame.K_TAB: self.toggle_two_players()
                    if e.key==pygame.K_t:   self.start_replay() if not self.replay_mode else setattr(self,"replay_mode",False)
                    if e.key==pygame.K_c:   print("CSV guardado" if self.rec.export_csv() else "Nada que exportar")

            if not self.replay_mode:
                if not self.game_over:
                    keys = pygame.key.get_pressed()
                    self.player.update(keys, dt)
                    if isinstance(self.opponent, B.CpuBot):
                        self.opponent.update(self.player, dt)
                    else:
                        self.opponent.update(keys, dt)
                    self.player.push_apart(self.opponent)

                    # sonar
                    self.player.launch_ping(now, self.opponent)
                    self.opponent.launch_ping(now, self.player)
                    self.player.update_ping(dt); self.opponent.update_ping(dt)

                    # KO
                    if not U.within_ring_with_radius(self.player.pos):
                        self.winner = "CPU" if not self.two_players else "JUGADOR 2"
                    if not U.within_ring_with_radius(self.opponent.pos):
                        self.winner = "JUGADOR" if not self.two_players else "JUGADOR 1"
                    if self.winner: self.game_over=True

                    self.rec.add(now, self.player, self.opponent)
                self.draw_game(now)
            else:
                self.draw_replay()
                self.replay_idx += 1
                if self.replay_idx >= len(self.rec.frames): self.replay_mode=False

        pygame.quit(); sys.exit()