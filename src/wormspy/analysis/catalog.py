"""Session/recording catalog and persistent analysis queue for `wormspy-review`."""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RecordingEntry:
    path: Path
    session_dir: Path
    key: str
    session_name: str
    recording_name: str
    created: str
    animal_id: str
    operator: str
    condition: str
    notes: str
    frames: int | None
    fps: float | None
    duration_s: float | None
    drops: int
    complete: bool
    roles: tuple[str, ...]


def _load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def _entry_from_recording(rec_dir: Path, session_info: dict | None) -> RecordingEntry:
    session_dir = rec_dir.parent
    meta = (session_info or {}).get("metadata", {})
    rec_info = _load_json(rec_dir / "recording.json")
    frames: int | None = None
    fps: float | None = None
    drops = 0
    roles: tuple[str, ...] = ()
    if rec_info is not None:
        frames = rec_info.get("frames")
        fps = rec_info.get("fps")
        dropped = rec_info.get("dropped") or {}
        if isinstance(dropped, dict):
            drops = sum(int(v) for v in dropped.values() if isinstance(v, int | float))
        channels = rec_info.get("channels") or {}
        if isinstance(channels, dict):
            roles = tuple(str(ch.get("role", "")) for ch in channels.values()
                          if isinstance(ch, dict) and ch.get("role"))
    if not roles:
        cfg_ch = (session_info or {}).get("config", {}).get("channels", {})
        if isinstance(cfg_ch, dict):
            roles = tuple(str(ch.get("role", "")) for ch in cfg_ch.values()
                          if isinstance(ch, dict) and ch.get("role"))
    if fps is None:
        fps = (session_info or {}).get("config", {}).get("fps")
    duration_s = (float(frames) / float(fps)) if (frames is not None and fps and fps > 0) else None
    return RecordingEntry(
        path=rec_dir,
        session_dir=session_dir,
        key=f"{session_dir.name}/{rec_dir.name}",
        session_name=session_dir.name,
        recording_name=rec_dir.name,
        created=str((session_info or {}).get("created", "")),
        animal_id=str(meta.get("animal_id", "")),
        operator=str(meta.get("operator", "")),
        condition=str(meta.get("condition", "")),
        notes=str(meta.get("notes", "")),
        frames=None if frames is None else int(frames),
        fps=None if fps is None else float(fps),
        duration_s=duration_s,
        drops=drops,
        complete=rec_info is not None,
        roles=roles,
    )


def scan_recordings(root: Path) -> list[RecordingEntry]:
    """Scan a recording, session, or data_root folder using only lightweight JSON metadata."""
    root = Path(root)
    if not root.exists():
        return []

    if (root / "frames.csv").exists():
        session_info = _load_json(root.parent / "session.json")
        return [_entry_from_recording(root, session_info)]

    if (root / "session.json").exists() or any(root.glob("rec-*/frames.csv")):
        session_dirs = [root]
    else:
        session_dirs = [
            p for p in root.iterdir()
            if p.is_dir() and ((p / "session.json").exists() or any(p.glob("rec-*/frames.csv")))
        ]

    entries: list[RecordingEntry] = []
    for session_dir in sorted(session_dirs, key=lambda p: p.name, reverse=True):
        session_info = _load_json(session_dir / "session.json")
        rec_dirs = sorted(
            (p for p in session_dir.glob("rec-*") if p.is_dir() and (p / "frames.csv").exists()),
            key=lambda p: p.name,
        )
        for rec_dir in rec_dirs:
            entries.append(_entry_from_recording(rec_dir, session_info))
    return entries


class AnalysisQueue:
    """Persistent recording -> selected pipeline IDs + pipeline options (`analysis_queue.json`)."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._selections: dict[str, list[str]] = {}
        self._options: dict[str, dict] = {}
        data = _load_json(self.path)
        if data is not None:
            raw_sel = data.get("selections", {})
            if isinstance(raw_sel, dict):
                self._selections = {
                    str(k): [str(pid) for pid in v]
                    for k, v in raw_sel.items() if isinstance(v, list) and v
                }
            raw_opt = data.get("options", {})
            if isinstance(raw_opt, dict):
                self._options = {
                    str(k): dict(v) for k, v in raw_opt.items() if isinstance(v, dict)
                }

    def selected_pipelines(self, key: str) -> list[str]:
        return list(self._selections.get(key, ()))

    def set_selected(self, key: str, pipeline_id: str, enabled: bool) -> None:
        current = list(self._selections.get(key, ()))
        if enabled and pipeline_id not in current:
            current.append(pipeline_id)
        elif not enabled and pipeline_id in current:
            current.remove(pipeline_id)
        if current:
            self._selections[key] = current
        else:
            self._selections.pop(key, None)
        self._save()

    def all_selected(self) -> list[tuple[str, list[str]]]:
        return [(k, list(v)) for k, v in self._selections.items() if v]

    def options_for(self, pipeline_id: str) -> dict:
        return dict(self._options.get(pipeline_id, {}))

    def set_options(self, pipeline_id: str, options: dict) -> None:
        self._options[pipeline_id] = dict(options)
        self._save()

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"selections": self._selections, "options": self._options}
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2))
        tmp.replace(self.path)
