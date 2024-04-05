from memory import PatternScanner

# pylint: disable=invalid-name

GWorld_pat = ("85 c0 75 ? ? 8b 05 ? ? ? ? c3", 7)
GNames_pat = ("8b 05 ? ? ? ? ff c0 c1 e9", 2)

scanner = PatternScanner("GameThread", "Win64-Shipping.exe")
GWorld = scanner.pattern_scan(GWorld_pat[0], GWorld_pat[1])
GNames = scanner.pattern_scan(GNames_pat[0], GNames_pat[1]) + 8
del scanner

PersistentLevel = 0x30
ActorArray = 0xA8

OwningGameInstance = 0x1B8
LocalPlayers = 0x38
PlayerController = 0x30
PlayerCameraManager = 0x350
CameraCachePrivate = 0x1330
AcknowledgedPawn = 0x340

RootComponent = 0x1A0
RootPos = 0xF0

IsGhost = 0x688
CreatureName = 0xCA0
GuildName = 0xCD0  # doesn't load until you target them. useless.
Health = 0xCE0
Height = 0xDB8

# StaticMesh actors have a different name offset
MeshName = 0x2F0
