import math
import random
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from algorithm import FortuneAlgorithm
from data_structures import Point
from geometry_utils import get_intersection, get_parabola_y, trace_edge


BACKGROUND = "#eaf2fc"
PANEL = "#f9fcff"
WHITE = "#ffffff"
NAVY = "#102a4d"
MUTED = "#4d6583"
BORDER = "#c1d3ea"
BLUE = "#215bc6"
EDGE = "#497ac9"
CIRCLE = "#007c9e"
GRID = "#e7effa"
CELL_COLORS = ("#d7e7ff", "#edf4ff", "#c9dcfb", "#e0edfb", "#c5e5f4", "#e7efff")
SWEEP = "#1269db"
BEACH = "#503ba8"
PENDING_SITE = "#9bb7d9"
FONT = "Segoe UI"
DEFAULT_BOUNDS = (0, 0, 900, 600)
SWEEP_SECONDS = 4.2


def read_points(path):
    """Read one x, y pair per line, with optional comments and blank lines."""
    coordinates = set()
    points = []
    for row, line in enumerate(Path(path).read_text(encoding="utf-8-sig").splitlines(), 1):
        fields = line.partition("#")[0].replace(",", " ").split()
        if not fields:
            continue
        try:
            x, y = map(float, fields)
            if not (math.isfinite(x) and math.isfinite(y)):
                raise ValueError
        except ValueError:
            raise ValueError(f"Baris {row} harus berisi dua angka berhingga, misalnya 120 80.") from None
        if (x, y) not in coordinates:
            coordinates.add((x, y))
            points.append(Point(x, y))
    if not points:
        raise ValueError("File belum berisi titik.")
    return points


def bounds_for(points):
    """Keep the default board unless a file needs a larger coordinate range."""
    left, top, right, bottom = DEFAULT_BOUNDS
    min_x = min(point.x for point in points)
    min_y = min(point.y for point in points)
    max_x = max(point.x for point in points)
    max_y = max(point.y for point in points)
    if left <= min_x <= max_x <= right and top <= min_y <= max_y <= bottom:
        return DEFAULT_BOUNDS

    # Fit both axes around the file data and leave space for points at the extremes.
    width = max(max_x - min_x, 1)
    height = max(max_y - min_y, 1)
    padding = max(0.08 * max(width, height), math.ulp(min_x), math.ulp(min_y),
                  math.ulp(max_x), math.ulp(max_y))
    bounds = (min_x - padding, min_y - padding, max_x + padding, max_y + padding)
    left, top, right, bottom = bounds
    if not all(map(math.isfinite, (*bounds, right - left, bottom - top))):
        raise ValueError("Rentang koordinat file terlalu besar.")
    return bounds


