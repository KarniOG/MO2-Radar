import math
import pyglet
from pyglet import shapes
from pyglet.graphics import Group
from pyglet.text.layout import TextLayout
from lib.common import config


# controls the order in which objects are drawn
# without this, the depth of actor markers will be based on
# when they were created, which can hide important information.
lowest = Group(0)
verylow = Group(1)
low = Group(2)
normal = Group(3)
high = Group(4)
veryhigh = Group(5)
highest = Group(6)


def make_view_matrix(
    cam_pos: tuple[float, ...], cam_rotation: tuple[float, ...]
) -> tuple[tuple[float, ...], ...]:
    """return view matrix for an orthographic "plan" camera"""
    # if you want to make an ESP, it's much easier
    # to understand by starting with two dimensions
    radyaw = math.radians(cam_rotation[1])
    sinyaw = math.sin(radyaw)
    cosyaw = math.cos(radyaw)
    # swap camera x and y so we can use the same view matrix
    # for rotating the compass and game objects
    y, x = cam_pos[0:2]
    # store our rotated position which will be subtracted
    # from object positions later
    vx = x * cosyaw - y * sinyaw
    vy = x * sinyaw + y * cosyaw
    return (
        # x axis
        (cosyaw, -sinyaw, -vx),
        # y axis
        (sinyaw, cosyaw, -vy),
        # w or scale
        # this would be the cross products but it's orthogonal I guess
        (0, 0, Radar.RANGE / Radar.RADIUS),
    )


class RadarObject:
    """
    generic radar object with methods for
    transformations and elevation-based alpha
    """

    def world_to_screen(
        self,
        obj_pos: tuple[float, ...],
        view_matrix: tuple[tuple[float, ...], ...],
        _round=False,
    ) -> tuple[float, float]:
        """
        apply orthographic projection transformation
        to coordinates and return screen position
        """

        # swap axes so we can use the "correct" rotation matrix
        obj_y, obj_x = obj_pos[0:2]

        # rotate + subtract camera position
        x = obj_x * view_matrix[0][0] + obj_y * view_matrix[0][1] + view_matrix[0][2]
        y = obj_x * view_matrix[1][0] + obj_y * view_matrix[1][1] + view_matrix[1][2]
        # w = x * view[2][0] + y * view[2][1] + view[2][2]
        # norm = 1 / w
        norm = 1 / view_matrix[2][2]
        # scale to radar size and place on radar
        screen_x = Radar.CENTER[0] + x * norm
        screen_y = Radar.CENTER[1] + y * norm

        if _round:
            return round(screen_x), round(screen_y)
        return screen_x, screen_y

    def get_alpha(self, elevation: float) -> int:
        """
        return an alpha value based on elevation that can be used to make
        distant markers more transparent. useful for visualizing 3D position
        on a 2D radar.
        """
        # 85 alpha at >45m difference but maintain 255 alpha if elevation < 5m
        min_alpha = 85
        ceiling = 4500
        threshold = 500
        raw_alpha = 255 - (
            (abs(elevation) - threshold) * ((255 - min_alpha) / (ceiling - threshold))
        )
        # round to nearest multiple of 5 to slightly reduce label updates
        inc = 5
        alpha = round(raw_alpha / inc) * inc
        # clamp values
        return min(255, max(min_alpha, alpha))


