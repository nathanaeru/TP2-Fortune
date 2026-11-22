import heapq
import math

from data_structures import BeachNode, CircleEvent, Event, Point, SiteEvent, VoronoiEdge
from geometry_utils import clip_polygon, get_circumcircle, get_intersection


class FortuneAlgorithm:
    """Sweep from bottom to top and close the resulting cells against the bounding box."""

    def __init__(self, sites: list[Point], width: float, height: float):
        unique = {(site.x, site.y): site for site in sites}
        self.sites = list(unique.values())
        self.width = width
        self.height = height
        self.events: list[Event] = []
        self.beach_head: BeachNode | None = None
        self.edges: list[VoronoiEdge] = []
        self.cells: list[tuple[Point, list[Point]]] = []
        self.circle_events_processed: list[tuple[Point, float]] = []
        self.sweep_steps: list[tuple[float, tuple[Point, ...]]] = []
        self.neighbors: dict[Point, dict[Point, None]] = {}
        self.tolerance = 64 * math.ulp(max(width, height))

    def process(self, *, record_sweep: bool = False):
        """Process events and optionally save the beach line after each event."""
        self.events = [SiteEvent(site) for site in self.sites]
        heapq.heapify(self.events)
        self.beach_head = None
        self.circle_events_processed.clear()
        self.sweep_steps.clear()
        self.neighbors = {site: {} for site in self.sites}
        while self.events:
            event = heapq.heappop(self.events)
            if isinstance(event, SiteEvent):
                self._handle_site_event(event)
            elif event.is_valid:
                self._handle_circle_event(event)
            else:
                continue
            if record_sweep:
                sites = []
                arc = self.beach_head
                while arc is not None:
                    sites.append(arc.site)
                    arc = arc.next
                self.sweep_steps.append((event.y, tuple(sites)))
        self._finish_diagram()
        return self.edges

    def _connect(self, left: Point, right: Point):
        self.neighbors[left][right] = None
        self.neighbors[right][left] = None

    def _handle_site_event(self, event: SiteEvent):
        site = event.point
        inserted = BeachNode(site)
        arc = self.beach_head
        if arc is None:
            self.beach_head = inserted
            return

        while arc.next and site.x > get_intersection(arc.site, arc.next.site, event.y):
            arc = arc.next
        self._connect(arc.site, site)
        if arc.site.y == site.y:
            # All sites on the initial directrix arrive from left to right.
            arc.next = inserted
            inserted.prev = arc
            self._check_circle_event(arc, event.y)
            return

        # Reuse the old arc on the left and duplicate its focus on the right.
        self._invalidate_circle_event(arc)
        right = BeachNode(arc.site)
        right.next = arc.next
        if right.next:
            right.next.prev = right
        arc.next = inserted
        inserted.prev = arc
        inserted.next = right
        right.prev = inserted

        self._check_circle_event(arc, event.y)
        self._check_circle_event(right, event.y)

    def _handle_circle_event(self, event: CircleEvent):
        arc = event.arc_node
        left, right = arc.prev, arc.next
        self._invalidate_circle_event(left)
        self._invalidate_circle_event(right)
        radius = math.hypot(event.center.x - arc.site.x, event.center.y - arc.site.y)
        self.circle_events_processed.append((event.center, radius))

        self._connect(left.site, right.site)
        left.next = right
        right.prev = left
        self._check_circle_event(left, event.y)
        self._check_circle_event(right, event.y)

    @staticmethod
    def _invalidate_circle_event(arc: BeachNode):
        if arc.circle_event:
            arc.circle_event.is_valid = False
            arc.circle_event = None

    def _check_circle_event(self, arc: BeachNode, sweep_y: float):
        if not arc.prev or not arc.next:
            return
        p1, p2, p3 = arc.prev.site, arc.site, arc.next.site
        cross = (p2.x - p1.x) * (p3.y - p1.y) - (p2.y - p1.y) * (p3.x - p1.x)
        if cross >= 0:
            return
        center, _, event_y = get_circumcircle(p1, p2, p3)
        if center is not None and event_y <= sweep_y + self.tolerance:
            event = CircleEvent(center, min(event_y, sweep_y), arc)
            arc.circle_event = event
            heapq.heappush(self.events, event)

    @staticmethod
    def _bisector(site: Point, other: Point) -> tuple[float, float, float]:
        """Return a unit normal and limit for the half-plane closer to site."""
        dx, dy = other.x - site.x, other.y - site.y
        length = math.hypot(dx, dy)
        nx, ny = dx / length, dy / length
        return nx, ny, nx * (site.x + dx / 2) + ny * (site.y + dy / 2)

    def _finish_diagram(self):
        """Clip each cell using the neighboring sites discovered by the sweep."""
        box = [
            Point(0, 0), Point(self.width, 0),
            Point(self.width, self.height), Point(0, self.height),
        ]
        self.cells = []
        self.edges = []
        seen = set()
        for site, neighbors in self.neighbors.items():
            bisectors = {other: self._bisector(site, other) for other in neighbors}
            polygon = box
            for bisector in bisectors.values():
                polygon = clip_polygon(polygon, *bisector)
            if len(polygon) < 3:
                continue
            self.cells.append((site, polygon))

            # A side on a bisector is internal. Emit it once, even though it
            # belongs to both cells. Sides of the box are drawn by the GUI.
            for other, (nx, ny, limit) in bisectors.items():
                pair = frozenset((site, other))
                if pair in seen:
                    continue
                for index, end in enumerate(polygon):
                    start = polygon[index - 1]
                    if (
                        abs(nx * start.x + ny * start.y - limit) <= self.tolerance
                        and abs(nx * end.x + ny * end.y - limit) <= self.tolerance
                        and math.hypot(end.x - start.x, end.y - start.y) > self.tolerance
                    ):
                        edge = VoronoiEdge(site, other)
                        edge.set_start(start)
                        edge.set_end(end)
                        self.edges.append(edge)
                        seen.add(pair)
                        break

    def get_cells(self) -> list[tuple[Point, list[Point]]]:
        """Return each site with the vertices of its bounded Voronoi cell."""
        return self.cells

    def get_clipped_edges(self) -> list[tuple[Point, Point]]:
        """Return the internal sides of the bounded cells."""
        return [(edge.start, edge.end) for edge in self.edges]

    def get_largest_empty_circles(self) -> list[tuple[Point, float]]:
        """Return all distinct maximum empty circles with centers in the box."""
        circles = []
        for center, radius in self.circle_events_processed:
            if not (0 <= center.x <= self.width and 0 <= center.y <= self.height):
                continue
            if any(math.hypot(site.x - center.x, site.y - center.y) < radius - self.tolerance
                   for site in self.sites):
                continue
            if any(math.hypot(center.x - other.x, center.y - other.y) <= self.tolerance
                   for other, _ in circles):
                continue
            circles.append((center, radius))
        if not circles:
            return []
        largest = max(radius for _, radius in circles)
        return [(center, radius) for center, radius in circles
                if largest - radius <= self.tolerance]
