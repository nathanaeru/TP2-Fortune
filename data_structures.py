class Point:
    """Represents a two-dimensional point in the Tkinter coordinate system."""

    def __init__(self, x: float, y: float):
        """Initializes a 2D point with x and y coordinates."""
        self.x = float(x)
        self.y = float(y)

    def __repr__(self):
        """Returns the string representation of the point."""
        return f"Point({self.x}, {self.y})"


class Event:
    """Base class for sweep-line events ordered by vertical position."""

    def __init__(self, x: float, y: float):
        """Initializes an event at the specified coordinates."""
        self.x = float(x)
        self.y = float(y)

    def __lt__(self, other):
        """Compares events primarily by y-coordinate from top to bottom then x-coordinate."""
        if self.y != other.y:
            return self.y > other.y
        return self.x < other.x

    def is_site(self) -> bool:
        """Returns True if this event is a site event, False otherwise."""
        raise NotImplementedError("Subclasses must implement the is_site method.")


class SiteEvent(Event):
    """Represents a sweep-line event triggered when reaching a new site."""

    def __init__(self, point: Point):
        """Initializes a site event for a given input point."""
        super().__init__(point.x, point.y)
        self.point = point

    def is_site(self) -> bool:
        """Returns True to indicate that this is a site event."""
        return True


class CircleEvent(Event):
    """Represents a sweep-line event triggered when a parabola arc vanishes."""

    def __init__(self, center: Point, y_sweep: float, arc_node):
        """Initializes a circle event with its circumcenter, sweep y-coordinate, and target arc node."""
        super().__init__(center.x, y_sweep)
        self.center = center
        self.arc_node = arc_node
        self.is_valid = True

    def is_site(self) -> bool:
        """Returns False to indicate that this is not a site event."""
        return False


class VoronoiEdge:
    """Represents a bisector edge between two Voronoi sites."""

    def __init__(self, site1: Point, site2: Point):
        """Initializes an edge separating two sites."""
        self.site1 = site1
        self.site2 = site2
        self.start: Point | None = None
        self.end: Point | None = None

    def set_start(self, point: Point):
        """Sets the starting vertex of the edge."""
        self.start = point

    def set_end(self, point: Point):
        """Sets the ending vertex of the edge."""
        self.end = point


class BeachNode:
    """Represents a node in the beach line tree structure."""

    def __init__(self, site: Point | None = None):
        """Initializes a beach line node for an arc or internal breakpoint."""
        self.site: Point | None = site
        self.left: BeachNode | None = None
        self.right: BeachNode | None = None
        self.parent: BeachNode | None = None
        self.edge: VoronoiEdge | None = None
        self.circle_event: CircleEvent | None = None
        self.prev: BeachNode | None = None
        self.next: BeachNode | None = None
