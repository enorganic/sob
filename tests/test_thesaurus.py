from __future__ import annotations

import json
from pathlib import Path

import pytest

from sob.thesaurus import Thesaurus

THESAURUS_JSON: Path = Path(__file__).parent / "data" / "thesaurus.json"
THESAURUS_MODEL_PY: Path = (
    Path(__file__).parent / "data" / "thesaurus_model.py"
)


def test_thesaurus() -> None:
    with open(THESAURUS_JSON) as thesaurus_io:
        thesaurus: Thesaurus = Thesaurus(json.load(thesaurus_io))
    thesaurus.save_module(THESAURUS_MODEL_PY)


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-vv"])
