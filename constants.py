"""
Constantes y parámetros globales del simulador Sumo-Sensors.
Se mantienen aquí para que todo el proyecto comparta la misma “fuente de verdad”.
"""
import math

# ── Escala real/virtual ──────────────────────────────────────────
PX_PER_CM      = 4                       # 1 cm → 4 px

# ── Geometría pantalla / dojo ────────────────────────────────────
SCREEN_W, SCREEN_H = 900, 700
CENTER = (SCREEN_W // 2, SCREEN_H // 2)
DOJO_RADIUS = int(40 * PX_PER_CM)        # 80 cm de diámetro → 40 cm de radio
RING_EDGE   = int(5 * PX_PER_CM)         # grosor borde blanco (5 cm)
CENTER_MARK_RADIUS = int(5 * PX_PER_CM)  # radio del círculo azul central (5 cm)
BOT_RADIUS  = 18                 # px

# ── Escala de sonido ─────────────────────────────────────────────
V_SOUND_CMMS   = 34.3                    # velocidad sonido (cm ms-1)
WAVE_SPEED_PX_MS = (V_SOUND_CMMS / 100) * PX_PER_CM   # ≃ 1.37 px ms-1

# ── Movimiento ──────────────────────────────────────────────────
TURN_DEG            = 4          # giro jugador (° frame-1)
MOVE_ACC            = 950.0       # aceleración jugador (px s-2)
CPU_TURN            = 4          # giro máximo CPU (° frame-1)
MAX_SPEED           = 260.0
CPU_SPEED           = 150.0      # velocidad objetivo CPU (px s-1)
DAMPING_PER_FRAME   = 0.93       # amortiguación (~10 % a 60 FPS)
TIME_SCALE          = 0.5        # escala global del tiempo (<1 más lento)

# ── Sensor ultrasónico ──────────────────────────────────────────
FOV_DEG        = 24
CREST_GAP_PX   = 35
PING_PERIOD_MS = 700
MAX_RANGE_PX   = DOJO_RADIUS + 40
PING_NOISE_PX  = 0               # amplitud del ruido (px)
# Rango ajustable para interfaces o menús externos
PING_NOISE_RANGE = (0, 40)

# ── Acelerómetro ────────────────────────────────────────────────
ACCEL_DISPLAY_MS = 600
G_MSS = 9.81

# ── Sensor infrarrojo ────────────────────────────────────────────
IR_POWER     = 1000.0             # potencia emitida (unidad arb.)
IR_RHO_WHITE = 0.9                # reflectividad (blanco)
IR_RHO_BLACK = 0.2                # reflectividad (negro)
IR_RHO_BLUE  = 0.5                # reflectividad (azul)
IR_SENSOR_HEIGHT_CM = 2.0         # altura fija del sensor sobre el suelo


# ── Colores (RGB) ───────────────────────────────────────────────
BG_C         = (  0,   0,   0)
RING_FILL    = BG_C
RING_EDGE_C  = (255, 255, 255)
CENTER_MARK_C= (  0,   0, 255)

PLAYER_C = ( 80, 160, 255)
CPU_C    = (255,  60, 180)
P2_C     = (110, 210, 120)

PING_C   = ( 60, 230, 110)
ECHO_C   = (240, 120,  60)
IMPACT_C = (255,  90,  90)
ACCEL_VEC_C = (255, 210,   0)
TXT_C    = (  0,   0,   0)

TAU = math.tau          # 2π, útil para cálculos angulares

