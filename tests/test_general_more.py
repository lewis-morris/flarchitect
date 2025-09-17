import os
from pathlib import Path

import pytest

from flarchitect.utils.general import read_file_content


def test_read_file_content_found_and_missing(tmp_path: Path):
    p = tmp_path / "f.txt"
    p.write_text("hello")
    assert read_file_content(str(p)) == "hello"
    with pytest.raises(FileNotFoundError):
        read_file_content(str(p) + ".missing")
