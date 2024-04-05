from memory import Reader
import offsets


class Actor:
    """Base actor data handler"""

    __slots__ = "mem", "addr", "fname", "root_component", "pos", "name"

    def __init__(self, addr: int, fname: str, memory: Reader):
        self.mem = memory
        self.addr = addr
        self.fname = fname
        self.root_component = self.mem.read(addr + offsets.RootComponent, "Q")
        self.pos = 0.0, 0.0, 0.0
        self.name = fname

    def read_name(self, name_ptr: int) -> str:
        """Read actor name from pointer and return it"""
        # Actor->Name, Actor.NameLength
        name_addr, name_length = self.mem.read(name_ptr, "QB")
        name_bytes = max(0, name_length * 2 - 2)
        name = self.mem.read_utf16(name_addr, name_bytes)
        return name

    def update_actor_state(self):
        # Actor->RootComponent.RootPosition
        # UE5 is more or less the same as UE4 for our purposes,
        # but it uses float64s for coordinates instead of float32s.
        self.pos = self.mem.read(self.root_component + offsets.RootPos, "3d")


class NPC(Actor):
    """NPC data handler"""

    __slots__ = ("health",)

    def __init__(self, addr: int, fname: str, memory: Reader):
        super().__init__(addr, fname, memory)
        self.health = 0.0, 0.0

    def update_actor_state(self):
        super().update_actor_state()
        self.name = self.read_name(self.addr + offsets.CreatureName)
        # Actor.Health, Actor.MaxHealth
        self.health = self.mem.read(self.addr + offsets.Health, "2f")


class Player(NPC):
    """Player data handler"""

    __slots__ = ("is_ghost",)

    def __init__(self, addr: int, fname: str, memory: Reader):
        super().__init__(addr, fname, memory)
        self.is_ghost = False

    def update_actor_state(self):
        super().update_actor_state()
        # Actor.IsGhost
        self.is_ghost = self.mem.read(self.addr + offsets.IsGhost, "?")


class Mesh(Actor):
    """StaticMesh data handler"""

    def update_actor_state(self):
        super().update_actor_state()
        self.name = self.read_name(self.addr + offsets.MeshName)
