import os
import time
from lib.memory import Reader
from lib import offsets
from lib.common import config
from lib.actors import Actor, Player, NPC, Mesh
from lib.graphics import PlayerBlip, NPCBlip, GenericBlip, make_view_matrix


class GameHandler:
    """tracks game state information and actors of interest"""

    __slots__ = "mem", "actor_cache", "fname_cache", "objects", "local"

    def __init__(self):
        self.mem = Reader("GameThread")
        # use a set for fast membership testing
        self.actor_cache = frozenset()
        self.fname_cache = {}
        self.objects = []
        self.local = {}

    def update_local(self, uworld: int):
        """Update local player position, view matrix, and pawn address"""
        # UWorld->OwningGameInstance->*LocalPlayer->PlayerController
        game_instance = self.mem.read(uworld + offsets.OwningGameInstance, "Q")
        local_players = self.mem.read(game_instance + offsets.LocalPlayers, "Q")
        local_player = self.mem.read(local_players, "Q")  # local_players[0]
        controller = self.mem.read(local_player + offsets.PlayerController, "Q")

        # PlayerController->PlayerCameraManager.CameraCachePrivate
        camera = self.mem.read(controller + offsets.PlayerCameraManager, "Q")
        # x, y, z, pitch, yaw, roll, FOV
        raw_pov = self.mem.read(camera + offsets.CameraCachePrivate, "6df")

        self.local["pos"] = raw_pov[0:3]
        view = raw_pov[3:7]
        self.local["view_matrix"] = make_view_matrix(self.local["pos"], view)

        # PlayerController->AcknowledgedPawn
        # we compare this to player addresses to ignore ourself
        self.local["pawn"] = self.mem.read(controller + offsets.AcknowledgedPawn, "Q")

    def get_fname(self, key: tuple[int, int]) -> str:
        """Return a key's FName value"""
        try:
            # use cached value if possible
            return self.fname_cache[key]
        except KeyError:
            # retrieve fname from string intern pool using its key
            # see UnrealNames.cpp and NameTypes.h

            # FNameEntryHandle
            block = key[1] * 8
            offset = key[0] * 2

            block_ptr = self.mem.read(offsets.GNames + block, "Q")

            # FNameEntryHeader
            name_len = self.mem.read(block_ptr + offset, "H") >> 6
            name = self.mem.read_string(block_ptr + offset + 2, name_len)

            self.fname_cache[key] = name  # cache it for later
            # you can use the debug_fnames option to find actor fnames
            # consider outputting the program to a file, e.g.:
            # sudo python -OO main.py > fname_dump.txt
            # and then you can search it later.
            if config["debug_fnames"]:
                print(name)
            return name

    def read_actors(self, uworld: int) -> tuple[int, str]:
        """
        Read actor array, read fnames of new actors,
        update actor cache, return list of new actors.
        """
        persistent_level = self.mem.read(uworld + offsets.PersistentLevel, "Q")
        # UWorld->PersistentLevel->ActorArray, PersistentLevel.ActorCount
        actor_array, actor_count = self.mem.read(
            persistent_level + offsets.ActorArray, "QH"
        )

        current_actors = frozenset(self.mem.read(actor_array, str(actor_count) + "Q"))

        new_actors = []
        # loop through addresses that are in current_actors
        # but not in self.actor_cache
        for addr in current_actors - self.actor_cache:
            if not addr:
                continue
            # I like bitmath but reading the key as two uint16s is simpler
            key = self.mem.read(addr + 0x18, "2H")
            fname = self.get_fname(key)
            new_actors.append((addr, fname))

        # replace cache with the most recent actor array
        self.actor_cache = current_actors
        return new_actors

    def init_actor(self, addr: int, fname: str):
        """Parse an actor's fname and add a blip to self.objects if it matches"""
        # I don't like the way I designed the config file but I'm too lazy to change it.

        if fname == "BP_PlayerCharacter_C" and addr != self.local["pawn"]:
            actor = Player(addr, fname, self.mem)
            blip = PlayerBlip(actor)
            self.objects.append(blip)
            return

        is_npc = any(fname.startswith(prefix) for prefix in config["npc_prefixes"])
        if is_npc and any(npc in fname for npc in config["npc"]):
            actor = NPC(addr, fname, self.mem)
            blip = NPCBlip(actor)
            self.objects.append(blip)
            return

        if any(mesh in fname for mesh in config["mesh"]):
            actor = Mesh(addr, fname, self.mem)
            blip = GenericBlip(actor)
            self.objects.append(blip)
            return

        if config["debug_actors"]:
            actor = Actor(addr, fname, self.mem)
            blip = GenericBlip(actor)
            self.objects.append(blip)
            return

    def update_objects(self, tries=0):
        try:
            uworld = self.mem.read(offsets.GWorld, "Q")
            self.update_local(uworld)
            new_actors = self.read_actors(uworld)

        except TypeError as e:
            # changing levels or the process died.

            # signal 0 doesn't actually send a signal,
            # it just checks if the process is alive.
            os.kill(self.mem.pid, 0)
            if tries > 300:  # 30s
                raise RuntimeError("Bad offsets or game is stalled!") from e
            time.sleep(0.1)
            self.update_objects(tries + 1)
            return

        for addr, fname in new_actors:
            self.init_actor(addr, fname)

        # use a copy since we're modifying the original list
        for obj in self.objects.copy():
            is_loaded = obj.actor.addr in self.actor_cache
            is_local_player = obj.actor.addr == self.local["pawn"]
            if is_loaded and not is_local_player:
                try:
                    obj.update(self.local["pos"], self.local["view_matrix"])
                    continue
                except TypeError:
                    # the actor either just unloaded
                    # or was never a valid actor to begin with.
                    pass
            obj.delete()
            self.objects.remove(obj)
