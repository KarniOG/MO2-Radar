"""Quick demo I made for showcasing the radar's graphics"""

# pylint: skip-file
import random
import math
import pyglet

pyglet.options["debug_gl"] = False  # disable pyglet's debug mode
from lib.graphics import Radar, PlayerBlip, NPCBlip, GenericBlip, make_view_matrix
from lib.common import config

FPS = 60
YAW = 360
dummies = []

window = pyglet.window.Window(
    config["window_size"],
    config["window_size"],
    caption="Demo",
    style="default",
)
fps = pyglet.window.FPSDisplay(window)
fps.label.font_size = 10

coords = pyglet.text.Label(
    " ",
    font_name="DejaVu Sans",
    font_size=10,
    x=4,
    y=config["window_size"] - 4,
    anchor_x="left",
    anchor_y="top",
    multiline=True,
    width=180,
    batch=Radar.BATCH,
)
coords.text = f"X: {random.randint(-10000, 10000)}\n\
Y: {random.randint(-10000, 10000)}\n\
Z: {random.randint(-10000, 10000)}"

radar = Radar()


@window.event
def on_draw():
    window.clear()
    Radar.BATCH.draw()
    fps.draw()


class DummyActor:

    def __init__(self, fname, name, pos, health, is_ghost):
        self.fname = fname
        self.name = name
        self.pos = pos
        self.health = health
        self.is_ghost = is_ghost

    def update_actor_state(self):
        return


def randpos(
    min_dist=-config["max_range"] * 0.8,
    max_dist=config["max_range"] * 0.8,
    elevation_min=-4500,
    elevation_max=4500,
):
    x = math.inf
    y = math.inf
    z = math.inf

    while math.dist((x, y), (0, 0)) > max_dist:
        x = random.randrange(min_dist, max_dist)
        y = random.randrange(min_dist, max_dist)
        z = random.randrange(elevation_min, elevation_max)
    return [x, y, z]


for actor_type in ("Player", "NPC", "Object"):
    for i in range(5):
        name = f"{actor_type} {i+1}"
        pos = randpos()
        max_hp = random.randint(100, 250)
        health = [random.randrange(0, max_hp), max_hp]
        is_ghost = random.random() < 0.25

        actor = DummyActor(
            name,
            name,
            pos,
            health,
            is_ghost,
        )
        match actor_type:
            case "Player":
                if random.random() < 0.5:
                    actor.health[0] = actor.health[1]
                dummies.append(PlayerBlip(actor))
            case "NPC":
                blip = NPCBlip(actor)
                if random.random() < 0.4:
                    blip.show_health = True
                dummies.append(blip)
            case "Object":
                dummies.append(GenericBlip(actor))


def refresh_radar(_):
    global YAW
    YAW -= 0.2
    view_matrix = make_view_matrix((0, 0, 0), (0, YAW, 0))
    radar.compass.rotate_compass(view_matrix)
    for dummy in dummies:
        dummy.actor.health[0] -= 0.2
        if dummy.actor.health[0] < 0:
            dummy.actor.health[0] = dummy.actor.health[1]
        dummy.update((0, 0, 0), view_matrix)


pyglet.clock.schedule_interval(refresh_radar, 1 / FPS)
pyglet.app.run(interval=1 / FPS)
