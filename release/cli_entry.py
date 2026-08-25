"""PyInstaller entry point for the standalone public CLI."""

from geyser_cli.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
