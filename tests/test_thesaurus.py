from __future__ import annotations

import json
from pathlib import Path

import pytest

from sob.thesaurus import Thesaurus

THESAURUS_JSON: Path = Path(__file__).parent / "static-data" / "thesaurus.json"
THESAURUS_MODEL_PY: Path = (
    Path(__file__).parent / "regression-data" / "thesaurus_model.py"
)


def test_thesaurus() -> None:
    with open(THESAURUS_JSON) as thesaurus_io:
        thesaurus: Thesaurus = Thesaurus(json.load(thesaurus_io))
    if THESAURUS_MODEL_PY.exists():
        assert thesaurus.get_module_source().strip() == (
            THESAURUS_MODEL_PY.read_text().strip()
        )
    else:
        thesaurus.save_module(THESAURUS_MODEL_PY)


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-vv"])
