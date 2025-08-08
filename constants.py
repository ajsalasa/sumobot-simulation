"""
Constantes y parámetros globales del simulador Sumo-Sensors.
Se mantienen aquí para que todo el proyecto comparta la misma “fuente de verdad”.
"""
import math

SCREEN_W, SCREEN_H = 900, 700
CENTER = (SCREEN_W // 2, SCREEN_H // 2)
DOJO_RADIUS = 280
RING_EDGE   = 6
BOT_RADIUS  = 18


PX_PER_CM      = 4
V_SOUND_CMMS   = 34.3
WAVE_SPEED_PX_MS = (V_SOUND_CMMS / 100) * PX_PER_CM


TURN_DEG            = 4
MOVE_ACC            = 950.0
CPU_TURN            = 4
MAX_SPEED           = 260.0
CPU_SPEED           = 150.0
DAMPING_PER_FRAME   = 0.93
TIME_SCALE          = 0.5


FOV_DEG        = 24
CREST_GAP_PX   = 35
PING_PERIOD_MS = 700
MAX_RANGE_PX   = DOJO_RADIUS + 40
PING_NOISE_PX  = 0
PING_NOISE_RANGE = (0, 40)


ACCEL_DISPLAY_MS = 600
G_MSS = 9.81


GREY_BG   = (225, 225, 225)
RING_FILL = ( 20,  20,  20)
RING_EDGE_C = (255, 255, 255)

PLAYER_C = ( 80, 160, 255)
CPU_C    = (255,  60, 180)
P2_C     = (110, 210, 120)

PING_C   = ( 60, 230, 110)
ECHO_C   = (240, 120,  60)
IMPACT_C = (255,  90,  90)
ACCEL_VEC_C = (255, 210,   0)
TXT_C    = (  0,   0,   0)

TAU = math.tau