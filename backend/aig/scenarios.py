"""Committed hand-authored scenarios; no RNG or procedural generation."""

from dataclasses import replace
from types import MappingProxyType
from aig.versions import LATEST_SCENARIO_VERSION, resolve_version

from aig.setup import GameSetup, PlayerSetup
from aig.state import ControllerType, GameConfig, GameMap, Position, ResourceType, Terrain
from aig.state import BarbarianCamp


def _demo_v1_setup() -> GameSetup:
    """A fixed 12 by 10 square-grid map, with two manual factions and land routes."""
    rows = (
        "GGPPFFGGHHGG",
        "GGGFFGMGGPPG",
        "GPGGGGMGFFGG",
        "GFFPHGMGGGPG",
        "GGPHHGGGWWGG",
        "GGGMMMGWWWGG",
        "GPFGGGGGWGGG",
        "GGGGFHGGGPGG",
        "GPPGFFGHHGGG",
        "GGGGGGPPGGGG",
    )
    terrains = dict(G=Terrain.GRASSLAND, P=Terrain.PLAINS, F=Terrain.FOREST,
                    H=Terrain.HILLS, M=Terrain.MOUNTAINS, W=Terrain.WATER)
    return GameSetup(
        config=GameConfig(seed=42, debug_mode=False), game_map=GameMap(12, 10, origin=Position(0, 0)),
        tiles=tuple((Position(x, y), terrains[symbol])
                    for y, row in enumerate(rows) for x, symbol in enumerate(row)),
        players=(PlayerSetup("A", ControllerType.HUMAN, Position(2, 2)),
                 PlayerSetup("B", ControllerType.HUMAN, Position(9, 7))),
        turn_order=("A", "B"),
    )


def _scenario_v1_setup() -> GameSetup:
    """Same world and starts as hot-seat; A is human and B uses explicit AI control."""
    setup = _demo_v1_setup()
    return replace(setup, players=tuple(
        replace(p, controller=ControllerType.AI) if p.id == "B" else p
        for p in setup.players
    ))


# Immutable, deliberately placed resources on the original terrain/start geometry.
SCENARIO_V2_RESOURCES = (
    (Position(2, 2), ResourceType.WHEAT),
    (Position(3, 1), ResourceType.CATTLE),
    (Position(4, 4), ResourceType.IRON),
    (Position(1, 6), ResourceType.SPICES),
    (Position(0, 8), ResourceType.GEMS),
    (Position(9, 7), ResourceType.WHEAT),
    (Position(8, 7), ResourceType.CATTLE),
    (Position(8, 8), ResourceType.IRON),
    (Position(10, 3), ResourceType.SPICES),
    (Position(11, 1), ResourceType.GEMS),
    (Position(6, 4), ResourceType.CATTLE),
    (Position(6, 6), ResourceType.SPICES),
    (Position(7, 3), ResourceType.GEMS),
    (Position(5, 7), ResourceType.IRON),
)


def _scenario_v2_setup() -> GameSetup:
    return replace(_scenario_v1_setup(), resources=SCENARIO_V2_RESOURCES)


SCENARIO_V3_CAMPS = (
    BarbarianCamp("camp-1", Position(1, 6)),
    BarbarianCamp("camp-2", Position(10, 3)),
    BarbarianCamp("camp-3", Position(6, 4)),
)


def _scenario_v3_setup() -> GameSetup:
    return replace(_scenario_v2_setup(), camps=SCENARIO_V3_CAMPS)


SCENARIO_V4_ROWS = (
    "GGPPFFGGHHGGPPGG",
    "GGGFFGGMMGGFFGGG",
    "GPGGGGGHGGGGGGPG",
    "GFFPHGGGGGHGPFFG",
    "GGPHHGFGGFGHHPGG",
    "GGGGGGHGGHGGGGGG",
    "GPFGGWWWGGGGGFPG",
    "GGGGFHWGGHFGGGGG",
    "GPPGGFGGGGFGGPPG",
    "GGGGGGPHHPGGGGGG",
    "GGFFGGGMMGGGFFGG",
    "GGPPGGGGGGGGPPGG",
)
SCENARIO_V4_RESOURCES = tuple((Position(x, y), kind) for x, y, kind in (
    (2, 2, ResourceType.WHEAT), (3, 1, ResourceType.CATTLE),
    (13, 2, ResourceType.WHEAT), (12, 1, ResourceType.CATTLE),
    (2, 9, ResourceType.WHEAT), (3, 10, ResourceType.CATTLE),
    (13, 9, ResourceType.WHEAT), (12, 10, ResourceType.CATTLE),
    (4, 4, ResourceType.IRON), (11, 4, ResourceType.IRON),
    (5, 7, ResourceType.IRON), (9, 7, ResourceType.IRON),
    (7, 3, ResourceType.GEMS), (8, 8, ResourceType.GEMS),
    (6, 4, ResourceType.SPICES), (9, 4, ResourceType.SPICES),
    (5, 8, ResourceType.SPICES), (10, 8, ResourceType.SPICES),
))
SCENARIO_V4_CAMPS = tuple(BarbarianCamp(f"camp-{i}", Position(x, y))
    for i, (x, y) in enumerate(((4, 4), (11, 4), (4, 7), (11, 7), (8, 5)), 1))


def _scenario_v4_setup() -> GameSetup:
    terrains = dict(G=Terrain.GRASSLAND, P=Terrain.PLAINS, F=Terrain.FOREST,
                    H=Terrain.HILLS, M=Terrain.MOUNTAINS, W=Terrain.WATER)
    return GameSetup(
        config=GameConfig(seed=42, debug_mode=False), game_map=GameMap(16, 12),
        tiles=tuple((Position(x, y), terrains[symbol])
                    for y, row in enumerate(SCENARIO_V4_ROWS) for x, symbol in enumerate(row)),
        players=tuple(PlayerSetup(actor, ControllerType.HUMAN, Position(x, y))
                      for actor, x, y in (("A", 2, 2), ("B", 13, 2), ("C", 2, 9), ("D", 13, 9))),
        turn_order=("A", "B", "C", "D"), resources=SCENARIO_V4_RESOURCES,
        camps=SCENARIO_V4_CAMPS,
    )


SCENARIOS = MappingProxyType({"scenario-v1": _scenario_v1_setup, "scenario-v2": _scenario_v2_setup,
                              "scenario-v3": _scenario_v3_setup, "scenario-v4": _scenario_v4_setup})


def scenario_setup(version=None) -> GameSetup:
    selected = resolve_version(version, available=SCENARIOS, latest=LATEST_SCENARIO_VERSION)
    return SCENARIOS[selected]()


def human_vs_ai_demo_setup() -> GameSetup:
    """Preserved two-player browser demo; benchmarks select scenarios independently."""
    return scenario_setup("scenario-v3")


def demo_game_setup() -> GameSetup:
    setup = human_vs_ai_demo_setup()
    return replace(setup, players=tuple(replace(p, controller=ControllerType.HUMAN) for p in setup.players))
