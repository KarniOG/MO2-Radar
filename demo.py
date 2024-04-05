import random
import math
import pyglet

pyglet.options["debug_gl"] = False  # disable pyglet's debug mode
# pylint: disable=wrong-import-position
from graphics import Radar, PlayerBlip, NPCBlip, GenericBlip
from common import config

FPS = 30
YAW = 360
dummies = []

window = pyglet.window.Window(
    config["window_size"],
    config["window_size"],
    caption="Demo",
    style="default",  # can be "transparent" if you want
)

radar = Radar()


@window.event
def on_draw():
    window.clear()
    Radar.BATCH.draw()


class DummyActor:
    def __init__(self, fname, name, pos, health, is_ghost):
        self.set_state(fname, name, pos, health, is_ghost)

    def update_actor_state(self):
        return

    def set_state(self, fname, name, pos, health, is_ghost):
        self.fname = fname
        self.name = name
        self.pos = pos
        self.health = health
        self.is_ghost = is_ghost


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
    YAW -= 1
    radar.compass.rotate_compass(YAW)
    for dummy in dummies:
        dummy.actor.health[0] -= 1
        if dummy.actor.health[0] < 0:
            dummy.actor.health[0] = dummy.actor.health[1]
        dummy.update((0, 0, 0), YAW)


pyglet.clock.schedule_interval(refresh_radar, 1 / FPS)
pyglet.app.run(interval=1 / FPS)
