"""Run the dependency-free Genopedia demonstration from a fresh checkout."""

from pathlib import Path
import sys


# Make ``python examples/demo_genomics.py`` work before editable installation.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from genopedia.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main(["demo", "--length", "120"]))
