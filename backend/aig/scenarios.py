"""Committed hand-authored scenarios; no RNG or procedural generation."""

from dataclasses import replace

from aig.setup import GameSetup, PlayerSetup
from aig.state import ControllerType, GameConfig, GameMap, Position, Terrain


def demo_game_setup() -> GameSetup:
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
        config=GameConfig(seed=42), game_map=GameMap(12, 10),
        tiles=tuple((Position(x, y), terrains[symbol])
                    for y, row in enumerate(rows) for x, symbol in enumerate(row)),
        players=(PlayerSetup("A", ControllerType.HUMAN, Position(2, 2)),
                 PlayerSetup("B", ControllerType.HUMAN, Position(9, 7))),
        turn_order=("A", "B"),
    )


def human_vs_ai_demo_setup() -> GameSetup:
    """Same world and starts as hot-seat; A is human and B uses explicit AI control."""
    setup = demo_game_setup()
    return replace(setup, players=tuple(
        replace(p, controller=ControllerType.AI) if p.id == "B" else p
        for p in setup.players
    ))
