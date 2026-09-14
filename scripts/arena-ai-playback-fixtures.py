"""Offline, executed-command fixtures shared by Phase 5 tests and the lab."""
import json
from pathlib import Path
from aig.web import ArenaWebSession
from aig.settings import load_settings
from aig.arena import ArenaEndTurn


def examples():
    result = {}
    for provider in ('heuristic', 'heuristic-v2'):
        session = ArenaWebSession(load_settings())
        start = session.demo(versus_ai=True, provider=provider)
        final = session.execute(ArenaEndTurn('blue'))
        batch = final.pop('presentation')
        result[provider] = dict(start=start, final=final, batch=batch)
    return result


if __name__ == '__main__':
    Path('frontend/src/js/arena-ai-playback-fixtures.json').write_text(
        json.dumps(examples(), separators=(',', ':')) + '\n', encoding='utf-8')
