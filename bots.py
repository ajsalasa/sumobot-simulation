"""
Ping + clases Bot (base y derivadas).  Toda la lógica física y de IA vive aquí;
nada de render salvo indicar colores (que vienen de constants).
"""
import math, pygame
from pygame.math import Vector2
import constants as C
import utils as U

# ── Ping ultrasónico ────────────────────────────────────────────
class Ping:
    """Representa un pulso ultrasónico y su eco de retorno."""

    __slots__ = ("origin","dir_det","target_d","hit_pt","target_src","out","echo","echo_dir")

    def __init__(self, origin, dir_det, target_d, hit_pt, src):
        """Inicializa el ping indicando origen, dirección y punto de impacto."""
        self.origin   = origin                  # (x,y)
        self.dir_det  = dir_det                 # radianes de emisión
        self.target_d = target_d                # distancia al impacto (px)
        self.hit_pt   = hit_pt                  # punto (x,y) de impacto
        self.target_src = src                   # "ring" | "bot"
        self.out   = 0.0
        self.echo  = 0.0
        self.echo_dir = None                    # dirección del eco (rad)

    def update(self, dt_ms):
        """Propaga el frente de onda y, si procede, su eco.

        Devuelve ``False`` cuando el ciclo del ping ha terminado.
        """
        step = C.WAVE_SPEED_PX_MS * dt_ms
        self.out += step
        # Iniciar eco
        if self.out >= self.target_d and self.echo_dir is None:
            sx, sy = self.origin; hx, hy = self.hit_pt
            self.echo_dir = math.atan2(sy-hy, sx-hx)
            self.echo = 0.0
        # Propagar eco
        if self.echo_dir is not None:
            self.echo += step
            if self.echo >= self.target_d:
                return False                    # ciclo completo
        # Optimización: ping sin eco y lejísimos
        if self.echo_dir is None and self.out > C.MAX_RANGE_PX:
            return False
        return True

# ── Bot base ────────────────────────────────────────────────────
class Bot:
    """Entidad base para todos los robots del simulador."""

    def __init__(self, pos, colour):
        """Crea un bot en ``pos`` y con color ``colour``."""
        self.pos         = Vector2(pos)
        self.heading_deg = 0.0
        self.base_colour = colour
        self.colour      = colour
        self.vel         = Vector2()
        self.prev_vel    = Vector2()

        self.ping        = None     # Ping activo
        self.last_ping_ms= 0

        self.accel       = (0.0, 0.0)
        self.accel_time  = 0
        self.alert       = False

    # ― física ―
    def integrate(self, dt_ms):
        """Integra la velocidad actual para actualizar la posición."""
        self.pos += self.vel * (dt_ms/1000.0)

    def apply_damping(self, dt_ms):
        """Aplica amortiguación proporcional al tiempo transcurrido."""
        self.vel *= U.damping_factor(dt_ms)

    def push_apart(self, other):
        """Separa este bot de ``other`` si se solapan."""
        d = self.pos.distance_to(other.pos)
        if d and d < C.BOT_RADIUS*2:
            overlap = C.BOT_RADIUS*2 - d
            n = (other.pos - self.pos).normalize()
            self.pos  -= n * overlap/2
            other.pos += n * overlap/2

    # ― acelerómetro ―
    def record_accel(self, dt_ms):
        """Calcula la aceleración a partir de la variación de velocidad."""
        if dt_ms <= 0:
            self.prev_vel = self.vel; return
        dv = self.vel - self.prev_vel
        ax = (dv.x) / (dt_ms/1000.0)
        ay = (dv.y) / (dt_ms/1000.0)
        ax *= 0.0025; ay *= 0.0025          # px→m
        self.accel = (ax, ay)
        self.accel_time = pygame.time.get_ticks()
        self.prev_vel = self.vel

    # ― sensor de línea ―
    def edge_distance(self):
        """Distancia en píxeles desde el bot hasta el borde del dojo."""
        return C.DOJO_RADIUS - U.dist_to_center(self.pos)

    # ― sonar ―
    def _compute_ping_hit(self, opponent):
        """Calcula la distancia del siguiente obstáculo en la dirección actual."""
        dv = U.unit_vec(self.heading_deg)
        d_ring = U.ray_circle((self.pos.x, self.pos.y), dv)
        d_bot  = None
        if opponent is not None:
            d_bot = U.ray_disc((self.pos.x, self.pos.y), dv,
                               (opponent.pos.x, opponent.pos.y), C.BOT_RADIUS)
        if d_bot is not None and d_bot < d_ring and d_bot <= C.MAX_RANGE_PX:
            hit_pt = (self.pos.x + dv[0]*d_bot,
                      self.pos.y + dv[1]*d_bot)
            return d_bot, hit_pt, "bot"
        dist = min(d_ring, C.MAX_RANGE_PX)
        hit_pt = (self.pos.x + dv[0]*dist,
                  self.pos.y + dv[1]*dist)
        return dist, hit_pt, "ring"

    def launch_ping(self, now_ms, opponent=None):
        """Lanza un nuevo ping si ha pasado el tiempo de recarga."""
        if self.ping is None and now_ms - self.last_ping_ms >= C.PING_PERIOD_MS:
            dist, hit_pt, src = self._compute_ping_hit(opponent)
            self.ping = Ping((self.pos.x, self.pos.y),
                             math.radians(self.heading_deg),
                             dist, hit_pt, src)
            self.last_ping_ms = now_ms

    def update_ping(self, dt_ms):
        """Actualiza el ping activo y lo elimina al finalizar."""
        if self.ping and not self.ping.update(dt_ms):
            self.ping = None

