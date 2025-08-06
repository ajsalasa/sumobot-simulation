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
    """Encapsula el estado y la lógica principal del simulador."""

    def __init__(self):
        """Inicializa Pygame y crea los bots y recursos iniciales."""
        self.scr   = pygame.display.set_mode((C.SCREEN_W, C.SCREEN_H))
        pygame.display.set_caption("Sumo-Sensors (modular)")
        self.clock = pygame.time.Clock()
        self.two_players = False
        self.replay_mode = False
        self.rec   = Recorder()
        self.reset()

    # ── ciclos de vida ───────────────────────────────────────────
    def reset(self):
        """Reinicia la partida creando bots nuevos y limpiando estados."""
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

    def toggle_two_players(self):
        """Activa o desactiva el modo de dos jugadores."""
        self.two_players = not self.two_players
        self.reset()

    def start_replay(self):
        """Inicia el modo de repetición si hay datos grabados."""
        self.replay_mode = bool(self.rec.frames)
        self.replay_idx = 0

    # ── helpers de dibujo ────────────────────────────────────────
    def _ring(self):
        """Dibuja el dojo circular con su borde blanco."""
        pygame.draw.circle(self.scr, C.RING_FILL, C.CENTER, C.DOJO_RADIUS)
        pygame.draw.circle(self.scr, C.RING_EDGE_C, C.CENTER, C.DOJO_RADIUS, C.RING_EDGE)

    def _draw_bot(self, bot):
        """Renderiza un bot y una línea indicando su orientación."""
        pygame.draw.circle(self.scr, bot.colour,
                           (int(bot.pos.x), int(bot.pos.y)), C.BOT_RADIUS)
        vx, vy = U.unit_vec(bot.heading_deg)
        tip = (bot.pos.x + vx*C.BOT_RADIUS, bot.pos.y + vy*C.BOT_RADIUS)
        pygame.draw.line(self.scr, (255,255,255), bot.pos, tip, 2)

    # ping fans (idénticos a versión monolítica) → reutilizamos los de bots.py
    def _draw_pings(self, bot):
        """Dibuja el frente de onda del ping y su eco."""
        if not bot.ping:
            return
        fan = pygame.Surface((C.SCREEN_W, C.SCREEN_H), pygame.SRCALPHA)
        self._draw_fan(fan, bot.ping.origin, bot.ping.dir_det, bot.ping.out, C.PING_C)
        if bot.ping.echo_dir is not None:
            col = C.ECHO_C if bot.ping.target_src=="ring" else C.IMPACT_C
            self._draw_fan(fan, bot.ping.hit_pt, bot.ping.echo_dir, bot.ping.echo, col)
        self.scr.blit(fan, (0,0))

    def _draw_fan(self, surf, centre, det_angle, prog, colour):
        """Dibuja arcos concéntricos representando la propagación de una onda."""
        arc = (-det_angle) % C.TAU
        half = math.radians(C.FOV_DEG/2)
        kmax = int(prog//C.CREST_GAP_PX) + 2
        for k in range(kmax):
            r = prog - k*C.CREST_GAP_PX
            if r <= 0:
                continue
            alpha = max(0, 210 - k*32)
            pygame.draw.arc(surf, (*colour,alpha),
                            pygame.Rect(centre[0]-r, centre[1]-r, r*2, r*2),
                            arc-half, arc+half, 2)

    def _draw_hud(self, bot, opponent, align_left=True):
        """Renderiza fórmulas e información de sensores para un bot."""
        dist_px, _, _ = bot._compute_ping_hit(opponent)
        dist_cm = dist_px / C.PX_PER_CM
        tof_ms  = (2 * dist_cm) / C.V_SOUND_CMMS
        ax, ay  = bot.accel
        amag    = math.hypot(ax, ay)
        edge_d  = bot.edge_distance()

        lines = [
            "Sensor de línea:",
            "d = R - r",
            f"d = {edge_d:6.1f} px",
            "",
            "Ultrasonido:",
            "d = (v · t) / 2",
            f"v = {C.V_SOUND_CMMS/100:.0f} m/s",
            f"t = {tof_ms:6.2f} ms",
            f"d = {dist_cm:6.1f} cm",
            "",
            "Acelerómetro:",
            "a = Δv / Δt",
            f"ax = {ax:6.2f} m/s²",
            f"ay = {ay:6.2f} m/s²",
            f"|a| = {amag:6.2f} m/s²",
            f"|a| = {amag/C.G_MSS:5.2f} g",
        ]

        for i, line in enumerate(lines):
            txt = SMALL.render(line, True, C.TXT_C)
            if align_left:
                pos = (10, 10 + i*18)
            else:
                pos = (C.SCREEN_W - 10 - txt.get_width(), 10 + i*18)
            self.scr.blit(txt, pos)

    # ── draw modos ───────────────────────────────────────────────
    def draw_game(self, now):
        """Renderiza el estado del juego durante una partida normal."""
        self.scr.fill(C.GREY_BG)
        self._ring()
        for b in (self.player, self.opponent):
            self._draw_bot(b)
            self._draw_pings(b)

        # HUD de sensores para ambos bots
        self._draw_hud(self.player, self.opponent, align_left=True)
        self._draw_hud(self.opponent, self.player, align_left=False)

        help1 = "ESC salir  |  R reiniciar  |  TAB CPU/2P  |  T replay  |  C CSV"
        self.scr.blit(SMALL.render(help1, True, C.TXT_C), (10, C.SCREEN_H-40))

        if self.game_over:
            msg = FONT.render(f"¡GANA {self.winner}! (R para reiniciar)",
                              True, C.IMPACT_C)
            self.scr.blit(msg, (C.SCREEN_W//2 - msg.get_width()//2, 30))
        pygame.display.flip()

    def draw_replay(self):
        """Dibuja el modo de repetición de una partida grabada."""
        self.scr.fill((245,245,245))
        self._ring()
        fr = self.rec.frames[self.replay_idx]
        p1 = (fr["p1x"], fr["p1y"])
        p2 = (fr["p2x"], fr["p2y"])
        pygame.draw.circle(self.scr, C.PLAYER_C, p1, C.BOT_RADIUS)
        pygame.draw.circle(self.scr,
                           C.P2_C if self.two_players else C.CPU_C,
                           p2, C.BOT_RADIUS)
        # barra de tiempo + etiqueta
        total = len(self.rec.frames)
        if total:
            prog = self.replay_idx / (total - 1) if total > 1 else 0
            bar_x, bar_y = 20, C.SCREEN_H - 25
            bar_w = C.SCREEN_W - bar_x*2
            pygame.draw.rect(self.scr, C.TXT_C, (bar_x, bar_y, bar_w, 10), 1)
            pygame.draw.rect(self.scr, C.IMPACT_C,
                             (bar_x, bar_y, int(bar_w*prog), 10))
            t0 = self.rec.frames[0]["t"]
            t_sec = (fr["t"] - t0) / 1000
            label = SMALL.render(f"{t_sec:6.2f} s", True, C.TXT_C)
            self.scr.blit(label,
                          (C.SCREEN_W//2 - label.get_width()//2, bar_y - 20))
        pygame.display.flip()

    # ── bucle principal ──────────────────────────────────────────
    def run(self):
        """Bucle principal de la aplicación."""
        running = True
        while running:
            dt   = self.clock.tick(60) * C.TIME_SCALE
            now  = pygame.time.get_ticks()
            for e in pygame.event.get():
                if e.type == pygame.QUIT or \
                   (e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE):
                    running=False
                if e.type==pygame.KEYDOWN:
                    if e.key==pygame.K_r:
                        self.reset()
                    if e.key==pygame.K_TAB:
                        self.toggle_two_players()
                    if e.key==pygame.K_t:
                        self.start_replay() if not self.replay_mode else setattr(self,"replay_mode",False)
                    if e.key==pygame.K_c:
                        print("CSV guardado" if self.rec.export_csv() else "Nada que exportar")

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
                    self.player.update_ping(dt)
                    self.opponent.update_ping(dt)

                    # sensor de línea
                    for b in (self.player, self.opponent):
                        b.alert = b.edge_distance() < C.BOT_RADIUS*2
                        b.colour = C.IMPACT_C if b.alert else b.base_colour

                    # KO
                    if not U.within_ring_with_radius(self.player.pos):
                        self.winner = "CPU" if not self.two_players else "JUGADOR 2"
                    if not U.within_ring_with_radius(self.opponent.pos):
                        self.winner = "JUGADOR" if not self.two_players else "JUGADOR 1"
                    if self.winner:
                        self.game_over=True

                    self.rec.add(now, self.player, self.opponent)
                self.draw_game(now)
            else:
                self.draw_replay()
                self.replay_idx += 1
                if self.replay_idx >= len(self.rec.frames):
                    self.replay_mode=False

        pygame.quit()
        sys.exit()