class FortuneGUI:
    """Display and edit Fortune's input sites and draw the results it returns."""

    def __init__(self, root):
        self.root = root
        root.title("Diagram Voronoi  |  Algoritma Fortune")
        root.geometry("1150x760")
        root.minsize(880, 640)
        root.configure(bg=BACKGROUND)

        self.points = []
        self.bounds = DEFAULT_BOUNDS
        self.custom_bounds = False
        self.zoom = 1.0
        self.undo_history = []
        self.cells = []
        self.edges = []
        self.circles = []
        self.sweep_y = None
        self.sweep_after = None
        self.beach_sites: tuple[Point, ...] = ()
        self.site_count = tk.StringVar(value="0")
        self.edge_count = tk.StringVar(value="0")
        self.cell_count = tk.StringVar(value="0")
        self.show_circles = tk.BooleanVar(value=True)
        self.source = tk.StringVar()
        self.status = tk.StringVar()

        self._build()
        root.bind("<Control-o>", lambda event: self.open_file())
        root.bind("<Control-z>", lambda event: self.undo())
        root.bind("<F5>", lambda event: self.animate_sweep())
        for key in ("plus", "equal", "KP_Add"):
            root.bind(f"<Control-{key}>", lambda event: self._change_zoom(1.25))
        for key in ("minus", "KP_Subtract"):
            root.bind(f"<Control-{key}>", lambda event: self._change_zoom(0.8))
        root.bind("<MouseWheel>", self._scroll_canvas)
        self._invalidate_result()

    def _label(self, parent, text="", size=10, color=NAVY, weight="normal", **options):
        return tk.Label(
            parent, text=text, bg=parent["bg"], fg=color, font=(FONT, size, weight),
            **options,
        )

    def _build(self):
        menu = tk.Menu(self.root)
        self.file_menu = tk.Menu(menu, tearoff=False)
        self.file_menu.add_command(label="Buka file TXT...", accelerator="Ctrl+O", command=self.open_file)
        self.file_menu.add_command(label="Muat contoh 25 titik", command=self.load_example)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Hapus", accelerator="Ctrl+Z", command=self.undo)
        self.file_menu.add_command(label="Hapus semua", command=self.clear)
        menu.add_cascade(label="File", menu=self.file_menu)
        edit_menu = tk.Menu(menu, tearoff=False)
        edit_menu.add_command(label="Bounding box...", command=self.edit_bounds)
        menu.add_cascade(label="Edit", menu=edit_menu)
        view_menu = tk.Menu(menu, tearoff=False)
        view_menu.add_checkbutton(label="Tampilkan lingkaran", variable=self.show_circles, command=self._draw)
        menu.add_cascade(label="Tampilan", menu=view_menu)
        self.root.configure(menu=menu)

        header = tk.Frame(self.root, bg=NAVY, padx=25, pady=14)
        header.pack(fill="x")
        self._label(header, "Diagram Voronoi", 25, WHITE, "bold").pack(anchor="w")

        body = tk.Frame(self.root, bg=BACKGROUND)
        body.pack(fill="both", expand=True, padx=20, pady=(16, 9))
        sidebar = tk.Frame(body, bg=PANEL, padx=14, pady=12, highlightthickness=1, highlightbackground=BORDER)
        sidebar.pack(side="left", fill="y", padx=(0, 14))
        plot = tk.Frame(body, bg=PANEL, padx=14, pady=12, highlightthickness=1, highlightbackground=BORDER)
        plot.pack(side="left", fill="both", expand=True)

        tk.Button(
            sidebar, text="Play", command=self.animate_sweep, width=10, pady=7,
            bd=0, relief="flat", cursor="hand2", highlightcolor=BLUE,
            bg=BLUE, fg=WHITE, activebackground="#194ca8", activeforeground=WHITE,
            font=(FONT, 10, "bold"),
        ).pack(fill="x", pady=(0, 15))
        for name, count in (("Titik", self.site_count), ("Sisi", self.edge_count), ("Sel", self.cell_count)):
            self._label(sidebar, size=20, weight="bold", textvariable=count).pack(anchor="w")
            self._label(sidebar, name, 9, MUTED).pack(anchor="w", pady=(0, 10))

        board = tk.Frame(plot, bg="#e1ecfa", highlightthickness=1, highlightbackground=BORDER)
        board.pack(fill="both", expand=True)
        board.grid_rowconfigure(0, weight=1)
        board.grid_columnconfigure(0, weight=1)
        self.viewport = tk.Canvas(board, bg=board["bg"], bd=0, highlightthickness=0, width=1, height=1)
        self.viewport.grid(row=0, column=0, sticky="nsew")
        vertical = ttk.Scrollbar(board, orient="vertical", command=self.viewport.yview)
        horizontal = ttk.Scrollbar(board, orient="horizontal", command=self.viewport.xview)
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        self.viewport.configure(xscrollcommand=horizontal.set, yscrollcommand=vertical.set)
        self.canvas = tk.Canvas(self.viewport, bg=WHITE, bd=0, highlightthickness=0, cursor="crosshair")
        self.canvas_window = self.viewport.create_window(0, 0, anchor="nw", window=self.canvas)
        self.viewport.bind("<Configure>", self._fit_canvas)
        self.canvas.bind("<Configure>", self._draw)
        self.canvas.bind("<Button-1>", self.add_point)
        self.canvas.bind("<Button-3>", self.remove_point)

        footer = tk.Frame(self.root, bg=BACKGROUND, padx=21)
        footer.pack(fill="x", pady=(0, 9))
        self._label(footer, size=9, textvariable=self.status).pack(side="left")
        self._label(footer, size=9, color=MUTED, textvariable=self.source).pack(side="right")

    def _replace_points(self, points, bounds, source, custom_bounds=False):
        if bounds != self.bounds:
            self.zoom = 1.0
        self.points = points
        self.bounds = bounds
        self.custom_bounds = custom_bounds
        self.source.set(source)
        self._fit_canvas()
        self._invalidate_result()

    def load_example(self):
        rng = random.Random(812)
        points = [Point(round(rng.uniform(60, 840)), round(rng.uniform(55, 545))) for _ in range(25)]
        bounds = self.bounds if self.custom_bounds else DEFAULT_BOUNDS
        self._remember_points()
        self._replace_points(points, bounds, "Contoh bawaan", self.custom_bounds)

    def open_file(self):
        filename = filedialog.askopenfilename(
            parent=self.root, title="Buka file titik",
            filetypes=[("File teks", "*.txt"), ("Semua file", "*.*")],
        )
        if not filename:
            return
        try:
            points = read_points(filename)
            bounds = self.bounds if self.custom_bounds else bounds_for(points)
        except (OSError, ValueError) as exc:
            messagebox.showerror("File titik gagal dibuka", str(exc), parent=self.root)
            return
        self._remember_points()
        self._replace_points(points, bounds, Path(filename).name, self.custom_bounds)

    def clear(self):
        if self.points:
            self._remember_points()
            bounds = self.bounds if self.custom_bounds else DEFAULT_BOUNDS
            self._replace_points([], bounds, "", self.custom_bounds)

    def _remember_points(self):
        self.undo_history.append((self.points.copy(), self.bounds, self.source.get(), self.custom_bounds))

    def undo(self):
        if self.undo_history:
            self._replace_points(*self.undo_history.pop())

    def edit_bounds(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Bounding box")
        dialog.transient(self.root)
        dialog.resizable(False, False)
        form = ttk.Frame(dialog, padding=16)
        form.grid(sticky="nsew")
        entries = []
        for row, (label, value) in enumerate(zip(("X min", "Y min", "X max", "Y max"), self.bounds)):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=4)
            entry = ttk.Entry(form, width=18)
            entry.insert(0, repr(value))
            entry.grid(row=row, column=1, columnspan=2, sticky="ew", pady=4)
            entries.append(entry)

        def apply():
            try:
                left, top, right, bottom = bounds = tuple(float(entry.get()) for entry in entries)
                if (
                    not all(map(math.isfinite, (*bounds, right - left, bottom - top)))
                    or not (left < right and top < bottom)
                ):
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Bounding box tidak valid", "Isi angka berhingga dengan min lebih kecil dari max.",
                    parent=dialog,
                )
                return
            if bounds != self.bounds or not self.custom_bounds:
                self._remember_points()
                self._replace_points(self.points, bounds, self.source.get(), True)
            dialog.destroy()

        ttk.Button(form, text="Batal", command=dialog.destroy).grid(row=4, column=1, padx=(0, 6), pady=(10, 0))
        ttk.Button(form, text="Terapkan", command=apply).grid(row=4, column=2, pady=(10, 0))
        dialog.bind("<Return>", lambda event: apply())
        dialog.bind("<Escape>", lambda event: dialog.destroy())
        dialog.wait_visibility()
        dialog.grab_set()
        entries[0].focus_set()
        entries[0].selection_range(0, "end")

    def _fit_canvas(self, event=None):
        viewport = self.viewport
        width, height = viewport.winfo_width(), viewport.winfo_height()
        available_width, available_height = max(1, width - 24), max(1, height - 24)
        left, top, right, bottom = self.bounds
        aspect = (right - left) / (bottom - top)
        if aspect >= available_width / available_height:
            fit_width, fit_height = available_width, available_width / aspect
        else:
            fit_width, fit_height = available_height * aspect, available_height
        canvas_width = max(1, round(fit_width * self.zoom))
        canvas_height = max(1, round(fit_height * self.zoom))
        region_width = max(width, canvas_width + 24)
        region_height = max(height, canvas_height + 24)
        viewport.coords(self.canvas_window, (region_width - canvas_width) // 2, (region_height - canvas_height) // 2)
        viewport.itemconfigure(self.canvas_window, width=canvas_width, height=canvas_height)
        viewport.configure(scrollregion=(0, 0, region_width, region_height))

    def _change_zoom(self, factor):
        zoom = min(5.0, max(0.5, round(self.zoom * factor, 8)))
        if zoom == self.zoom:
            return "break"

        viewport = self.viewport
        center_x, center_y = viewport.winfo_width() / 2, viewport.winfo_height() / 2
        old_x, old_y = viewport.coords(self.canvas_window)
        old_width = int(viewport.itemcget(self.canvas_window, "width"))
        old_height = int(viewport.itemcget(self.canvas_window, "height"))
        anchor_x = (viewport.canvasx(center_x) - old_x) / old_width
        anchor_y = (viewport.canvasy(center_y) - old_y) / old_height
        self.zoom = zoom
        self._fit_canvas()
        x, y = viewport.coords(self.canvas_window)
        width = int(viewport.itemcget(self.canvas_window, "width"))
        height = int(viewport.itemcget(self.canvas_window, "height"))
        _, _, region_width, region_height = map(int, viewport.cget("scrollregion").split())
        viewport.xview_moveto((x + anchor_x * width - center_x) / region_width)
        viewport.yview_moveto((y + anchor_y * height - center_y) / region_height)
        return "break"

    def _scroll_canvas(self, event):
        if event.state & 0x4:
            return self._change_zoom(1.25 if event.delta > 0 else 0.8)
        steps = max(1, abs(event.delta) // 120) * (-1 if event.delta > 0 else 1)
        scroll = self.viewport.xview_scroll if event.state & 0x1 else self.viewport.yview_scroll
        scroll(steps, "units")
        return "break"

    def _geometry(self):
        left, top, right, bottom = self.bounds
        width = max(1, self.canvas.winfo_width() - 1)
        height = max(1, self.canvas.winfo_height() - 1)
        return left, top, width / (right - left), height / (bottom - top)

    def _point_at(self, event):
        left, top, scale_x, scale_y = self._geometry()
        return Point(left + event.x / scale_x, top + event.y / scale_y)

    def _nearest_index(self, event, tolerance):
        left, top, scale_x, scale_y = self._geometry()
        nearest = None
        for index, point in enumerate(self.points):
            distance = math.hypot(
                (point.x - left) * scale_x - event.x, (point.y - top) * scale_y - event.y,
            )
            if distance <= tolerance:
                tolerance = distance
                nearest = index
        return nearest

    def add_point(self, event):
        if self._nearest_index(event, tolerance=3) is None:
            self._remember_points()
            self.points.append(self._point_at(event))
            self.source.set("")
            self._invalidate_result()

    def remove_point(self, event):
        index = self._nearest_index(event, tolerance=10)
        if index is not None:
            self._remember_points()
            del self.points[index]
            self.source.set("")
            self._invalidate_result()

    def _invalidate_result(self):
        self._stop_sweep()
        self.cells = []
        self.edges = []
        self.circles = []
        self.site_count.set(0)
        self.edge_count.set(0)
        self.cell_count.set(0)
        self.status.set("")
        self.file_menu.entryconfigure("Hapus", state="normal" if self.undo_history else "disabled")
        self.file_menu.entryconfigure("Hapus semua", state="normal" if self.points else "disabled")
        self._draw()

    def _stop_sweep(self):
        if self.sweep_after is not None:
            self.root.after_cancel(self.sweep_after)
            self.sweep_after = None
        self.sweep_y = None
        self.beach_sites = ()

    def animate_sweep(self):
        self._invalidate_result()
        if not self.points:
            return
        algorithm = self._compute()
        if algorithm is None:
            return
        first_y = max(algorithm.height, max(site.y for site in algorithm.sites))
        # A cell is complete once the beach line has reached all its vertices.
        cell_completion = [
            min(point.y - math.hypot(point.x - site.x, point.y - site.y) for point in polygon)
            for site, polygon in algorithm.get_cells()
        ]
        last_y = min(0, min(site.y for site in algorithm.sites), min(cell_completion, default=0))
        started = time.monotonic()
        next_step = 0
        self.status.set("Animasi berjalan")

        def tick():
            nonlocal next_step
            self.sweep_after = None
            progress = min((time.monotonic() - started) / SWEEP_SECONDS, 1)
            if progress >= 1:
                self._stop_sweep()
                self._show_result(algorithm)
                return
            self.sweep_y = first_y - progress * (first_y - last_y)
            while next_step < len(algorithm.sweep_steps):
                event_y, sites = algorithm.sweep_steps[next_step]
                if event_y < self.sweep_y:
                    break
                self.beach_sites = sites
                next_step += 1
            self.edges = []
            for edge in algorithm.edges:
                visible = trace_edge(edge.start, edge.end, edge.site1, self.sweep_y)
                if visible is not None:
                    self.edges.append(visible)
            self.site_count.set(sum(site.y >= self.sweep_y for site in algorithm.sites))
            self.edge_count.set(len(self.edges))
            self.cell_count.set(sum(y >= self.sweep_y for y in cell_completion))
            self._draw()
            self.sweep_after = self.root.after(16, tick)

        tick()

    def _compute(self):
        left, top, right, bottom = self.bounds
        # Reflect canvas y so Fortune's decreasing-y sweep moves down the screen.
        sites = [Point(point.x - left, bottom - point.y) for point in self.points]
        algorithm = FortuneAlgorithm(sites, right - left, bottom - top)
        try:
            algorithm.process(record_sweep=True)
        except ArithmeticError:
            self._invalidate_result()
            self.status.set("Perhitungan gagal untuk koordinat ini.")
            return None
        return algorithm

    def _show_result(self, algorithm):
        self.cells = algorithm.get_cells()
        self.edges = algorithm.get_clipped_edges()
        self.circles = algorithm.get_largest_empty_circles()
        self.site_count.set(len(algorithm.sites))
        self.edge_count.set(len(self.edges))
        self.cell_count.set(len(self.cells))
        self.status.set("")
        self._draw()

    def _draw_beach_line(self, sweep_y, scale_x, scale_y, canvas_height):
        left, top, right, bottom = self.bounds
        board_width, board_height = right - left, bottom - top
        # Each active focus owns the interval between its two breakpoints.
        breakpoints = [0]
        breakpoints.extend(
            get_intersection(a, b, sweep_y) for a, b in zip(self.beach_sites, self.beach_sites[1:])
        )
        breakpoints.append(board_width)
        for index, site in enumerate(self.beach_sites):
            delta = site.y - sweep_y
            if delta <= 0:
                continue
            # Clip at the reflected upper boundary before sampling the parabola.
            reach_squared = delta * (2 * (board_height - sweep_y) - delta)
            if reach_squared <= 0:
                continue
            reach = math.sqrt(reach_squared)
            start = max(0, breakpoints[index], site.x - reach)
            end = min(board_width, breakpoints[index + 1], site.x + reach)
            if start >= end:
                continue
            segments = max(2, math.ceil((end - start) * scale_x / 3))
            coordinates = []
            for step in range(segments + 1):
                x = start + (end - start) * step / segments
                y = get_parabola_y(site, sweep_y, x)
                coordinates.extend((x * scale_x, canvas_height - y * scale_y))
            self.canvas.create_line(coordinates, fill=BEACH, width=3, tags="beach")

    def _draw(self, event=None):
        canvas = self.canvas
        canvas.delete("all")
        left, top, scale_x, scale_y = self._geometry()
        width = canvas.winfo_width() - 1
        height = canvas.winfo_height() - 1
        if width < 2 or height < 2:
            return
        for index, (_, polygon) in enumerate(self.cells):
            coordinates = [(point.x * scale_x, height - point.y * scale_y) for point in polygon]
            canvas.create_polygon(
                coordinates, fill=CELL_COLORS[index % len(CELL_COLORS)], outline="", tags="cell",
            )
        for index in range(1, 12):
            x = width * index / 12
            canvas.create_line(x, 0, x, height, fill=GRID)
        for index in range(1, 8):
            y = height * index / 8
            canvas.create_line(0, y, width, y, fill=GRID)
        for start, end in self.edges:
            canvas.create_line(
                start.x * scale_x, height - start.y * scale_y,
                end.x * scale_x, height - end.y * scale_y,
                fill=EDGE, width=2, tags="edge",
            )
        if self.show_circles.get():
            for center, radius in self.circles:
                x, y = center.x * scale_x, height - center.y * scale_y
                rx, ry = radius * scale_x, radius * scale_y
                canvas.create_oval(x - rx, y - ry, x + rx, y + ry, outline=CIRCLE,
                                   width=3, dash=(7, 4), tags="circle")
                canvas.create_line(x - 5, y, x + 5, y, fill=CIRCLE, width=2, tags="circle_center")
                canvas.create_line(x, y - 5, x, y + 5, fill=CIRCLE, width=2, tags="circle_center")
        canvas.create_rectangle(0, 0, width, height, outline=BORDER)
        if self.sweep_y is not None:
            y = height - self.sweep_y * scale_y
            if 0 <= y <= height:
                canvas.create_line(0, y, width, y, fill=SWEEP, width=2, dash=(8, 4), tags="sweep")
            self._draw_beach_line(self.sweep_y, scale_x, scale_y, height)
        for point in self.points:
            x, y = (point.x - left) * scale_x, (point.y - top) * scale_y
            pending = self.sweep_y is not None and y > height - self.sweep_y * scale_y
            color = PENDING_SITE if pending else NAVY
            canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill=color, outline=WHITE, tags="site")
