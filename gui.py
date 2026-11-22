import math
import random
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from algorithm import FortuneAlgorithm
from data_structures import Point


BACKGROUND = "#eaf2fc"
PANEL = "#f9fcff"
SIDEBAR_STATS = "#e8f1ff"
WHITE = "#ffffff"
NAVY = "#102a4d"
MUTED = "#4d6583"
BORDER = "#c1d3ea"
BLUE = "#215bc6"
EDGE = "#497ac9"
CIRCLE = "#007c9e"
GRID = "#e7effa"
FONT = "Segoe UI"
DEFAULT_BOUNDS = (0, 0, 900, 600)


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
        self.edges = []
        self.circles = []
        self.has_result = False
        self.show_circles = tk.BooleanVar(value=True)
        self.source = tk.StringVar()
        self.status = tk.StringVar()
        self.coordinates = tk.StringVar(value="x —   y —")
        self.range_text = tk.StringVar()

        self._build()
        root.bind("<Control-o>", lambda event: self.open_file())
        root.bind("<F5>", lambda event: self.run())
        self.load_example()

    def _label(self, parent, text="", size=10, color=NAVY, weight="normal", **options):
        return tk.Label(
            parent, text=text, bg=parent["bg"], fg=color, font=(FONT, size, weight),
            **options,
        )

    def _button(self, parent, text, command, primary=False):
        button = tk.Button(
            parent, text=text, command=command, anchor="w", padx=12, pady=7,
            bd=0, relief="flat", cursor="hand2", highlightthickness=1,
            highlightbackground=BLUE if primary else BORDER, highlightcolor=BLUE,
            bg=BLUE if primary else WHITE, fg=WHITE if primary else NAVY,
            activebackground="#194ca8" if primary else "#dfecff",
            activeforeground=WHITE if primary else NAVY, font=(FONT, 10, "bold"),
        )
        button.pack(fill="x", pady=(0, 7))

    def _section(self, parent, title):
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=(11, 10))
        self._label(parent, title, 10, weight="bold").pack(anchor="w", pady=(0, 5))

    def _build(self):
        header = tk.Frame(self.root, bg=NAVY, padx=25, pady=14)
        header.pack(fill="x")
        self._label(header, "GEOMETRI KOMPUTASIONAL  /  TP 2", 9, "#a9cfff", "bold").pack(anchor="w")
        self._label(header, "Diagram Voronoi", 25, WHITE, "bold").pack(anchor="w")

        body = tk.Frame(self.root, bg=BACKGROUND)
        body.pack(fill="both", expand=True, padx=20, pady=(16, 9))
        sidebar = tk.Frame(body, bg=PANEL, padx=14, pady=12, highlightthickness=1, highlightbackground=BORDER)
        sidebar.pack(side="left", fill="y", padx=(0, 14))
        plot = tk.Frame(body, bg=PANEL, padx=14, pady=12, highlightthickness=1, highlightbackground=BORDER)
        plot.pack(side="left", fill="both", expand=True)

        self._label(sidebar, "Input titik", 13, weight="bold").pack(anchor="w", pady=(0, 8))
        self._button(sidebar, "Buka file TXT...", self.open_file)
        self._button(sidebar, "Muat contoh 25 titik", self.load_example)
        self._button(sidebar, "Kosongkan", self.clear)
        self._label(
            sidebar, "Klik kiri untuk tambah titik.\nKlik kanan pada titik untuk hapus.",
            9, MUTED, justify="left", anchor="w",
        ).pack(fill="x")

        self._section(sidebar, "Hasil")
        self._button(sidebar, "Hitung Voronoi", self.run, primary=True)
        counts = tk.Frame(sidebar, bg=SIDEBAR_STATS)
        counts.pack(fill="x", pady=(2, 3))
        self.counts = []
        for index, name in enumerate(("Titik", "Sisi", "Lingkaran")):
            counts.grid_columnconfigure(index, weight=1, uniform="counts")
            cell = tk.Frame(counts, bg=SIDEBAR_STATS, padx=5, pady=5)
            cell.grid(row=0, column=index, sticky="ew")
            number = tk.StringVar(value="—")
            self.counts.append(number)
            self._label(cell, size=14, weight="bold", textvariable=number).pack()
            self._label(cell, name, size=8, color=MUTED).pack()
        self.radius_text = tk.StringVar(value="Radius terbesar  —")
        self._label(sidebar, size=9, color=MUTED, textvariable=self.radius_text).pack(anchor="w", pady=(3, 0))

        self._section(sidebar, "Tampilan")
        toggle = tk.Checkbutton(
            sidebar, text="Tampilkan lingkaran", variable=self.show_circles,
            command=self._draw, bg=PANEL, fg=NAVY, selectcolor=WHITE,
            activebackground=PANEL, activeforeground=NAVY, font=(FONT, 9),
        )
        toggle.pack(anchor="w")

        heading = tk.Frame(plot, bg=PANEL)
        heading.pack(fill="x", pady=(0, 8))
        self._label(heading, "Bidang Voronoi", 15, weight="bold").pack(side="left")
        self._label(heading, size=9, color=MUTED, textvariable=self.range_text).pack(side="right")

        board = tk.Frame(plot, bg="#e1ecfa", highlightthickness=1, highlightbackground=BORDER)
        board.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(board, bg=WHITE, bd=0, highlightthickness=0, cursor="crosshair")
        board.bind("<Configure>", self._fit_canvas)
        self.canvas.bind("<Configure>", self._draw)
        self.canvas.bind("<Button-1>", self.add_point)
        self.canvas.bind("<Button-3>", self.remove_point)
        self.canvas.bind("<Motion>", self._show_coordinates)
        self.canvas.bind("<Leave>", lambda event: self.coordinates.set("x —   y —"))
        self.board = board

        legend = tk.Frame(plot, bg=PANEL)
        legend.pack(fill="x", pady=(8, 0))
        for symbol, name, color in (
            ("●", "Titik", NAVY),
            ("━", "Sisi Voronoi", EDGE),
            ("○", "Lingkaran kosong terbesar", CIRCLE),
        ):
            self._label(legend, symbol, 12, color, "bold").pack(side="left", padx=(0, 4))
            self._label(legend, name, 9, MUTED).pack(side="left", padx=(0, 14))
        self._label(legend, size=9, color=MUTED, textvariable=self.coordinates).pack(side="right")

        footer = tk.Frame(self.root, bg=BACKGROUND, padx=21)
        footer.pack(fill="x", pady=(0, 9))
        self._label(footer, size=9, textvariable=self.status).pack(side="left")
        self._label(footer, size=9, color=MUTED, textvariable=self.source).pack(side="right")

    def _replace_points(self, points, bounds, source):
        self.points = points
        self.bounds = bounds
        self.source.set(source)
        self._fit_canvas()
        self._invalidate_result()

    def load_example(self):
        rng = random.Random(812)
        points = [Point(round(rng.uniform(60, 840)), round(rng.uniform(55, 545))) for _ in range(25)]
        self._replace_points(points, DEFAULT_BOUNDS, "Contoh bawaan")
        self.run()

    def open_file(self):
        filename = filedialog.askopenfilename(
            parent=self.root, title="Buka file titik",
            filetypes=[("File teks", "*.txt"), ("Semua file", "*.*")],
        )
        if not filename:
            return
        try:
            points = read_points(filename)
            bounds = bounds_for(points)
        except (OSError, ValueError) as exc:
            messagebox.showerror("File titik gagal dibuka", str(exc), parent=self.root)
            return
        self._replace_points(points, bounds, Path(filename).name)
        self.run()

    def clear(self):
        self._replace_points([], DEFAULT_BOUNDS, "Input mouse")

    def _fit_canvas(self, event=None):
        width = max(1, self.board.winfo_width() - 22)
        height = max(1, self.board.winfo_height() - 22)
        left, top, right, bottom = self.bounds
        aspect = (right - left) / (bottom - top)
        canvas_width = max(1, min(width, round(height * aspect)))
        canvas_height = max(1, min(height, round(width / aspect)))
        self.canvas.place(
            relx=0.5, rely=0.5, anchor="center", width=canvas_width, height=canvas_height,
        )
        self.range_text.set(f"x [{left:.4g}, {right:.4g}]     y [{top:.4g}, {bottom:.4g}]")

    def _geometry(self):
        left, top, right, bottom = self.bounds
        width = max(1, self.canvas.winfo_width() - 1)
        height = max(1, self.canvas.winfo_height() - 1)
        return left, top, width / (right - left), height / (bottom - top)

    def _point_at(self, event):
        left, top, scale_x, scale_y = self._geometry()
        return Point(left + event.x / scale_x, top + event.y / scale_y)

    def _show_coordinates(self, event):
        point = self._point_at(event)
        self.coordinates.set(f"x {point.x:.4g}   y {point.y:.4g}")

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
            self.points.append(self._point_at(event))
            self.source.set("Input diedit lewat mouse")
            self._invalidate_result()

    def remove_point(self, event):
        index = self._nearest_index(event, tolerance=10)
        if index is not None:
            del self.points[index]
            self.source.set("Input diedit lewat mouse")
            self._invalidate_result()

    def _invalidate_result(self):
        self.edges = []
        self.circles = []
        self.has_result = False
        if len(self.points) < 2:
            self.status.set("Tambahkan minimal dua titik untuk menghitung diagram.")
        else:
            self.status.set("Titik siap. Klik Hitung Voronoi atau tekan F5.")
        self._update_counts()
        self._draw()

    def run(self):
        if len(self.points) < 2:
            self._invalidate_result()
            return
        left, top, right, bottom = self.bounds
        # The existing algorithm clips to a box starting at (0, 0).
        sites = [Point(point.x - left, point.y - top) for point in self.points]
        algorithm = FortuneAlgorithm(sites, right - left, bottom - top)
        try:
            algorithm.process()
            # Ignore collapsed segments and overlapping copies of the same circle.
            self.edges = [
                (start, end) for start, end in algorithm.get_clipped_edges()
                if math.hypot(end.x - start.x, end.y - start.y) > 1e-7
            ]
            self.circles = []
            for center, radius in algorithm.get_largest_empty_circles():
                if not any(
                    math.hypot(center.x - other.x, center.y - other.y) < 1e-5
                    and abs(radius - other_radius) < 1e-5
                    for other, other_radius in self.circles
                ):
                    self.circles.append((center, radius))
        except ArithmeticError:
            self._invalidate_result()
            self.status.set("Perhitungan gagal untuk koordinat ini.")
            return
        self.has_result = True
        if not self.edges:
            self.status.set("Algoritma Fortune tidak menghasilkan sisi yang bisa digambar.")
        elif not self.circles:
            self.status.set("Perhitungan selesai. Tidak ada lingkaran kosong yang ditemukan.")
        else:
            self.status.set("Perhitungan selesai.")
        self._update_counts()
        self._draw()

    def _update_counts(self):
        self.counts[0].set(len(self.points))
        self.counts[1].set(len(self.edges) if self.has_result else "—")
        self.counts[2].set(len(self.circles) if self.has_result else "—")
        radius = max((radius for _, radius in self.circles), default=None)
        radius_label = "—" if radius is None else f"{radius:.4g}"
        self.radius_text.set(f"Radius terbesar  {radius_label}")

    def _draw(self, event=None):
        canvas = self.canvas
        canvas.delete("all")
        left, top, scale_x, scale_y = self._geometry()
        width = canvas.winfo_width() - 1
        height = canvas.winfo_height() - 1
        if width < 2 or height < 2:
            return
        for index in range(1, 12):
            x = width * index / 12
            canvas.create_line(x, 0, x, height, fill=GRID)
        for index in range(1, 8):
            y = height * index / 8
            canvas.create_line(0, y, width, y, fill=GRID)
        for start, end in self.edges:
            canvas.create_line(
                start.x * scale_x, start.y * scale_y, end.x * scale_x, end.y * scale_y,
                fill=EDGE, width=2, tags="edge",
            )
        if self.show_circles.get():
            for center, radius in self.circles:
                x, y = center.x * scale_x, center.y * scale_y
                rx, ry = radius * scale_x, radius * scale_y
                canvas.create_oval(x - rx, y - ry, x + rx, y + ry, outline=CIRCLE,
                                   width=3, dash=(7, 4), tags="circle")
                canvas.create_line(x - 5, y, x + 5, y, fill=CIRCLE, width=2, tags="circle_center")
                canvas.create_line(x, y - 5, x, y + 5, fill=CIRCLE, width=2, tags="circle_center")
        for point in self.points:
            x, y = (point.x - left) * scale_x, (point.y - top) * scale_y
            canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill=NAVY, outline=WHITE, tags="site")
        canvas.create_rectangle(0, 0, width, height, outline=BORDER)
        if not self.points:
            canvas.create_text(width / 2, height / 2, text="Klik bidang untuk menambah titik pertama",
                               font=(FONT, 11), fill=MUTED)