class GameObject(RadarObject):
    """labelled radar object for ingame actors"""

    __slots__ = "label", "actor"

    def __init__(self, actor, group: Group):
        super().__init__()
        self.actor = actor

        doc = pyglet.text.document.FormattedDocument(" ")
        doc.set_style(
            0,
            1,
            attributes={
                "font_name": "DejaVu Sans",
                "color": (255, 255, 255, 255),
                "align": "center",
            },
        )

        self.label = TextLayout(doc, batch=Radar.BATCH, group=group)
        # we don't know how wide the label will be
        # so let's just make it big.
        self.label.width = 240
        self.label.multiline = True
        self.label.anchor_x = "center"
        self.label.anchor_y = "bottom"

    def update_label(self, text: str, font_sizes: tuple[int], alpha: int):
        """Update label text and alpha if necessary"""
        # updating labels is the most expensive operation
        # we perform by far. I tried really hard to optimize it
        # but in crowded areas the radar might lag a little.

        text_changed = text not in (self.label.document.text, "")
        alpha_changed = alpha != self.label.document.get_style("color")[3]
        if not (text_changed or alpha_changed):
            return

        if alpha_changed:
            # it's actually faster to do this outside the label update?
            self.label.document.set_style(
                0,
                len(self.label.document.text),
                {"color": (255, 255, 255, alpha)},
            )

        if text_changed:
            self.label.begin_update()  # very important
            self.write_label(text, font_sizes)
            self.label.end_update()

    def write_label(self, text: str, font_sizes: tuple[int]):
        """
        Write out a label of n lines using font_sizes to set the size of each line.
        """
        lines = text.splitlines()

        self.label.document.delete_text(0, len(self.label.document.text))
        self.label.document.insert_text(0, lines[0], {"font_size": font_sizes[0]})
        for i in range(1, len(lines)):
            # a trailing newline sets the height of the next row to the current font size
            # so we need to *start* additional lines with newline or they'll be too tall
            self.label.document.insert_text(
                len(self.label.document.text),
                "\n" + lines[i],
                {"font_size": font_sizes[i]},
            )

    def elevation_string(self, elevation: float) -> str:
        """return a string that indicates elevation difference"""
        if abs(elevation) < 450:
            # hide elevation if target is at the same level as you
            # return "\n "  # uncomment this to increase label FPS. probably.
            return ""
        if elevation < 0:
            return f"\n▾ {round(abs(elevation)/100)}m"
        return f"\n▴ {round(elevation/100)}m"


class Radar(RadarObject):
    BATCH = pyglet.graphics.Batch()
    RADIUS = config["window_size"] / 2
    CENTER = (RADIUS, RADIUS)
    RANGE = config["max_range"]

    __slots__ = "compass", "rings", "static"

    def __init__(self):
        super().__init__()
        # these don't need a group since the radar should be created before
        # any actors are loaded and the components are added in the right order.
        bg = shapes.Circle(
            x=Radar.CENTER[0],
            y=Radar.CENTER[1],
            radius=Radar.RADIUS,
            color=(85, 85, 85, 170),
            batch=Radar.BATCH,
        )

        fov_angle = math.radians(110)
        fov = shapes.Sector(
            x=Radar.CENTER[0],
            y=Radar.CENTER[1],
            radius=Radar.RADIUS,
            angle=fov_angle,
            start_angle=math.pi / 2 - fov_angle / 2,
            color=(85, 85, 85, 85),
            batch=Radar.BATCH,
        )

        self.build_rings()
        self.compass = Compass()

        # red line indicating the center of your FOV
        facing = shapes.Line(
            x=Radar.CENTER[0],
            y=Radar.CENTER[1],
            x2=Radar.CENTER[0],
            y2=Radar.CENTER[1] + Radar.RADIUS,
            width=1,
            color=(170, 0, 0, 255),
            batch=Radar.BATCH,
        )
        # prevent GC
        self.static = bg, fov, facing

    def build_rings(self):
        """create radar rings that indicate specific ranges"""
        self.rings = []
        # name range, load-in range, unload range
        ranges = (4500, 15000, 20000)
        for r in ranges:
            if r >= Radar.RANGE:
                continue
            ring = shapes.Arc(
                x=Radar.CENTER[0],
                y=Radar.CENTER[1],
                radius=Radar.RADIUS * (r / Radar.RANGE),
                color=(170, 170, 170, 85),
                batch=Radar.BATCH,
            )
            self.rings.append(ring)


