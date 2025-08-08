"""
Ping + clases Bot (base y derivadas).  Toda la lógica física y de IA vive aquí;
nada de render salvo indicar colores (que vienen de constants).
"""
import math, pygame, random
from pygame.math import Vector2
import constants as C
import utils as U
from gyroscope import GyroscopeSimulated

class Ping:
    """Representa un pulso ultrasónico y su eco de retorno."""

    __slots__ = ("origin","dir_det","target_d","hit_pt","target_src","out","echo","echo_dir")

    def __init__(self, origin, dir_det, target_d, hit_pt, src):
        """Inicializa el ping indicando origen, dirección y punto de impacto."""
        self.origin   = origin
        self.dir_det  = dir_det
        self.target_d = target_d
        self.hit_pt   = hit_pt
        self.target_src = src 
        self.out   = 0.0
        self.echo  = 0.0
        self.echo_dir = None

    def update(self, dt_ms):
        """Propaga el frente de onda y, si procede, su eco.

        Devuelve ``False`` cuando el ciclo del ping ha terminado.
        """
        step = C.WAVE_SPEED_PX_MS * dt_ms
        self.out += step
        if self.out >= self.target_d and self.echo_dir is None:
            sx, sy = self.origin; hx, hy = self.hit_pt
            self.echo_dir = math.atan2(sy-hy, sx-hx)
            self.echo = 0.0
        if self.echo_dir is not None:
            self.echo += step
            if self.echo >= self.target_d:
                return False
        if self.echo_dir is None and self.out > C.MAX_RANGE_PX:
            return False
        return True

class Bot:
    """Entidad base para todos los robots del simulador."""

    def __init__(self, pos, colour):
        """Crea un bot en ``pos`` y con color ``colour``."""
        self.pos         = Vector2(pos)
        self.heading_deg = 0.0
        self.colour      = colour
        self.vel         = Vector2()
        self.prev_vel    = Vector2()

        self.ping        = None 
        self.last_ping_ms= 0

        self.accel       = (0.0, 0.0)
        self.accel_time  = 0
        self.ang_vel     = 0.0
        self.prev_heading = 0.0

        self.gyroscope = GyroscopeSimulated()
        self.ir_intensity = 0.0
        self.ir_rho       = C.IR_RHO_BLACK
        self.ir_dist_cm   = 0.0
        self.ir_colour    = "negro"

    # ― física ―
    def integrate(self, dt_ms):
        """Integra la velocidad actual para actualizar la posición."""
        self.pos += self.vel * (dt_ms/1000.0)
        self.gyroscope.update(self.ang_vel, dt_ms)

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

    def record_accel(self, dt_ms):
        """Calcula la aceleración a partir de la variación de velocidad."""
        if dt_ms <= 0:
            self.prev_vel = self.vel; return
        dv = self.vel - self.prev_vel
        ax = (dv.x) / (dt_ms/1000.0)
        ay = (dv.y) / (dt_ms/1000.0)
        ax *= 0.0025; ay *= 0.0025
        self.accel = (ax, ay)
        self.accel_time = pygame.time.get_ticks()
        self.prev_vel = self.vel

    def record_ang_vel(self, dt_ms):
        """Calcula la velocidad angular a partir de la variación de orientación."""
        if dt_ms <= 0:
            self.prev_heading = self.heading_deg
            self.ang_vel = 0.0
            return
        dtheta = (self.heading_deg - self.prev_heading + 540) % 360 - 180
        self.ang_vel = dtheta / (dt_ms/1000.0)
        self.prev_heading = self.heading_deg

    # ― sensor infrarrojo ―
    def update_ir(self):
        """Actualiza la lectura del sensor IR según la posición actual."""
        if U.on_white_line((self.pos.x, self.pos.y)):
            self.ir_rho = C.IR_RHO_WHITE
            self.ir_colour = "blanco"
        elif U.on_blue_center((self.pos.x, self.pos.y)):
            self.ir_rho = C.IR_RHO_BLUE
            self.ir_colour = "azul"
        else:
            self.ir_rho = C.IR_RHO_BLACK
            self.ir_colour = "negro"
        self.ir_intensity = (C.IR_POWER * self.ir_rho) / (C.IR_SENSOR_HEIGHT_CM ** 2)

    # ― sonar ―

    def _compute_ping_hit(self, opponent, noisy=True):
        """Calcula la distancia del siguiente obstáculo en la dirección actual.

        Devuelve una tupla ``(medida, real, hit_pt, src)`` donde ``medida`` es la
        distancia perturbada aleatoriamente y ``real`` la distancia exacta.
        """
        dv = U.unit_vec(self.heading_deg)
        d_ring = U.ray_circle((self.pos.x, self.pos.y), dv)
        d_bot  = None
        if opponent is not None:
            d_bot = U.ray_disc((self.pos.x, self.pos.y), dv,
                               (opponent.pos.x, opponent.pos.y), C.BOT_RADIUS)
        if d_bot is not None and d_bot < d_ring and d_bot <= C.MAX_RANGE_PX:
            real = d_bot
            hit_pt = (self.pos.x + dv[0]*real,
                      self.pos.y + dv[1]*real)
            src = "bot"
        else:
            real = min(d_ring, C.MAX_RANGE_PX)
            hit_pt = (self.pos.x + dv[0]*real,
                      self.pos.y + dv[1]*real)
            src = "ring"
        if noisy:
            noise = random.uniform(-C.PING_NOISE_PX, C.PING_NOISE_PX)
            measured = max(0.0, real + noise)
        else:
            measured = real
        return measured, real, hit_pt, src

    def launch_ping(self, now_ms, opponent=None):
        """Lanza un nuevo ping si ha pasado el tiempo de recarga."""
        if self.ping is None and now_ms - self.last_ping_ms >= C.PING_PERIOD_MS:
            _, dist, hit_pt, src = self._compute_ping_hit(opponent, noisy=False)
            self.ping = Ping((self.pos.x, self.pos.y),
                             math.radians(self.heading_deg),
                             dist, hit_pt, src)
            self.last_ping_ms = now_ms

    def update_ping(self, dt_ms):
        """Actualiza el ping activo y lo elimina al finalizar."""
        if self.ping and not self.ping.update(dt_ms):
            self.ping = None
    
    def detectar_Empuje(self, umbral_giro = 40.0):
        vel_vang = self.gyroscope.read_angular_velocity()
        if abs(vel_vang) > umbral_giro and self.ang_vel == 0:
            print(f"[{self.colour}] Empujón Detectado, velocidad angular: {vel_vang:.2f}°/s")
            return True
        return False
    
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
        self.record_ang_vel(dt_ms)
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
        self.record_ang_vel(dt_ms)
        if self.vel.length() > C.MAX_SPEED:
            self.vel.scale_to_length(C.MAX_SPEED)
        self.apply_damping(dt_ms); self.integrate(dt_ms); self.record_accel(dt_ms)

