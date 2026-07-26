import tkinter as tk
from collections import defaultdict

from graph import GraphHandler
from models import Zone, ZoneTypes


class VisualizerUnavailableError(RuntimeError):
    """Raised when tkinter cannot create a graphical window."""


class Visualizer:
    """Draw a static representation of a Fly-in graph."""

    ZONE_COLORS = {
        ZoneTypes.Normal: "#3b82f6",
        ZoneTypes.Restricted: "#f97316",
        ZoneTypes.Priority: "#22c55e",
        ZoneTypes.Blocked: "#6b7280",
    }

    def __init__(
        self,
        graph: GraphHandler,
        width: int | None = None,
        height: int | None = None,
        margin: int = 110,
    ) -> None:
        self.graph = graph
        self.margin = margin
        self.zone_radius = 27
        self.coordinate_spacing_x = 150
        self.coordinate_spacing_y = 120
        self.zoom_level = 1.0

        try:
            self.root = tk.Tk()
        except tk.TclError as err:
            raise VisualizerUnavailableError(str(err)) from err

        self.root.title("Fly-in Map Visualizer")
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        available_width = int(screen_width * 0.92)
        available_height = int(screen_height * 0.88)
        window_width = (
            available_width
            if width is None
            else min(width, available_width)
        )
        window_height = (
            available_height
            if height is None
            else min(height, available_height)
        )
        self.width = window_width
        self.height = window_height
        window_x = max(0, (screen_width - window_width) // 2)
        window_y = max(0, (screen_height - window_height) // 2)
        self.root.geometry(
            f"{window_width}x{window_height}+{window_x}+{window_y}"
        )
        self.root.minsize(
            min(900, window_width),
            min(600, window_height),
        )

        canvas_frame = tk.Frame(self.root, bg="#0f172a")
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(
            canvas_frame,
            width=self.width,
            height=self.height,
            bg="#0f172a",
            highlightthickness=0,
            xscrollincrement=1,
            yscrollincrement=1,
        )
        horizontal_scrollbar = tk.Scrollbar(
            canvas_frame,
            orient=tk.HORIZONTAL,
            command=self.canvas.xview,
        )
        vertical_scrollbar = tk.Scrollbar(
            canvas_frame,
            orient=tk.VERTICAL,
            command=self.canvas.yview,
        )
        self.canvas.configure(
            xscrollcommand=horizontal_scrollbar.set,
            yscrollcommand=vertical_scrollbar.set,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vertical_scrollbar.grid(row=0, column=1, sticky="ns")
        horizontal_scrollbar.grid(row=1, column=0, sticky="ew")
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        self.status = tk.Label(
            self.root,
            text=(
                "Mouse wheel: zoom  |  Middle/right drag: pan  |  "
                "Click a zone: details"
            ),
            bg="#1e293b",
            fg="#e2e8f0",
            anchor="w",
            padx=10,
            pady=6,
        )
        self.status.pack(fill=tk.X)
        self.positions = self.normalize_positions()
        self.bind_navigation()

    def normalize_positions(self) -> dict[str, tuple[float, float]]:
        """Lay out coordinates with a readable minimum separation."""
        zones = list(self.graph.zones.values())
        unique_x = sorted({zone.x for zone in zones})
        unique_y = sorted({zone.y for zone in zones})
        x_index = {value: index for index, value in enumerate(unique_x)}
        y_index = {value: index for index, value in enumerate(unique_y)}
        same_coordinates: defaultdict[tuple[int, int], list[Zone]] = (
            defaultdict(list)
        )
        for zone in zones:
            same_coordinates[(zone.x, zone.y)].append(zone)

        self.virtual_width = max(
            self.width,
            (2 * self.margin)
            + max(1, len(unique_x) - 1) * self.coordinate_spacing_x,
        )
        self.virtual_height = max(
            self.height,
            (2 * self.margin)
            + max(1, len(unique_y) - 1) * self.coordinate_spacing_y,
        )
        content_width = max(0, len(unique_x) - 1) * self.coordinate_spacing_x
        content_height = max(0, len(unique_y) - 1) * self.coordinate_spacing_y
        origin_x = (self.virtual_width - content_width) / 2
        origin_y = (self.virtual_height - content_height) / 2
        positions: dict[str, tuple[float, float]] = {}

        for zone in zones:
            if len(unique_x) == 1:
                canvas_x = self.virtual_width / 2
            else:
                canvas_x = (
                    origin_x
                    + x_index[zone.x] * self.coordinate_spacing_x
                )

            if len(unique_y) == 1:
                canvas_y = self.virtual_height / 2
            else:
                canvas_y = (
                    origin_y
                    + y_index[zone.y] * self.coordinate_spacing_y
                )

            duplicates = same_coordinates[(zone.x, zone.y)]
            if len(duplicates) > 1:
                duplicate_index = duplicates.index(zone)
                canvas_x += (duplicate_index % 3 - 1) * 38
                canvas_y += (duplicate_index // 3) * 62

            positions[zone.name] = (canvas_x, canvas_y)

        return positions

    def bind_navigation(self) -> None:
        """Bind zooming and canvas panning controls."""
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)
        self.canvas.bind("<ButtonPress-2>", self.start_pan)
        self.canvas.bind("<B2-Motion>", self.pan)
        self.canvas.bind("<ButtonPress-3>", self.start_pan)
        self.canvas.bind("<B3-Motion>", self.pan)

    def on_mouse_wheel(self, event: tk.Event) -> None:
        """Zoom the drawing around the mouse pointer."""
        zoom_in = event.num == 4 or event.delta > 0
        factor = 1.12 if zoom_in else 1 / 1.12
        next_zoom = self.zoom_level * factor
        if not 0.35 <= next_zoom <= 4.0:
            return

        mouse_x = self.canvas.canvasx(event.x)
        mouse_y = self.canvas.canvasy(event.y)
        self.canvas.scale("all", mouse_x, mouse_y, factor, factor)
        self.zoom_level = next_zoom
        self.update_scroll_region()

    def start_pan(self, event: tk.Event) -> None:
        """Record the starting point for a canvas drag."""
        self.canvas.scan_mark(event.x, event.y)

    def pan(self, event: tk.Event) -> None:
        """Pan the virtual canvas while dragging."""
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def update_scroll_region(self) -> None:
        """Update scroll limits to contain all currently drawn items."""
        bounds = self.canvas.bbox("all")
        if bounds is not None:
            padding = 70
            self.canvas.configure(
                scrollregion=(
                    bounds[0] - padding,
                    bounds[1] - padding,
                    bounds[2] + padding,
                    bounds[3] + padding,
                )
            )

    def get_zone_color(self, zone: Zone) -> str:
        """Return a safe display color for a zone."""
        if zone.key == "start_hub":
            return "#16a34a"
        if zone.key == "end_hub":
            return "#eab308"

        if zone.metadata.color is not None:
            try:
                self.root.winfo_rgb(zone.metadata.color)
                return zone.metadata.color
            except tk.TclError:
                pass

        return self.ZONE_COLORS[zone.metadata.zone]

    def draw_connections(self) -> None:
        """Draw every graph connection below the zones."""
        for connection in self.graph.connection.values():
            from_x, from_y = self.positions[connection.from_]
            to_x, to_y = self.positions[connection.to]
            self.canvas.create_line(
                from_x,
                from_y,
                to_x,
                to_y,
                fill="#64748b",
                width=3,
            )
            if connection.metadata.max_link_capacity > 1:
                self.canvas.create_text(
                    (from_x + to_x) / 2,
                    ((from_y + to_y) / 2) - 10,
                    text=f"cap {connection.metadata.max_link_capacity}",
                    fill="#cbd5e1",
                    font=("TkDefaultFont", 9),
                )

    def draw_zones(self) -> None:
        """Draw zones with their names, types, and capacities."""
        radius = self.zone_radius
        for zone in self.graph.zones.values():
            x, y = self.positions[zone.name]
            zone_tag = f"zone:{zone.name}"
            self.canvas.create_oval(
                x - radius,
                y - radius,
                x + radius,
                y + radius,
                fill=self.get_zone_color(zone),
                outline="#f8fafc",
                width=2,
                tags=(zone_tag, "zone"),
            )
            self.canvas.create_text(
                x,
                y,
                text=zone.name,
                fill="#ffffff",
                font=("TkDefaultFont", 10, "bold"),
                tags=(zone_tag, "zone"),
            )

            if zone.key in {"start_hub", "end_hub"}:
                detail = zone.key.replace("_hub", "") + " · unlimited"
            else:
                detail = (
                    f"{zone.metadata.zone.value} · "
                    f"cap {zone.metadata.max_drones}"
                )
            if len(self.graph.zones) <= 20 or zone.key != "hub":
                self.canvas.create_text(
                    x,
                    y + radius + 16,
                    text=detail,
                    fill="#e2e8f0",
                    font=("TkDefaultFont", 9),
                    tags=(zone_tag, "zone"),
                )

            def show_details(
                _event: tk.Event[tk.Misc],
                selected: Zone = zone,
            ) -> None:
                self.show_zone_details(selected)

            self.canvas.tag_bind(
                zone_tag,
                "<Button-1>",
                show_details,
            )

    def show_zone_details(self, zone: Zone) -> None:
        """Show complete zone metadata in the status bar."""
        capacity = (
            "unlimited"
            if zone.key in {"start_hub", "end_hub"}
            else str(zone.metadata.max_drones)
        )
        self.status.configure(
            text=(
                f"{zone.name}  |  {zone.key}  |  "
                f"type={zone.metadata.zone.value}  |  "
                f"coordinates=({zone.x}, {zone.y})  |  "
                f"capacity={capacity}"
            )
        )

    def draw(self) -> None:
        """Draw the complete static map."""
        self.canvas.delete("all")
        self.draw_connections()
        self.draw_zones()
        self.canvas.configure(
            scrollregion=(0, 0, self.virtual_width, self.virtual_height)
        )
        self.update_scroll_region()

    def run(self) -> None:
        """Draw the map and start tkinter's event loop."""
        self.draw()
        self.root.mainloop()
