import math
from data_structures import Point


def get_parabola_y(site: Point, sweep_y: float, x: float) -> float:
    """Calculates the y-coordinate of a parabolic arc at position x for a given site and sweep line."""
    dp = 2 * (site.y - sweep_y)
    if dp == 0:
        return site.y
    return ((x - site.x) ** 2 + site.y**2 - sweep_y**2) / dp


def get_intersection(site1: Point, site2: Point, sweep_y: float) -> float:
    """Computes the x-coordinate of the intersection breakpoint between two adjacent parabolic arcs."""
    p1 = site1
    p2 = site2

    if p1.y == p2.y:
        return (p1.x + p2.x) / 2.0

    d1 = 2.0 * (p1.y - sweep_y)
    d2 = 2.0 * (p2.y - sweep_y)

    if d1 == 0:
        return p1.x
    if d2 == 0:
        return p2.x

    a1 = 1.0 / d1
    b1 = -2.0 * p1.x / d1
    c1 = (p1.x**2 + p1.y**2 - sweep_y**2) / d1

    a2 = 1.0 / d2
    b2 = -2.0 * p2.x / d2
    c2 = (p2.x**2 + p2.y**2 - sweep_y**2) / d2

    a = a1 - a2
    b = b1 - b2
    c = c1 - c2

    disc = b**2 - 4 * a * c
    if disc < 0:
        disc = 0.0

    x1 = (-b + math.sqrt(disc)) / (2 * a)
    x2 = (-b - math.sqrt(disc)) / (2 * a)

    if p1.y > p2.y:
        return max(x1, x2)
    else:
        return min(x1, x2)


def get_circumcircle(p1: Point, p2: Point, p3: Point):
    """Computes the circumcenter, radius, and lowest sweep-line y-coordinate for three points."""
    d = 2 * (p1.x * (p2.y - p3.y) + p2.x * (p3.y - p1.y) + p3.x * (p1.y - p2.y))
    if abs(d) < 1e-9:
        return None, None, None

    ux = (
        (p1.x**2 + p1.y**2) * (p2.y - p3.y)
        + (p2.x**2 + p2.y**2) * (p3.y - p1.y)
        + (p3.x**2 + p3.y**2) * (p1.y - p2.y)
    ) / d

    uy = (
        (p1.x**2 + p1.y**2) * (p3.x - p2.x)
        + (p2.x**2 + p2.y**2) * (p1.x - p3.x)
        + (p3.x**2 + p3.y**2) * (p2.x - p1.x)
    ) / d

    center = Point(ux, uy)
    radius = math.hypot(p1.x - ux, p1.y - uy)
    y_sweep = uy + radius

    return center, radius, y_sweep


def clip_line(p1: Point, p2: Point, width: float, height: float):
    """Clips a line segment to the bounding box specified by width and height using Cohen-Sutherland algorithm."""
    x1, y1 = p1.x, p1.y
    x2, y2 = p2.x, p2.y

    INSIDE, LEFT, RIGHT, BOTTOM, TOP = 0, 1, 2, 4, 8

    def compute_code(x, y):
        code = INSIDE
        if x < 0:
            code |= LEFT
        elif x > width:
            code |= RIGHT
        if y < 0:
            code |= BOTTOM
        elif y > height:
            code |= TOP
        return code

    code1 = compute_code(x1, y1)
    code2 = compute_code(x2, y2)
    accept = False

    while True:
        if code1 == 0 and code2 == 0:
            accept = True
            break
        elif (code1 & code2) != 0:
            break
        else:
            code_out = code1 if code1 != 0 else code2
            x, y = 0.0, 0.0
            if code_out & TOP:
                x = x1 + (x2 - x1) * (height - y1) / (y2 - y1)
                y = height
            elif code_out & BOTTOM:
                x = x1 + (x2 - x1) * (0 - y1) / (y2 - y1)
                y = 0
            elif code_out & RIGHT:
                y = y1 + (y2 - y1) * (width - x1) / (x2 - x1)
                x = width
            elif code_out & LEFT:
                y = y1 + (y2 - y1) * (0 - x1) / (x2 - x1)
                x = 0

            if code_out == code1:
                x1, y1 = x, y
                code1 = compute_code(x1, y1)
            else:
                x2, y2 = x, y
                code2 = compute_code(x2, y2)

    if accept:
        return Point(x1, y1), Point(x2, y2)
    return None, None
