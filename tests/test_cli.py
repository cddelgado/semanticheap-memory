from pathlib import Path
import subprocess
import sys


def run_cli(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    db = tmp_path / "cli.db"
    return subprocess.run(
        [sys.executable, "-m", "semantic_heap.cli", "--db", str(db), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_init_save_retrieve(tmp_path: Path):
    init = run_cli(tmp_path, "init")
    assert init.returncode == 0

    save = run_cli(tmp_path, "save", "--domain", "users", "--idea", "David is going to dinner tonight", "--json")
    assert save.returncode == 0
    assert '"idea_id"' in save.stdout

    retrieve = run_cli(tmp_path, "retrieve", "--idea", "dinner plans", "--time", "now", "--json")
    assert retrieve.returncode == 0
    assert '"matches"' in retrieve.stdout
