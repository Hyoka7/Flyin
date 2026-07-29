from __future__ import annotations

import math

import pygame

from graph import GraphHandler
from models import (
    DroneSnapshot,
    DroneState,
    TurnSnapshot,
    Zone,
    ZoneTypes,
)
from simulator import Simulator


class PygameVisualizer:
    """Animate turn snapshots using a 60 FPS Pygame loop."""

    BACKGROUND = (15, 23, 42)
    FOREGROUND = (241, 245, 249)
    CONNECTION = (100, 116, 139)
    ZONE_COLORS = {
        ZoneTypes.Normal: (59, 130, 246),
        ZoneTypes.Restricted: (249, 115, 22),
        ZoneTypes.Priority: (34, 197, 94),
        ZoneTypes.Blocked: (107, 114, 128),
    }

    def __init__(
        self,
        graph: GraphHandler,
        simulator: Simulator,
    ) -> None:
        self.graph = graph
        self.simulator = simulator
        pygame.init()
        display = pygame.display.Info()
        self.width = max(900, int(display.current_w * 0.9))
        self.height = max(600, int(display.current_h * 0.85))
        self.screen = pygame.display.set_mode(
            (self.width, self.height),
            pygame.RESIZABLE,
        )
        pygame.display.set_caption("Fly-in Pygame Visualizer")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 22)
        self.small_font = pygame.font.Font(None, 17)
        self.positions: dict[str, pygame.Vector2] = {}
        self.rebuild_positions()

        self.timeline = self.build_timeline()
        self.timeline_index = 0
        self.previous = self.timeline[0]
        self.current = self.timeline[0]
        self.animation_elapsed = 0.0
        self.animation_duration = 0.55
        self.animating = False
        self.playing = False
        self.running = True

    def build_timeline(self) -> list[TurnSnapshot]:
        """Run the simulation once and retain every snapshot."""
        timeline = [self.simulator.get_snapshot()]
        while not timeline[-1].finished and not timeline[-1].deadlocked:
            timeline.append(self.simulator.step())
        return timeline

    def rebuild_positions(self) -> None:
        """Fit source coordinates into the current window."""
        zones = list(self.graph.zones.values())
        min_x = min(zone.x for zone in zones)
        max_x = max(zone.x for zone in zones)
        min_y = min(zone.y for zone in zones)
        max_y = max(zone.y for zone in zones)
        padding = 110
        draw_width = max(1, self.width - 2 * padding)
        draw_height = max(1, self.height - 2 * padding)
        x_span = max(1, max_x - min_x)
        y_span = max(1, max_y - min_y)
        self.positions = {
            zone.name: pygame.Vector2(
                padding + (zone.x - min_x) / x_span * draw_width,
                padding + (zone.y - min_y) / y_span * draw_height,
            )
            for zone in zones
        }

    def get_zone_color(self, zone: Zone) -> pygame.Color:
        """Resolve configured colors with a safe fallback."""
        if zone.metadata.color is not None:
            try:
                return pygame.Color(zone.metadata.color)
            except ValueError:
                pass
        if zone.key == "start_hub":
            return pygame.Color("#16a34a")
        if zone.key == "end_hub":
            return pygame.Color("#eab308")
        return pygame.Color(self.ZONE_COLORS[zone.metadata.zone])

    def snapshot_position(
        self,
        drone: DroneSnapshot,
    ) -> pygame.Vector2:
        """Map a drone snapshot to a zone or connection midpoint."""
        if (
            drone.state == DroneState.IN_TRANSIT
            and drone.transit_from is not None
            and drone.transit_to is not None
        ):
            start = self.positions[drone.transit_from]
            end = self.positions[drone.transit_to]
            position = start.lerp(end, 0.5)
        else:
            position = self.positions[drone.zone or self.graph.start].copy()

        column = (drone.drone_id - 1) % 5 - 2
        row = ((drone.drone_id - 1) // 5) % 5 - 2
        position += pygame.Vector2(column * 9, row * 9)
        return position

    def begin_turn(self) -> None:
        """Move to the next stored turn and begin interpolation."""
        if self.animating:
            return
        if self.timeline_index >= len(self.timeline) - 1:
            self.playing = False
            return
        self.previous = self.current
        self.timeline_index += 1
        self.current = self.timeline[self.timeline_index]
        self.animation_elapsed = 0.0
        self.animating = True

    def previous_turn(self) -> None:
        """Move to the preceding stored turn with reverse animation."""
        if self.animating or self.timeline_index == 0:
            return
        self.playing = False
        self.previous = self.current
        self.timeline_index -= 1
        self.current = self.timeline[self.timeline_index]
        self.animation_elapsed = 0.0
        self.animating = True

    def reset(self) -> None:
        """Return immediately to the initial stored turn."""
        self.playing = False
        self.animating = False
        self.timeline_index = 0
        self.previous = self.timeline[0]
        self.current = self.timeline[0]
        self.animation_elapsed = 0.0

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle playback, stepping, speed, resize, and quit controls."""
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.VIDEORESIZE:
            self.width, self.height = event.size
            self.screen = pygame.display.set_mode(
                event.size,
                pygame.RESIZABLE,
            )
            self.rebuild_positions()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.playing = not self.playing
            elif event.key == pygame.K_RIGHT:
                self.begin_turn()
            elif event.key == pygame.K_LEFT:
                self.previous_turn()
            elif event.key == pygame.K_r:
                self.reset()
            elif event.key == pygame.K_UP:
                self.animation_duration = max(
                    0.15,
                    self.animation_duration - 0.1,
                )
            elif event.key == pygame.K_DOWN:
                self.animation_duration = min(
                    2.0,
                    self.animation_duration + 0.1,
                )
            elif event.key == pygame.K_ESCAPE:
                self.running = False

    def update(self, elapsed: float) -> None:
        """Advance animation time and trigger automatic turns."""
        if self.animating:
            self.animation_elapsed += elapsed
            if self.animation_elapsed >= self.animation_duration:
                self.animation_elapsed = self.animation_duration
                self.animating = False
        elif self.playing:
            self.begin_turn()

    def draw_connections(self) -> None:
        """Draw graph connections and their capacities."""
        for connection in self.graph.connection.values():
            start = self.positions[connection.from_]
            end = self.positions[connection.to]
            pygame.draw.line(
                self.screen,
                self.CONNECTION,
                start,
                end,
                3,
            )
            if connection.metadata.max_link_capacity > 1:
                center = start.lerp(end, 0.5)
                label = self.small_font.render(
                    f"cap {connection.metadata.max_link_capacity}",
                    True,
                    self.FOREGROUND,
                )
                self.screen.blit(label, center + pygame.Vector2(5, -18))

    def draw_zones(self) -> None:
        """Draw zones over graph connections."""
        for zone in self.graph.zones.values():
            position = self.positions[zone.name]
            pygame.draw.circle(
                self.screen,
                self.get_zone_color(zone),
                position,
                27,
            )
            pygame.draw.circle(
                self.screen,
                self.FOREGROUND,
                position,
                27,
                2,
            )
            label = self.small_font.render(
                zone.name,
                True,
                self.FOREGROUND,
            )
            rect = label.get_rect(center=(position.x, position.y - 37))
            self.screen.blit(label, rect)

    def draw_drones(self) -> None:
        """Interpolate and draw every drone between turn snapshots."""
        previous = {drone.drone_id: drone for drone in self.previous.drones}
        if self.animating:
            raw_progress = self.animation_elapsed / self.animation_duration
            progress = raw_progress * raw_progress * (3 - 2 * raw_progress)
        else:
            progress = 1.0

        for drone in self.current.drones:
            old = previous.get(drone.drone_id, drone)
            start = self.snapshot_position(old)
            end = self.snapshot_position(drone)
            position = start.lerp(end, progress)
            color = (
                pygame.Color("#facc15")
                if drone.state == DroneState.IN_TRANSIT
                else pygame.Color("#f8fafc")
            )
            pygame.draw.circle(self.screen, color, position, 9)
            pygame.draw.circle(self.screen, self.BACKGROUND, position, 9, 1)
            number = self.small_font.render(
                str(drone.drone_id),
                True,
                self.BACKGROUND,
            )
            self.screen.blit(number, number.get_rect(center=position))

    def draw_status(self) -> None:
        """Draw controls and the current simulation state."""
        speed = 1 / self.animation_duration
        mode = "playing" if self.playing else "paused"
        status = f"Turn {self.current.turn}  |  {mode}  |  speed {speed:.1f}x"
        if self.current.finished:
            status += "  |  all drones delivered"
        elif self.current.deadlocked:
            status += "  |  deadlock"
        controls = (
            "Space: play/pause   Right: next   Left: previous   "
            "R: reset   Up/Down: speed   Esc: quit"
        )
        self.screen.blit(
            self.font.render(status, True, self.FOREGROUND),
            (14, 12),
        )
        self.screen.blit(
            self.small_font.render(controls, True, self.FOREGROUND),
            (14, 38),
        )
        if self.current.moves:
            move_text = "  ".join(self.current.moves)
            max_chars = max(20, math.floor(self.width / 9))
            self.screen.blit(
                self.small_font.render(
                    move_text[:max_chars],
                    True,
                    self.FOREGROUND,
                ),
                (14, self.height - 25),
            )

    def draw(self) -> None:
        """Draw one animation frame."""
        self.screen.fill(self.BACKGROUND)
        self.draw_connections()
        self.draw_zones()
        self.draw_drones()
        self.draw_status()
        pygame.display.flip()

    def run(self) -> None:
        """Run the visualizer until its window is closed."""
        while self.running:
            elapsed = self.clock.tick(60) / 1000
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(elapsed)
            self.draw()
        pygame.quit()