class CpuBot(Bot):
    """Bot controlado por IA menos preciso que barre con ultrasonidos."""

    def __init__(self, pos, colour):
        super().__init__(pos, colour)
        self.state = "scan"
        self.scan_rot = 0.0
        self.move_time = 0

    def update(self, target_bot, dt_ms):
        """IA basada en estados: escaneo, movimiento y persecución."""
        now_ms = pygame.time.get_ticks()

        if self.state == "scan":
            # gira sobre su eje lanzando pings y sin desplazarse
            turn = C.CPU_TURN * (dt_ms / 16.6667)
            self.heading_deg = (self.heading_deg + turn) % 360
            self.record_ang_vel(dt_ms)
            self.vel.xy = (0.0, 0.0)
            self.launch_ping(now_ms, target_bot)
            self.update_ping(dt_ms)

            # detección básica dentro del campo de visión del sonar
            dx = target_bot.pos.x - self.pos.x
            dy = target_bot.pos.y - self.pos.y
            dist = math.hypot(dx, dy)
            if dist <= C.MAX_RANGE_PX:
                ang_to = math.degrees(math.atan2(dy, dx)) % 360
                diff = (ang_to - self.heading_deg + 540) % 360 - 180
                if abs(diff) <= C.FOV_DEG / 2:
                    self.state = "pursue"
                    self.heading_deg = ang_to
                    self.scan_rot = 0
                    self.record_accel(dt_ms)
                    return

            self.scan_rot += abs(turn)
            self.record_accel(dt_ms)
            if self.scan_rot >= 360:
                self.state = "move"
                self.move_time = 0
                self.scan_rot = 0
                self.heading_deg = random.uniform(0, 360)

        elif self.state == "move":
            # avanza recto durante un breve periodo antes de volver a escanear
            vx, vy = U.unit_vec(self.heading_deg)
            self.vel = Vector2(vx*C.CPU_SPEED, vy*C.CPU_SPEED)
            if self.vel.length() > C.MAX_SPEED:
                self.vel.scale_to_length(C.MAX_SPEED)
            self.apply_damping(dt_ms); self.integrate(dt_ms)
            self.record_accel(dt_ms); self.record_ang_vel(dt_ms)
            self.move_time += dt_ms
            if self.move_time >= 1000:
                self.state = "scan"
                self.vel.xy = (0.0, 0.0)

        elif self.state == "pursue":
            # se desplaza hacia delante con rumbo fijo
            vx, vy = U.unit_vec(self.heading_deg)
            self.vel = Vector2(vx*C.CPU_SPEED, vy*C.CPU_SPEED)
            if self.vel.length() > C.MAX_SPEED:
                self.vel.scale_to_length(C.MAX_SPEED)
            self.apply_damping(dt_ms); self.integrate(dt_ms)
            self.record_accel(dt_ms); self.record_ang_vel(dt_ms)
            self.launch_ping(now_ms, target_bot)
            self.update_ping(dt_ms)

            dx = target_bot.pos.x - self.pos.x
            dy = target_bot.pos.y - self.pos.y
            dist = math.hypot(dx, dy)
            ang_to = math.degrees(math.atan2(dy, dx)) % 360
            diff = (ang_to - self.heading_deg + 540) % 360 - 180
            if dist > C.MAX_RANGE_PX or abs(diff) > C.FOV_DEG / 2:
                self.state = "scan"
                self.vel.xy = (0.0, 0.0)

        if self.detectar_Empuje():
            print("[CPUBot] Empujón Detectado, reposicionado...")
            self.heading_deg = (self.heading_deg + 90) % 360
