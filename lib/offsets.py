from lib.memory import PatternScanner

# pylint: disable=invalid-name

GWorld_pat = ("85 c0 75 ? ? 8b 05 ? ? ? ? c3", 7)
GNames_pat = ("8b 05 ? ? ? ? ff c0 c1 e9", 2)

scanner = PatternScanner("GameThread", "Win64-Shipping.exe")
GWorld = scanner.pattern_scan(GWorld_pat[0], GWorld_pat[1])
GNames = scanner.pattern_scan(GNames_pat[0], GNames_pat[1]) + 8
del scanner

PersistentLevel = 0x30
ActorArray = 0xB0

OwningGameInstance = 0x1D8
LocalPlayers = 0x38
PlayerController = 0x30
PlayerCameraManager = 0x348
CameraCachePrivate = 0x13A0
AcknowledgedPawn = 0x338

RootComponent = 0x1A0
RootPos = 0xF0

IsGhost = 0x678
CreatureName = 0xC90
Health = 0xCD0

MeshName = 0x2E8