# ── Derivadas “jugables” ────────────────────────────────────────
class PlayerBot(Bot):
    """Bot controlado por el jugador con cursores."""

    def update(self, keys, dt_ms):
        """Procesa la entrada del usuario y actualiza el estado del bot."""
        ax = ay = 0.0
        if keys[pygame.K_LEFT]:  ax -= C.MOVE_ACC
        if keys[pygame.K_RIGHT]: ax += C.MOVE_ACC
        if keys[pygame.K_UP]:    ay -= C.MOVE_ACC
        if keys[pygame.K_DOWN]:  ay += C.MOVE_ACC
        self.vel.x += ax * (dt_ms/1000.0)
        self.vel.y += ay * (dt_ms/1000.0)
        if self.vel.length_squared() > 0:
            self.heading_deg = math.degrees(math.atan2(self.vel.y, self.vel.x)) % 360
        # Limitar la velocidad para que no crezca sin control
        if self.vel.length() > C.MAX_SPEED:
            self.vel.scale_to_length(C.MAX_SPEED)
        self.apply_damping(dt_ms); self.integrate(dt_ms); self.record_accel(dt_ms)


class Player2Bot(Bot):
    """Bot controlado por un segundo jugador con las teclas IJKL."""

    def update(self, keys, dt_ms):
        """Procesa la entrada del segundo jugador y actualiza el bot."""
        ax = ay = 0.0
        if keys[pygame.K_j]: ax -= C.MOVE_ACC
        if keys[pygame.K_l]: ax += C.MOVE_ACC
        if keys[pygame.K_i]: ay -= C.MOVE_ACC
        if keys[pygame.K_k]: ay += C.MOVE_ACC
        self.vel.x += ax * (dt_ms/1000.0)
        self.vel.y += ay * (dt_ms/1000.0)
        if self.vel.length_squared() > 0:
            self.heading_deg = math.degrees(math.atan2(self.vel.y, self.vel.x)) % 360
        # Limitar la velocidad para que no crezca sin control
        if self.vel.length() > C.MAX_SPEED:
            self.vel.scale_to_length(C.MAX_SPEED)
        self.apply_damping(dt_ms); self.integrate(dt_ms); self.record_accel(dt_ms)

class CpuBot(Bot):
    """Bot controlado por IA que busca al oponente mediante un radar FOV."""

    def _scan_angle(self, target_pos):
        """Barre varios ángulos y devuelve el más cercano al objetivo."""
        N, half = 7, C.FOV_DEG/2
        best_d = best_deg = None
        for i in range(N):
            rel = -half + i * (C.FOV_DEG/(N-1))
            deg = (self.heading_deg + rel) % 360
            dv  = U.unit_vec(deg)
            d   = U.ray_disc((self.pos.x, self.pos.y), dv, target_pos, C.BOT_RADIUS)
            if d is not None and d <= C.MAX_RANGE_PX:
                if best_d is None or d < best_d:
                    best_d, best_deg = d, deg
        return best_deg

    def update(self, target_bot, dt_ms):
        """Actualiza la IA orientándola hacia ``target_bot``."""
        # 1) sonar FOV
        scan = self._scan_angle((target_bot.pos.x, target_bot.pos.y))
        target_deg = scan if scan is not None else \
            math.degrees(math.atan2(target_bot.pos.y - self.pos.y,
                                    target_bot.pos.x - self.pos.x)) % 360

        # limitar velocidad angular
        diff = (target_deg - self.heading_deg + 540) % 360 - 180
        if abs(diff) > C.CPU_TURN:
            self.heading_deg = (self.heading_deg +
                                C.CPU_TURN*(1 if diff>0 else -1)) % 360
        else:
            self.heading_deg = target_deg

        # velocidad deseada
        vx, vy = U.unit_vec(self.heading_deg)
        desired = Vector2(vx*C.CPU_SPEED, vy*C.CPU_SPEED)
        self.vel = self.vel.lerp(desired, 0.25)
        # Limitar la velocidad para que no crezca sin control
        if self.vel.length() > C.MAX_SPEED:
            self.vel.scale_to_length(C.MAX_SPEED)
        self.apply_damping(dt_ms); self.integrate(dt_ms); self.record_accel(dt_ms)
