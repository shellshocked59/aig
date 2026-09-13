"""Opt-in: python -m aig.arena.ollama_smoke. Exactly one request, no repair."""
from aig.arena.smoke import main

if __name__ == "__main__":
    raise SystemExit(main("ollama"))
