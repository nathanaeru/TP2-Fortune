import heapq
import math
from data_structures import Point, Event, SiteEvent, CircleEvent, VoronoiEdge, BeachNode
from geometry_utils import get_intersection, get_circumcircle, clip_line


class FortuneAlgorithm:
    """Executes Fortune's sweep-line algorithm to compute Voronoi diagrams and largest empty circles."""

    def __init__(self, sites: list[Point], width: float, height: float):
        """Initializes the algorithm with input sites and bounding box dimensions."""
        self.sites = sites
        self.width = width
        self.height = height
        self.events: list[Event] = []
        self.beach_head: BeachNode | None = None
        self.edges: list[VoronoiEdge] = []
        self.circle_events_processed: list[tuple[Point, float]] = []

    def process(self):
        """Runs the main sweep-line loop processing all site and circle events."""
        for site in self.sites:
            heapq.heappush(self.events, SiteEvent(site))

        while self.events:
            event = heapq.heappop(self.events)
            if event.is_site():
                if isinstance(event, SiteEvent):
                    self._handle_site_event(event)
            else:
                if isinstance(event, CircleEvent):
                    self._handle_circle_event(event)

        self._finish_edges()
        return self.edges

    def _handle_site_event(self, event: SiteEvent):
        """Handles insertion of a new parabolic arc into the beach line when sweep line reaches a site."""
        site = event.point
        if self.beach_head is None:
            self.beach_head = BeachNode(site)
            return

        curr: BeachNode | None = self.beach_head
        while curr:
            next_x = self._get_right_break_x(curr, event.y)
            if next_x is not None and site.x > next_x:
                curr = curr.next
            else:
                break

        if curr is None or curr.site is None:
            return

        if curr.circle_event:
            curr.circle_event.is_valid = False
            curr.circle_event = None

        left_arc = BeachNode(curr.site)
        middle_arc = BeachNode(site)
        right_arc = BeachNode(curr.site)

        left_arc.edge = curr.edge

        edge = VoronoiEdge(curr.site, site)
        self.edges.append(edge)

        middle_arc.edge = edge
        right_arc.edge = edge

        left_arc.prev = curr.prev
        if curr.prev:
            curr.prev.next = left_arc
        else:
            self.beach_head = left_arc

        left_arc.next = middle_arc
        middle_arc.prev = left_arc

        middle_arc.next = right_arc
        right_arc.prev = middle_arc

        right_arc.next = curr.next
        if curr.next:
            curr.next.prev = right_arc

        self._check_circle_event(left_arc, event.y)
        self._check_circle_event(right_arc, event.y)

    def _handle_circle_event(self, event: CircleEvent):
        """Handles collapse of an arc and creation of a Voronoi vertex when a circle event is reached."""
        if not event.is_valid:
            return

        arc = event.arc_node
        left_arc = arc.prev
        right_arc = arc.next

        if (
            not left_arc
            or not right_arc
            or not arc.site
            or not left_arc.site
            or not right_arc.site
        ):
            return

        if left_arc.circle_event:
            left_arc.circle_event.is_valid = False
            left_arc.circle_event = None
        if right_arc.circle_event:
            right_arc.circle_event.is_valid = False
            right_arc.circle_event = None

        vertex = event.center
        radius = math.hypot(event.center.x - arc.site.x, event.center.y - arc.site.y)
        self.circle_events_processed.append((event.center, radius))

        self._set_edge_endpoint(arc.edge, vertex)
        self._set_edge_endpoint(left_arc.edge, vertex)

        new_edge = VoronoiEdge(left_arc.site, right_arc.site)
        self.edges.append(new_edge)
        right_arc.edge = new_edge

        left_arc.next = right_arc
        right_arc.prev = left_arc

        self._check_circle_event(left_arc, event.y)
        self._check_circle_event(right_arc, event.y)

    def _set_edge_endpoint(self, edge: VoronoiEdge | None, point: Point):
        """Assigns an endpoint vertex to a Voronoi edge."""
        if edge:
            if edge.start is None:
                edge.set_start(point)
            elif edge.end is None:
                edge.set_end(point)

    def _check_circle_event(self, arc: BeachNode, sweep_y: float):
        """Checks whether an arc and its left and right neighbors converge to form a circle event."""
        if not arc or not arc.prev or not arc.next:
            return

        p1 = arc.prev.site
        p2 = arc.site
        p3 = arc.next.site

        if p1 is None or p2 is None or p3 is None:
            return

        if (p1.x, p1.y) == (p3.x, p3.y):
            return

        center, radius, event_y = get_circumcircle(p1, p2, p3)
        if center is None or event_y is None:
            return

        if event_y >= sweep_y - 1e-9:
            circle_event = CircleEvent(center, event_y, arc)
            arc.circle_event = circle_event
            heapq.heappush(self.events, circle_event)

    def _get_right_break_x(self, node: BeachNode, sweep_y: float) -> float | None:
        """Calculates the x-coordinate of the breakpoint on the right of the given arc node."""
        if not node or not node.next or not node.site or not node.next.site:
            return None
        return get_intersection(node.site, node.next.site, sweep_y)

    def _finish_edges(self):
        """Closes unfinished ray edges towards the bounding box boundary."""
        curr = self.beach_head
        while curr and curr.next:
            if curr.site and curr.next.site and curr.edge and curr.edge.end is None:
                dx = curr.next.site.y - curr.site.y
                dy = -(curr.next.site.x - curr.site.x)
                start_p = curr.edge.start or Point(
                    (curr.site.x + curr.next.site.x) / 2,
                    (curr.site.y + curr.next.site.y) / 2,
                )
                curr.edge.set_end(Point(start_p.x + dx * 1000, start_p.y + dy * 1000))
            curr = curr.next

    def get_clipped_edges(self) -> list[tuple[Point, Point]]:
        """Returns all Voronoi edges properly clipped within the bounding box boundaries."""
        clipped = []
        for edge in self.edges:
            if edge.start and edge.end:
                p1, p2 = clip_line(edge.start, edge.end, self.width, self.height)
                if p1 and p2:
                    clipped.append((p1, p2))
        return clipped

    def get_largest_empty_circles(self) -> list[tuple[Point, float]]:
        """Finds all valid empty circles with the maximum radius passing through three or more sites."""
        valid_circles = []
        for center, radius in self.circle_events_processed:
            if 0 <= center.x <= self.width and 0 <= center.y <= self.height:
                is_empty = True
                for site in self.sites:
                    dist = math.hypot(site.x - center.x, site.y - center.y)
                    if dist < radius - 1e-5:
                        is_empty = False
                        break
                if is_empty:
                    valid_circles.append((center, radius))

        if not valid_circles:
            return []

        max_r = max(r for _, r in valid_circles)
        return [c for c in valid_circles if abs(c[1] - max_r) < 1e-5]
