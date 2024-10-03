# MO2-Radar by KarniOG
<p align="center">
  <img src="https://github.com/KarniOG/MO2-Radar/assets/166090320/e0227110-1555-4f46-af6e-cfc9dc06664b"/>
</p>

This is an external Mortal Online 2 radar hack made for Linux and written in
Python. The code is relatively simple so it should be easy to extend or adapt
to other games, especially ones using Unreal Engine.

## FAQ

- ### Will I get banned?
    Probably not. You won't get *detected* - I've used this for thousands of
    hours. The radar doesn't modify any memory, it reads it externally. Don't
    be too blatant and you should be fine. With all that said, you cheat at
    your own risk, etc. etc. Don't blame me if you get caught.

- ### The game updated and now the radar is broken!
    Not every game update will break things, but if it does stop working after
    an update send me a message on UC or open an issue on GitHub and I'll take a
    look.

- ### Can you add...
    Don't count on it. I'm focusing on other projects now and don't plan on
    adding any major features to this, but I'm keeping it updated and might add
    small features from time to time.

- ### I don't know how to do X, can you help me?
    If it's related to hacking, I'll try my best. For general Linux questions
    check out [r/linux_gaming](https://www.reddit.com/r/linux_gaming/comments/16xx5yv/faqs/)
    or [DuckDuckGo](https://duckduckgo.com/) first. If you're still stuck, let
    me know and I'll be happy to help.

- ### Windows
    Not supported. If you want to port it yourself, the only major thing you'll
    need to do is change `native.py` to use `ReadProcessMemory`. The rest of
    the hack will work without changes. I recommend checking out
    [DougTheDruid's project](https://github.com/DougTheDruid/SoT-ESP-Framework/)
    if you're interested in that.


## Requirements

- Python >= 3.8
- Your favorite Linux distribution
- Root privileges
- The ability to use a command line

You don't need to be a programmer or have much experience with Linux to use
this hack. It works out of the box with no changes necessary.


## Setup

Download the code and extract the files to a new directory, then open a
terminal in that directory and run:
```
sh setup.sh
```
to create automatically create a virtual environment for the cheat. On Debian
based distributions, you may need to install the `python3-venv` package first
with:
```
sudo apt install python3-venv
```

Next, you can launch the cheat by running:
```
sudo sh launch.sh
```
I recommend using the [Flatpak](https://flathub.org/apps/com.valvesoftware.Steam)
version of Steam.


## Usage

The program must be run as root. To start the radar, open a terminal in the
directory where you extracted the program and run:
```
sudo python3 -OO main.py
```
while the game is running.

You can preview the radar graphics without running the hack ingame by running
`demo.py`.

You can close the radar by either pressing `Esc` inside the radar window or
`Ctrl+C` inside the terminal where you ran the program.

You can zoom in or out by pressing `PageUp` and `PageDown` or the `Up` and
`Down` arrow keys inside the radar window.

You can control what gets displayed by editing `config.json`. To view the
FNames of actors as they're loaded, enable the `debug_fnames` option. When you
see an actor you're interested in, you can add it to the appropriate category
in `config.json`.

To show an NPC, the beginning of its FName must be in `npc_prefixes`. The two
included by default cover pretty much every NPC in the game, so you shouldn't
need to change it. If an FName begins with a prefix in `npc_prefixes`, it's
checked to see if it contains any of the strings in `npc`. If it does, a radar
marker will be created.

If the NPC's FName contains a string from `show_health`, the radar will display
the NPC's health. Similarly, if it contains a string from `invert_label` the
label will be shown underneath the marker instead of above it. This is nice for
mounts because the label won't cover the name of the player riding it.

Here's an example of how it would process the FName
`BP_AI_Example_ZombieBear_C`:
- The FName **starts with** `BP_AI_`, which is in `npc_prefixes`. This means
    it's an NPC, but we still need to check to see if it's an NPC we want to
    display.

- The FName **contains** `Bear` from `npc`. That's a match, so the radar will
    show the NPC.

- The FName also **contains** the tag `Zombie` from `show_health`, so its
    health will be shown.

- Finally, it **contains** `Bear` from `invert_label`, so its label will be
    inverted.

Of course, you can change the options if you want. I like having a lot of
information, so the default config includes almost everything I consider
useful. Feel free to turn some things off.

Mesh actors are handled in a much simpler way. The radar just checks to see
if they contain a string in `mesh`. For `AvatarStaticMesh_LootBagExample_C`:

- The FName **contains** `AvatarStaticMesh_LootBag` from `mesh`, so it's a
    match and will be displayed. It only needs to be a partial match.

Because it doesn't care as much about what it matches for meshes, try to use
longer strings in the `mesh` section of the config to prevent bad matches.

If you'd like to change the font sizes, you'll need to edit
`PlayerBlip.FONT_SIZES`, `NPCBlip.FONT_SIZES`, or `GenericBlip.FONT_SIZES` in
`graphics.py`.


## Acknowledgements

- ### [DougTheDruid/SoT-ESP-Framework](https://github.com/DougTheDruid/SoT-ESP-Framework/)
    For being a great educational resource and demonstrating that there's
    nothing wrong with using Python for externals.

- ### [XRadius/project-tanya](https://github.com/XRadius/project-tanya/)
    For being an excellent Linux hack and providing detailed information on
    system settings.

- ### SV
    For letting us all get away with it. :^)
