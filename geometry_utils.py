import math
from data_structures import Point


def get_parabola_y(site: Point, sweep_y: float, x: float) -> float:
    """Calculates the y-coordinate of a parabolic arc at position x for a given site and sweep line."""
    dp = 2 * (site.y - sweep_y)
    if dp == 0:
        return site.y
    return sweep_y + dp / 4 + ((x - site.x) ** 2) / dp


def trace_edge(start: Point, end: Point, site: Point, sweep_y: float):
    """Keep the part of a bisector already reached by a decreasing-y beach line."""
    delta = site.y - sweep_y
    if delta <= 0:
        return None

    # For P(t) = start + t * (end - start), solve parabola_y(P.x) <= P.y.
    # The quadratic is convex, so the traced portion is a single interval.
    dx, dy = end.x - start.x, end.y - start.y
    offset = start.x - site.x
    a = dx * dx
    b = offset * dx - delta * dy
    c = offset * offset - 2 * delta * (start.y - sweep_y - delta / 2)
    at_end = a + 2 * b + c
    if c <= 0 and at_end <= 0:
        return start, end

    if a == 0:
        if c > 0 and at_end > 0:
            return None
        crossing = c / (c - at_end)
        low, high = (0, crossing) if c <= 0 else (crossing, 1)
    else:
        discriminant = b * b - a * c
        if discriminant <= 0:
            return None
        q = -b - math.copysign(math.sqrt(discriminant), b)
        first, second = sorted((q / a, c / q))
        low, high = max(0, first), min(1, second)
    if low >= high:
        return None
    return Point(start.x + low * dx, start.y + low * dy), Point(start.x + high * dx, start.y + high * dy)


def get_intersection(site1: Point, site2: Point, sweep_y: float) -> float:
    """Return the breakpoint between the left and right arcs for decreasing sweep y."""
    p = site1.y - sweep_y
    q = site2.y - sweep_y
    dx = site2.x - site1.x
    dy = site2.y - site1.y
    if dy == 0:
        return site1.x + dx / 2
    if p == 0:
        return site1.x
    if q == 0:
        return site2.x

    root = math.sqrt(p) * math.sqrt(q) * math.hypot(dx, dy)
    # Rationalize the numerator when subtraction could lose precision.
    if dx >= 0:
        offset = p * (dx * dx + q * dy) / (p * dx + root)
    else:
        offset = (root - p * dx) / dy
    return site1.x + offset


def get_circumcircle(p1: Point, p2: Point, p3: Point):
    """Return the circumcenter, radius, and bottom-to-top circle event position."""
    bx, by = p2.x - p1.x, p2.y - p1.y
    cx, cy = p3.x - p1.x, p3.y - p1.y
    determinant = 2 * (bx * cy - by * cx)
    if determinant == 0:
        return None, None, None

    b_squared = bx * bx + by * by
    c_squared = cx * cx + cy * cy
    ux = (b_squared * cy - c_squared * by) / determinant
    uy = (bx * c_squared - cx * b_squared) / determinant
    center = Point(p1.x + ux, p1.y + uy)
    radius = math.hypot(ux, uy)
    return center, radius, center.y - radius


def clip_polygon(polygon: list[Point], nx: float, ny: float, limit: float) -> list[Point]:
    """Keep the part of the polygon satisfying nx*x + ny*y <= limit."""
    if not polygon:
        return []
    clipped = []
    previous = polygon[-1]
    previous_distance = nx * previous.x + ny * previous.y - limit
    for current in polygon:
        distance = nx * current.x + ny * current.y - limit
        if (distance < 0 < previous_distance) or (previous_distance < 0 < distance):
            ratio = previous_distance / (previous_distance - distance)
            clipped.append(Point(
                previous.x + ratio * (current.x - previous.x),
                previous.y + ratio * (current.y - previous.y),
            ))
        if distance <= 0:
            clipped.append(current)
        previous, previous_distance = current, distance
    return clipped


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