class Compass(RadarObject):
    __slots__ = "directions", "north"

    def __init__(self):
        super().__init__()
        self.build_compass()
        # north indicator
        self.north = shapes.Triangle(
            x=Radar.CENTER[0],
            y=Radar.CENTER[1],
            x2=Radar.CENTER[0] + 16,
            y2=Radar.CENTER[1] + 8,
            x3=Radar.CENTER[0] + 16,
            y3=Radar.CENTER[1] - 8,
            color=(170, 0, 0, 255),
            batch=Radar.BATCH,
        )
        # make it rotate around the center
        self.north.anchor_position = (Radar.CENTER[1], 0)

    def rotate_compass(self, view_matrix):
        """transform compass lines to follow camera yaw"""
        # calculate original yaw so we can directly set
        # the rotation of the north marker
        yaw = math.atan2(view_matrix[1][0], view_matrix[1][1])
        self.north.rotation = math.degrees(-yaw)
        for d in self.directions:
            # use view matrix to apply a rotation transformation
            # to each compass line
            new_x = d["x"] * view_matrix[0][0] + d["y"] * view_matrix[0][1]
            new_y = d["x"] * view_matrix[1][0] + d["y"] * view_matrix[1][1]

            new_x2 = d["x2"] * view_matrix[0][0] + d["y2"] * view_matrix[0][1]
            new_y2 = d["x2"] * view_matrix[1][0] + d["y2"] * view_matrix[1][1]

            d["line"].x = Radar.CENTER[0] + new_x
            d["line"].y = Radar.CENTER[1] + new_y
            d["line"].x2 = Radar.CENTER[0] + new_x2
            d["line"].y2 = Radar.CENTER[1] + new_y2

    def build_compass(self):
        """generate lines indicating cardinal + ordinal directions"""
        # ordinal line length
        ordinal = Radar.RADIUS * math.sin(math.pi / 4)
        self.directions = (
            # N-S
            {
                "x": 0,
                "y": -Radar.RADIUS,
                "x2": 0,
                "y2": Radar.RADIUS,
            },
            # E-W
            {
                "x": -Radar.RADIUS,
                "y": 0,
                "x2": Radar.RADIUS,
                "y2": 0,
            },
            # NE
            {
                "x": ordinal / 2,
                "y": ordinal / 2,
                "x2": ordinal,
                "y2": ordinal,
            },
            # SE
            {
                "x": ordinal / 2,
                "y": -ordinal / 2,
                "x2": ordinal,
                "y2": -ordinal,
            },
            # SW
            {
                "x": -ordinal / 2,
                "y": -ordinal / 2,
                "x2": -ordinal,
                "y2": -ordinal,
            },
            # NW
            {
                "x": -ordinal / 2,
                "y": ordinal / 2,
                "x2": -ordinal,
                "y2": ordinal,
            },
        )

        for d in self.directions:
            line = shapes.Line(
                d["x"] + Radar.CENTER[0],
                d["y"] + Radar.CENTER[1],
                d["x2"] + Radar.CENTER[0],
                d["y2"] + Radar.CENTER[1],
                width=1,
                color=(170, 170, 170, 85),
                batch=Radar.BATCH,
            )
            d["line"] = line


class PlayerBlip(GameObject):
    """player icon that shows health as a circle"""

    RADIUS = 5
    # name, elevation
    FONT_SIZES = (10, 7)

    __slots__ = "hp", "damage"

    def __init__(self, actor):
        super().__init__(actor, highest)
        self.hp = shapes.Sector(
            x=0,
            y=0,
            radius=PlayerBlip.RADIUS,
            start_angle=math.pi / 2,
            color=(0, 170, 0, 255),
            batch=Radar.BATCH,
            group=low,
        )
        self.damage = shapes.Sector(
            x=0,
            y=0,
            radius=PlayerBlip.RADIUS,
            angle=0,
            start_angle=math.pi / 2,
            color=(170, 0, 0, 255),
            batch=Radar.BATCH,
            group=low,
        )

    def delete(self):
        self.hp.delete()
        self.damage.delete()
        self.label.delete()

    def update(self, your_pos: tuple[float, float, float], view_matrix):
        # get the latest actor info
        self.actor.update_actor_state()

        screen_x, screen_y = self.world_to_screen(self.actor.pos, view_matrix)
        self.hp.x = screen_x
        self.hp.y = screen_y
        self.damage.x = screen_x
        self.damage.y = screen_y
        self.label.x = screen_x
        self.label.y = screen_y + PlayerBlip.RADIUS + 8

        elevation = self.actor.pos[2] - your_pos[2]

        alpha = self.get_alpha(elevation)
        if self.actor.is_ghost:
            # make ghosts black
            self.hp.color = (0, 0, 0, alpha)
            self.damage.color = (0, 0, 0, alpha)
        else:
            self.hp.color = (0, 170, 0, alpha)
            self.damage.color = (170, 0, 0, alpha)

            # adjust indicator to show health
            try:
                health_pct = self.actor.health[0] / self.actor.health[1]
            except ZeroDivisionError:
                health_pct = 0
            angle = min(math.tau, max(0, health_pct * math.tau))
            self.hp.angle = angle
            self.damage.angle = math.tau - angle
            self.damage.start_angle = math.pi / 2 + angle

        readable_elevation = self.elevation_string(elevation)

        new_label = f"{self.actor.name}{readable_elevation}"

        self.update_label(new_label, PlayerBlip.FONT_SIZES, alpha)


