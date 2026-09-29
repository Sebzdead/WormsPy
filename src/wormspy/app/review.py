"""The review launcher: `wormspy-review [rec-NNN or session folder]`.

Plays back a finished recording: the channels side by side, the worm's path with the event
markers, and a scrub bar, all frame-synced. Needs the `analysis` extra (pandas). Without a path
it asks for a folder.
"""

import argparse
import sys
from pathlib import Path


def _parse(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="wormspy-review", description=__doc__.splitlines()[0])
    parser.add_argument("path", type=Path, nargs="?",
                        help="a recording (rec-NNN) or session folder")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse(sys.argv[1:] if argv is None else argv)
    from PySide6.QtWidgets import QApplication

    try:
        from wormspy.ui.review_window import ReviewWindow
    except ImportError as exc:                  # pandas missing: the reader says how to fix it
        raise SystemExit(f"wormspy-review: {exc}") from exc
    from wormspy.ui import theme

    qt = QApplication.instance() or QApplication(sys.argv[:1])
    theme.apply(qt)
    window = ReviewWindow()
    if args.path is not None:
        try:
            window.open_path(args.path)
        except (OSError, ValueError, KeyError) as exc:
            raise SystemExit(f"wormspy-review: {exc}") from exc
    window.resize(1600, 900)
    window.show()
    if args.path is None:
        window.ask_open()
    return qt.exec()


if __name__ == "__main__":
    raise SystemExit(main())
