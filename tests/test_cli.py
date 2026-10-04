import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def test_cli_packs_example_files(tmp_path):
    out = tmp_path / "packed.txt"
    r = subprocess.run(
        [
            sys.executable, "-m", "context_packer.cli",
            "--budget", "600",
            "--strategy", "head-tail",
            "--reserve", "100",
            "--output-reserve", "200",
            "--report",
            "-o", str(out),
            "examples/architecture.md",
            "examples/meeting-notes.md",
            "examples/server-log.txt",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    assert out.is_file()
    assert "Context packing report" in r.stdout
