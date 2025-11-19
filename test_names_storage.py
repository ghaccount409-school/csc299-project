import tempfile
from pathlib import Path

from src.names_storage import NameStore


def test_add_and_list(tmp_path: Path):
    data_file = tmp_path / "names.json"
    store = NameStore(file_path=data_file)

    assert store.list_names() == []

    store.add_name("Alice")
    store.add_name("Bob")

    assert store.list_names() == ["Alice", "Bob"]
