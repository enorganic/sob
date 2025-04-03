from __future__ import annotations

from pathlib import Path

from sob._io import read

RAINBOX_PNG: Path = Path(__file__).parent / "data" / "rainbow.png"


def test_read() -> None:
    with open(RAINBOX_PNG, "rb") as rainbow_io:
        read(rainbow_io)
