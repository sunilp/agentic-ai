"""Lab-004 must be able to write its outputs somewhere other than the repo.

Without this, any smoke run overwrites the committed corpus and results.
"""
from __future__ import annotations

import json
from pathlib import Path

from labs.lab_004.run import HERE, write_outputs


def test_write_outputs_writes_only_to_the_directory_it_is_given(tmp_path: Path) -> None:
    before = {p.name: p.read_bytes() for p in HERE.glob("*.json")}

    write_outputs(tmp_path / "nested", tickets=[{"id": "t-1"}], payload={"meta": {}}, markdown="# x")

    out = tmp_path / "nested"
    assert json.loads((out / "corpus.json").read_text()) == [{"id": "t-1"}]
    assert json.loads((out / "results.json").read_text()) == {"meta": {}}
    assert (out / "RESULTS.md").read_text() == "# x"

    after = {p.name: p.read_bytes() for p in HERE.glob("*.json")}
    assert after == before, "committed lab_004 artifacts were modified"
