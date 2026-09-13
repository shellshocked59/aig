"""Fixed tactical match and offline replay, or an isolated HTTP smoke fixture.

Usage: python scripts/arena-phase2-smoke.py [--output DIR] [--serve PORT]
No action selection, AI, external providers, or production fixture endpoint.
"""

import argparse
import json
from pathlib import Path

from aig.state import Position as P
from aig.arena import (ArenaAttack, ArenaEndTurn, ArenaHeal, ArenaMove, ArenaFinish,
                       ArenaRevive, ArenaShieldBash, ArenaSnipe, ArenaFireball,
                       ArenaSimulation, replay, state_hash, to_snapshot)
from aig.arena.state import (ArenaState, ArenaCore, ArenaPlayer, ArenaUnit, Board,
                             Tile, Terrain, Bonus, UnitType, STATS)
from aig.arena.snapshots import command_to_dict, digest


def initial_state():
    bonuses = {(2, 2): Bonus.POWER, (3, 0): Bonus.POWER,
               (4, 2): Bonus.WARD, (5, 2): Bonus.SIEGE}
    board = Board(tuple(Tile(Terrain.BLOCKED if (x, y) in ((0, 4), (8, 0)) else Terrain.FLOOR,
                             bonuses.get((x, y))) for y in range(5) for x in range(9)))
    positions = {"blue": [(2, 2), (1, 0), (2, 3), (1, 3)],
                 "red": [(3, 2), (6, 0), (4, 3), (5, 4)]}
    units = {}
    for owner, points in positions.items():
        for kind, point in zip(UnitType, points):
            uid = f"{owner}-{kind.value}"
            units[uid] = ArenaUnit(uid, owner, kind, P(*point), STATS[kind].hp)
    return ArenaState(board, (ArenaPlayer("blue", "Blue Team"), ArenaPlayer("red", "Red Team")), units,
                      {f"{p}-core": ArenaCore(f"{p}-core", p, P(x, 2)) for p, x in (("blue", 0), ("red", 8))}, "blue")


def commands():
    return [
        ArenaShieldBash("blue", "blue-knight", "red-knight"),
        ArenaMove("blue", "blue-ranger", P(3, 0)),
        ArenaSnipe("blue", "blue-ranger", "red-mage"),
        ArenaMove("blue", "blue-mage", P(3, 3)),
        ArenaEndTurn("blue"),
        ArenaRevive("red", "red-cleric", "red-mage"),
        ArenaAttack("red", "red-mage", "blue-mage"),
        ArenaMove("red", "red-mage", P(5, 3)),
        ArenaHeal("red", "red-cleric", "red-mage"),
        ArenaEndTurn("red"),
        ArenaFireball("blue", "blue-mage", P(4, 3)),
        ArenaRevive("blue", "blue-cleric", "blue-mage"),
        ArenaAttack("blue", "blue-mage", "red-mage"),
        ArenaEndTurn("blue"),
        ArenaMove("red", "red-ranger", P(5, 0)),
        ArenaSnipe("red", "red-ranger", "blue-knight"),
        ArenaMove("red", "red-ranger", P(6, 1)),
        ArenaEndTurn("red"),
        ArenaMove("blue", "blue-knight", P(4, 3)),
        ArenaFinish("blue", "blue-knight", "red-mage"),
        ArenaHeal("blue", "blue-cleric", "blue-mage"),
        ArenaMove("blue", "blue-ranger", P(5, 2)),
        ArenaAttack("blue", "blue-ranger", "red-core"),
        ArenaEndTurn("blue"),
        ArenaEndTurn("red"),
        ArenaAttack("blue", "blue-ranger", "red-core"),
        ArenaAttack("blue", "blue-ranger", "red-core"),
        ArenaAttack("blue", "blue-ranger", "red-core"),
    ]


def run_match():
    sim = ArenaSimulation(initial_state())
    for command in commands():
        sim.execute(command)
    restored = replay(sim.trace())
    assert restored.state == sim.state
    assert restored.trace() == sim.trace()
    assert restored.metrics() == sim.metrics()
    assert sim.state.winner_player_id == "blue"
    return sim


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(".local/arena-phase2-verification"))
    parser.add_argument("--serve", type=int, help="Serve only on loopback using this tactical initial state")
    args = parser.parse_args()
    sim = run_match()
    args.output.mkdir(parents=True, exist_ok=True)
    report = dict(commands=len(commands()), winner=sim.state.winner_player_id,
                  final_hash=state_hash(sim.state), trace_hash=digest(sim.trace()),
                  metrics=sim.metrics(), replay="exact state, trace and metrics")
    for name, value in {"initial": to_snapshot(initial_state()), "commands": [command_to_dict(c) for c in commands()],
                        "final": to_snapshot(sim.state), "trace": sim.trace(), "match-report": report}.items():
        (args.output / f"{name}.json").write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if args.serve:
        import uvicorn
        from aig.api import create_app
        app = create_app()
        app.state.arena_session._simulation = ArenaSimulation(initial_state())
        uvicorn.run(app, host="127.0.0.1", port=args.serve)


if __name__ == "__main__":
    main()
