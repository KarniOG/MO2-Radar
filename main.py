import random
import pyglet

pyglet.options["debug_gl"] = False  # disable pyglet's debug mode
# pylint: disable=wrong-import-position
from pyglet.window import key

from lib.common import config
from lib.game import GameHandler
from lib.graphics import Radar

FPS = 30


def refresh_radar(_):
    game.update_objects()
    radar.compass.rotate_compass(game.local["view_matrix"])
    x, y, z = game.local["pos"]

    coords.text = f"X: {x/100:.0f}\nY: {y/100:.0f}\nZ: {z/100:.0f}"


if config["window_name"] == "":
    # if the window name isn't set, generate a random one.
    NAME_LEN = random.randint(6, 20)
    CHARACTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ "
    random_characters = random.choices(CHARACTERS, k=NAME_LEN)
    WINDOW_NAME = "".join(random_characters)
else:
    WINDOW_NAME = config["window_name"]

window = pyglet.window.Window(
    config["window_size"],
    config["window_size"],
    caption=WINDOW_NAME,
    style="default",  # can be "transparent" if you want
)

# move window to default position
window.set_location(config["window_x"], config["window_y"])
# FPS counter
fps = pyglet.window.FPSDisplay(window)
fps.label.font_size = 10

radar = Radar()
game = GameHandler()

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


@window.event
def on_draw():
    window.clear()
    Radar.BATCH.draw()
    fps.draw()

@window.event
def on_key_press(symbol, _modifiers):
    # up arrow or pageup to zoom in, down arrow or pagedown to zoom out
    match symbol:
        case key.UP | key.PAGEUP:
            Radar.RANGE = max(Radar.RANGE - 2000, 2000)
            radar.build_rings()
        case key.DOWN | key.PAGEDOWN:
            Radar.RANGE = min(Radar.RANGE + 2000, 100000)
            radar.build_rings()


pyglet.clock.schedule_interval(refresh_radar, 1 / FPS)
pyglet.app.run(interval=1 / FPS)
