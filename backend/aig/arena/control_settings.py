"""Opt-in gameplay control settings, separate from frozen research settings."""
from dataclasses import dataclass
import os
from pathlib import Path

from aig.arena.ai.bounded_replan import CONTROL_VERSION

CONTROL_VERSIONS = {
    'full_turn': 'arena-control-full-turn-v1',
    'bounded_replan': CONTROL_VERSION,
    'stepwise': 'arena-control-stepwise-v1',
}


@dataclass(frozen=True)
class ArenaControlSettings:
    mode: str = 'full_turn'

    def __post_init__(self):
        if self.mode not in CONTROL_VERSIONS:
            raise ValueError('AIG_ARENA_CONTROL_MODE must be full_turn, bounded_replan, or stepwise')


def load_control_settings(*, environ=None, local_file=None):
    # Optional dedicated file avoids changing the frozen .env key allowlist.
    values = {}
    if local_file is not None and Path(local_file).exists():
        for line in Path(local_file).read_text(encoding='utf-8-sig').splitlines():
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            key, sep, value = line.partition('=')
            if not sep or key.strip() != 'AIG_ARENA_CONTROL_MODE':
                raise ValueError('unknown Arena control setting')
            values[key.strip()] = value.strip().strip('\"\'')
    environment = os.environ if environ is None else environ
    return ArenaControlSettings(environment.get('AIG_ARENA_CONTROL_MODE') or
                                values.get('AIG_ARENA_CONTROL_MODE') or 'full_turn')
