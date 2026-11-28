"""The review launcher: `wormspy-review [data_root, session, or rec-NNN]`.

Browses sessions, replays channels frame-synced with world-coordinate trajectory and calcium
statistics, and selects/runs analysis pipelines. Needs the `analysis` extra (pandas).
"""

import argparse
import sys
from pathlib import Path

DEFAULT_CONFIG = Path("config/rig.toml")


def _parse(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="wormspy-review", description=__doc__.splitlines()[0])
    parser.add_argument("path", type=Path, nargs="?",
                        help="a data_root, session folder, or recording (rec-NNN)")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG,
                        help="rig.toml (used for default data_root when path is omitted)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse(sys.argv[1:] if argv is None else argv)
    from PySide6.QtWidgets import QApplication

    try:
        from wormspy.analysis.catalog import scan_recordings
        from wormspy.config import load_config
        from wormspy.ui.review_window import ReviewWindow
    except ImportError as exc:                  # pandas missing: the reader says how to fix it
        raise SystemExit(f"wormspy-review: {exc}") from exc
    from wormspy.ui import theme

    qt = QApplication.instance() or QApplication(sys.argv[:1])
    theme.apply(qt)
    window = ReviewWindow()
    opened = False
    if args.path is not None:
        try:
            path = args.path
            if (path / "frames.csv").exists() or (path / "session.json").exists():
                window.open_path(path)
                root = path.parent if (path / "session.json").exists() else path.parents[1]
                if root.exists():
                    window.browser.set_root(root)
                    window.browser.select_recording(window.recording.path)
            else:
                window.open_root(path)
            opened = True
        except (OSError, ValueError, KeyError) as exc:
            raise SystemExit(f"wormspy-review: {exc}") from exc
    else:
        try:
            cfg = load_config(args.config)
            if cfg.paths.data_root.exists() and scan_recordings(cfg.paths.data_root):
                window.open_root(cfg.paths.data_root)
                opened = True
        except ValueError:
            pass
    window.resize(1600, 900)
    window.show()
    if not opened:
        window.ask_open()
    return qt.exec()


if __name__ == "__main__":
    raise SystemExit(main())
