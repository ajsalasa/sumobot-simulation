"""
Funciones geométricas y de ayuda (sin dependencias de Pygame salvo Vector2).
"""
import math
from pygame.math import Vector2
import constants as C

def unit_vec(deg: float):
    """Devuelve un vector unitario a partir de un ángulo en grados."""
    rad = math.radians(deg)
    return math.cos(rad), math.sin(rad)

def dist_to_center(pos):
    """Distancia euclidiana desde ``pos`` al centro del dojo."""
    dx, dy = pos[0] - C.CENTER[0], pos[1] - C.CENTER[1]
    return math.hypot(dx, dy)

def within_ring_with_radius(pos):
    """¿El centro del bot (con radio) sigue dentro del dojo?"""
    return dist_to_center(pos) <= (C.DOJO_RADIUS - C.BOT_RADIUS)


def on_white_line(pos):
    """¿El sensor infrarrojo detecta la línea blanca del borde?"""
    d = dist_to_center(pos)
    half = C.RING_EDGE / 2
    return (C.DOJO_RADIUS - half) <= d <= (C.DOJO_RADIUS + half)

def on_blue_center(pos):
    """¿El sensor está sobre el círculo azul central?"""
    return dist_to_center(pos) <= C.CENTER_MARK_RADIUS

# ── Amortiguación dependiente de dt ────────────────────────────

def damping_factor(dt_ms: float):
    """Factor de amortiguación para un intervalo ``dt_ms``."""
    return C.DAMPING_PER_FRAME ** (dt_ms / 16.6667)

def _solve_quadratic(a, b, c):
    """Resuelve ``ax² + bx + c = 0`` devolviendo sus dos raíces."""
    disc = b*b - 4*a*c
    if disc < 0:
        return None, None
    root = math.sqrt(disc)
    return (-b - root) / (2*a), (-b + root) / (2*a)

def ray_circle(origin, dir_vec):
    """Mínima ``t`` > 0 del rayo con el dojo (o ``MAX_RANGE``)."""
    ox, oy = origin
    dx, dy = dir_vec
    cx, cy = C.CENTER
    a = dx*dx + dy*dy
    b = 2 * (dx*(ox-cx) + dy*(oy-cy))
    c = (ox-cx)**2 + (oy-cy)**2 - C.DOJO_RADIUS**2
    t1, t2 = _solve_quadratic(a, b, c)
    ts = [t for t in (t1, t2) if t and t > 0]
    return min(ts) if ts else C.MAX_RANGE_PX

def ray_disc(origin, dir_vec, center, radius):
    """Mínima ``t`` > 0 de intersección con un disco cualquiera."""
    ox, oy = origin
    dx, dy = dir_vec
    cx, cy = center
    fx, fy = ox-cx, oy-cy
    a = dx*dx + dy*dy
    b = 2 * (dx*fx + dy*fy)
    c = fx*fx + fy*fy - radius*radius
    t1, t2 = _solve_quadratic(a, b, c)
    ts = [t for t in (t1, t2) if t and t > 0]
    return min(ts) if ts else None