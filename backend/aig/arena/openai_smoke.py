"""Opt-in: python -m aig.arena.openai_smoke. Exactly one request, no repair."""
from aig.arena.smoke import main

if __name__ == "__main__":
    raise SystemExit(main("openai"))