class NPCBlip(GameObject):
    """a diamond marker for NPCs that can optionally show health"""

    MARKER_SIZE = 5
    # name, health/elevation
    FONT_SIZES = (8, 7, 7)

    __slots__ = "marker", "show_health", "y_offset"

    def __init__(self, actor):
        super().__init__(actor, veryhigh)
        self.show_health = any(npc in actor.fname for npc in config["show_health"])
        self.y_offset = 10

        if any(mount in actor.fname for mount in config["invert_label"]):
            self.y_offset = -self.y_offset
            self.label.anchor_y = "top"

        # a yellow diamond
        # this is in the veryhigh group because I want it to be
        # visible above player markers so it's easy to tell if
        # they're riding a mount or not.
        self.marker = shapes.Rectangle(
            x=0,
            y=0,
            width=NPCBlip.MARKER_SIZE,
            height=NPCBlip.MARKER_SIZE,
            color=(255, 255, 85, 255),
            batch=Radar.BATCH,
            group=normal,
        )

        # rotate around the center of the marker, not the bottom left
        self.marker.anchor_position = (NPCBlip.MARKER_SIZE / 2, NPCBlip.MARKER_SIZE / 2)
        self.marker.rotation = 45

    def delete(self):
        self.marker.delete()
        self.label.delete()

    def update(self, your_pos: tuple[float, float, float], view_matrix):
        self.actor.update_actor_state()

        screen_x, screen_y = self.world_to_screen(self.actor.pos, view_matrix)
        self.marker.x = screen_x
        self.marker.y = screen_y
        # self.marker.x = round(screen_x)
        # self.marker.y = round(screen_y)
        self.label.x = screen_x
        self.label.y = screen_y + self.y_offset

        elevation = self.actor.pos[2] - your_pos[2]
        alpha = self.get_alpha(elevation)
        readable_elevation = self.elevation_string(elevation)
        if self.show_health:
            # great for taming high level horses.
            hp, max_hp = self.actor.health
            new_label = (
                f"{self.actor.name}\n({round(hp)}/{round(max_hp)}){readable_elevation}"
            )
        else:
            new_label = f"{self.actor.name}{readable_elevation}"

        self.marker.color = (255, 255, 85, alpha)
        self.update_label(new_label, NPCBlip.FONT_SIZES, alpha)


class GenericBlip(GameObject):
    """simple X marker for generic objects"""

    OUTER_RADIUS = 4
    INNER_RADIUS = 1
    # name, elevation
    FONT_SIZES = (8, 7)

    __slots__ = ("marker",)

    def __init__(self, actor):
        super().__init__(actor, verylow)
        # white X shape
        self.marker = shapes.Star(
            0,
            0,
            outer_radius=GenericBlip.OUTER_RADIUS,
            inner_radius=GenericBlip.INNER_RADIUS,
            num_spikes=4,
            rotation=45,
            color=(255, 255, 255, 255),
            batch=Radar.BATCH,
            group=lowest,
        )

    def delete(self):
        self.marker.delete()
        self.label.delete()

    def update(self, your_pos: tuple[float, float, float], view_matrix):
        self.actor.update_actor_state()
        screen_x, screen_y = self.world_to_screen(self.actor.pos, view_matrix)
        self.marker.x = round(screen_x)
        self.marker.y = round(screen_y)
        self.label.x = screen_x
        self.label.y = screen_y + 10

        elevation = self.actor.pos[2] - your_pos[2]
        alpha = self.get_alpha(elevation)
        self.marker.color = (255, 255, 255, alpha)
        elevation_str = self.elevation_string(elevation)
        new_label = f"{self.actor.name}{elevation_str}"

        self.update_label(new_label, GenericBlip.FONT_SIZES, alpha)
