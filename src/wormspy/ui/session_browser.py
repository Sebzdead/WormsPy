"""SessionBrowser: browse sessions, queue recordings for analysis, and run pipelines."""

from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from wormspy.analysis.catalog import AnalysisQueue, RecordingEntry, scan_recordings
from wormspy.analysis.pipelines import PIPELINES, AnalysisPipeline, PipelineOption, pipeline_by_id


class _PipelineOptionsDialog(QDialog):
    """Generic schema-driven options dialog for any AnalysisPipeline."""

    def __init__(
        self,
        pipeline: AnalysisPipeline,
        current: dict,
        start_dir: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"{pipeline.name} options")
        self.setMinimumWidth(380)
        self._options: tuple[PipelineOption, ...] = pipeline.options
        self._widgets: dict[str, QWidget] = {}

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(8)
        for opt in self._options:
            val = current.get(opt.key, opt.default)
            if opt.kind == "bool":
                cb = QCheckBox(opt.label)
                cb.setChecked(bool(val))
                if opt.help:
                    cb.setToolTip(opt.help)
                self._widgets[opt.key] = cb
                form.addRow("", cb)
            elif opt.kind == "dir":
                edit = QLineEdit(str(val or ""))
                edit.setPlaceholderText("(default)")
                if opt.help:
                    edit.setToolTip(opt.help)
                browse = QPushButton("Browse…")
                browse.clicked.connect(
                    lambda _=False, e=edit, title=opt.label, base=start_dir:
                    self._browse_dir(e, title, base),
                )
                row = QWidget()
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.setSpacing(6)
                row_layout.addWidget(edit, 1)
                row_layout.addWidget(browse)
                self._widgets[opt.key] = edit
                form.addRow(opt.label, row)
            else:
                edit = QLineEdit(str(opt.default if val is None else val))
                if opt.help:
                    edit.setToolTip(opt.help)
                self._widgets[opt.key] = edit
                form.addRow(opt.label, edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def _browse_dir(edit: QLineEdit, label: str, start_dir: str) -> None:
        folder = QFileDialog.getExistingDirectory(edit, f"Choose {label}", edit.text() or start_dir)
        if folder:
            edit.setText(folder)

    def values(self) -> dict:
        out: dict = {}
        for opt in self._options:
            widget = self._widgets[opt.key]
            if isinstance(widget, QCheckBox):
                out[opt.key] = widget.isChecked()
            elif isinstance(widget, QLineEdit):
                text = widget.text().strip()
                out[opt.key] = text if opt.kind == "dir" else (text or opt.default)
        return out


class _PipelineRunner(QThread):
    progress = Signal(int, int, str)
    job_done = Signal(Path)
    finished_all = Signal(int, list)

    def __init__(self, jobs: list[tuple[Path, AnalysisPipeline, dict]]) -> None:
        super().__init__()
        self._jobs = jobs
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        total = len(self._jobs)
        completed = 0
        errors: list[str] = []
        for idx, (rec_dir, pipeline, options) in enumerate(self._jobs):
            if self._cancelled:
                break
            self.progress.emit(idx, total, f"Running {pipeline.name} on {rec_dir.parent.name}/{rec_dir.name}…")
            try:
                pipeline.run(
                    rec_dir,
                    options,
                    lambda msg, i=idx, n=total: self.progress.emit(i, n, msg),
                )
                completed += 1
                self.job_done.emit(rec_dir)
            except Exception as exc:  # noqa: BLE001 - surface error to UI without crashing
                errors.append(f"{rec_dir.parent.name}/{rec_dir.name} ({pipeline.id}): {exc}")
        self.progress.emit(total if not self._cancelled else completed, total, "Finished")
        self.finished_all.emit(completed, errors)


class SessionBrowser(QWidget):
    """Browse WormsPy sessions/recordings and select analysis pipelines per recording."""

    recording_selected = Signal(Path)
    root_change_requested = Signal()
    pipeline_finished = Signal(Path)

    COLUMNS = ("Session / Rec", "Animal", "Operator", "Condition", "Duration", "Pipelines")

    def __init__(self) -> None:
        super().__init__()
        self._root: Path | None = None
        self._entries: list[RecordingEntry] = []
        self._visible: list[RecordingEntry] = []
        self._queue: AnalysisQueue | None = None
        self._current_entry: RecordingEntry | None = None
        self._syncing = False
        self._runner: _PipelineRunner | None = None

        self.root_label = QLabel("No folder open")
        self.root_label.setObjectName("muted")
        self.browse_button = QPushButton("Folder…")
        self.browse_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.browse_button.clicked.connect(self.root_change_requested.emit)
        self.refresh_button = QPushButton("↻")
        self.refresh_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.refresh_button.setToolTip("Rescan sessions")
        self.refresh_button.clicked.connect(self.refresh)

        top_row = QHBoxLayout()
        top_row.setSpacing(6)
        top_row.addWidget(self.root_label, 1)
        top_row.addWidget(self.refresh_button)
        top_row.addWidget(self.browse_button)

        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filter animal, operator, condition…")
        self.filter_edit.textChanged.connect(self._apply_filter)
        self.selected_only_box = QCheckBox("Selected")
        self.selected_only_box.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.selected_only_box.toggled.connect(self._apply_filter)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(6)
        filter_row.addWidget(self.filter_edit, 1)
        filter_row.addWidget(self.selected_only_box)

        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

        # Pipeline selector box
        pipe_box = QGroupBox("SEND TO ANALYSIS PIPELINES")
        pipe_layout = QVBoxLayout(pipe_box)
        pipe_layout.setSpacing(6)

        self.target_label = QLabel("Select a recording above")
        self.target_label.setObjectName("muted")
        pipe_layout.addWidget(self.target_label)

        self.pipeline_checks: dict[str, QCheckBox] = {}
        self.pipeline_option_buttons: dict[str, QPushButton] = {}
        for pipeline in PIPELINES:
            cb = QCheckBox(pipeline.name)
            cb.setToolTip(pipeline.description)
            cb.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            cb.toggled.connect(lambda checked, pid=pipeline.id: self._on_pipeline_toggled(pid, checked))
            self.pipeline_checks[pipeline.id] = cb

            row_layout = QHBoxLayout()
            row_layout.setSpacing(6)
            row_layout.addWidget(cb, 1)
            if pipeline.options:
                opts_btn = QPushButton("Options…")
                opts_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                opts_btn.setToolTip(f"Configure {pipeline.name} options")
                opts_btn.clicked.connect(
                    lambda _=False, p=pipeline: self._edit_pipeline_options(p),
                )
                self.pipeline_option_buttons[pipeline.id] = opts_btn
                row_layout.addWidget(opts_btn)
            pipe_layout.addLayout(row_layout)

        self.run_current_button = QPushButton("Run this recording")
        self.run_current_button.setToolTip(
            "Run the checked pipelines on the currently open recording",
        )
        self.run_current_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.run_current_button.clicked.connect(self.run_current)
        self.run_selected_button = QPushButton("Run all queued (0)")
        self.run_selected_button.setToolTip(
            "Run every checked pipeline across all recordings in the list",
        )
        self.run_selected_button.setProperty("role", "primary")
        self.run_selected_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.run_selected_button.clicked.connect(self.run_selected)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.cancel_button.clicked.connect(self.stop_runner)
        self.cancel_button.hide()

        run_row = QHBoxLayout()
        run_row.setSpacing(6)
        run_row.addWidget(self.run_current_button)
        run_row.addWidget(self.run_selected_button, 1)
        run_row.addWidget(self.cancel_button)
        pipe_layout.addLayout(run_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.hide()
        self.runner_status = QLabel("")
        self.runner_status.setObjectName("muted")
        self.runner_status.setWordWrap(True)
        pipe_layout.addWidget(self.progress_bar)
        pipe_layout.addWidget(self.runner_status)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addLayout(top_row)
        layout.addLayout(filter_row)
        layout.addWidget(self.table, 1)
        layout.addWidget(pipe_box)

        self._update_pipeline_controls()

    @property
    def entries(self) -> list[RecordingEntry]:
        return list(self._entries)

    def visible_entries(self) -> list[RecordingEntry]:
        return list(self._visible)

    def set_root(self, root: Path) -> None:
        self._root = Path(root)
        self.root_label.setText(self._root.name or str(self._root))
        self.root_label.setToolTip(str(self._root))
        self._queue = AnalysisQueue(self._root / "analysis_queue.json")
        self.refresh()

    def refresh(self) -> None:
        if self._root is None:
            return
        self._entries = scan_recordings(self._root)
        self._apply_filter()

    def select_recording(self, path: Path) -> None:
        resolved = Path(path).resolve()
        matched = next((e for e in self._entries if e.path.resolve() == resolved), None)
        self._current_entry = matched
        self._syncing = True
        try:
            if matched is not None and matched in self._visible:
                row = self._visible.index(matched)
                self.table.selectRow(row)
            else:
                self.table.clearSelection()
        finally:
            self._syncing = False
        self._update_pipeline_controls()

    def _apply_filter(self) -> None:
        query = self.filter_edit.text().strip().lower()
        only_sel = self.selected_only_box.isChecked()
        visible: list[RecordingEntry] = []
        for entry in self._entries:
            if only_sel and not self._selected_for(entry.key):
                continue
            if query:
                haystack = (f"{entry.key} {entry.animal_id} {entry.operator} "
                            f"{entry.condition} {entry.notes}").lower()
                if query not in haystack:
                    continue
            visible.append(entry)
        self._visible = visible
        self._populate_table()
        if self._current_entry is not None:
            self.select_recording(self._current_entry.path)
        else:
            self._update_pipeline_controls()

    def _populate_table(self) -> None:
        self._syncing = True
        try:
            self.table.setRowCount(len(self._visible))
            for row, entry in enumerate(self._visible):
                dur = self._format_duration(entry.duration_s)
                if not entry.complete:
                    dur = f"{dur} !"
                selected = self._format_pipeline_badges(self._selected_for(entry.key))
                vals = (entry.key, entry.animal_id, entry.operator, entry.condition, dur, selected)
                for col, text in enumerate(vals):
                    item = QTableWidgetItem(text)
                    self.table.setItem(row, col, item)
        finally:
            self._syncing = False

    def _selected_for(self, key: str) -> list[str]:
        return [] if self._queue is None else self._queue.selected_pipelines(key)

    @staticmethod
    def _format_pipeline_badges(pids: list[str]) -> str:
        labels: list[str] = []
        for pid in pids:
            try:
                labels.append(pipeline_by_id(pid).short_name)
            except KeyError:
                labels.append(pid)
        return ", ".join(labels)

    def _options_for(self, pipeline_id: str) -> dict:
        defaults = {opt.key: opt.default for opt in pipeline_by_id(pipeline_id).options}
        if self._queue is not None:
            defaults.update(self._queue.options_for(pipeline_id))
        return defaults

    def _on_selection_changed(self) -> None:
        if self._syncing:
            return
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        row = rows[0].row()
        if 0 <= row < len(self._visible):
            entry = self._visible[row]
            self._current_entry = entry
            self._update_pipeline_controls()
            self.recording_selected.emit(entry.path)

    def _on_pipeline_toggled(self, pipeline_id: str, checked: bool) -> None:
        if self._syncing or self._current_entry is None or self._queue is None:
            return
        self._queue.set_selected(self._current_entry.key, pipeline_id, checked)
        self._refresh_row_pipelines(self._current_entry)
        self._update_run_buttons()

    def _refresh_row_pipelines(self, entry: RecordingEntry) -> None:
        if entry not in self._visible:
            return
        row = self._visible.index(entry)
        item = self.table.item(row, 5)
        if item is not None:
            item.setText(self._format_pipeline_badges(self._selected_for(entry.key)))

    def _update_pipeline_controls(self) -> None:
        entry = self._current_entry
        if entry is None:
            self.target_label.setText("Select a recording above")
        else:
            self.target_label.setText(f"For {entry.session_name} / {entry.recording_name}")
        selected = set(self._selected_for(entry.key)) if entry is not None else set()
        self._syncing = True
        try:
            for pipeline in PIPELINES:
                cb = self.pipeline_checks[pipeline.id]
                opts_btn = self.pipeline_option_buttons.get(pipeline.id)
                if opts_btn is not None:
                    opts_btn.setEnabled(self._runner is None and self._queue is not None)
                if entry is None:
                    cb.setText(pipeline.name)
                    cb.setChecked(False)
                    cb.setEnabled(False)
                    continue
                opts = self._options_for(pipeline.id)
                done = pipeline.is_done(entry.path, opts)
                cb.setText(f"{pipeline.name} [done]" if done else pipeline.name)
                compat = pipeline.compatible(entry.roles)
                cb.setEnabled(compat and self._runner is None)
                cb.setChecked(pipeline.id in selected)
                if not compat:
                    cb.setToolTip(f"Requires roles: {', '.join(pipeline.required_roles)}")
                else:
                    cb.setToolTip(pipeline.description)
        finally:
            self._syncing = False
        self._update_run_buttons()

    def _update_run_buttons(self) -> None:
        running = self._runner is not None
        current_count = (
            len(self._selected_for(self._current_entry.key))
            if self._current_entry is not None else 0
        )
        total_jobs = sum(len(pids) for _, pids in (self._queue.all_selected() if self._queue else ()))
        self.run_current_button.setEnabled(not running and current_count > 0)
        self.run_selected_button.setText(f"Run all queued ({total_jobs})")
        self.run_selected_button.setEnabled(not running and total_jobs > 0)
        self.cancel_button.setVisible(running)

    def _edit_pipeline_options(self, pipeline: AnalysisPipeline) -> None:
        if self._queue is None:
            return
        current = self._options_for(pipeline.id)
        dlg = _PipelineOptionsDialog(pipeline, current, str(self._root or ""), self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._queue.set_options(pipeline.id, dlg.values())
            self._update_pipeline_controls()

    # --- execution ------------------------------------------------------------------------

    def run_current(self) -> None:
        if self._current_entry is None:
            return
        jobs = [
            (self._current_entry.path, pipeline_by_id(pid), self._options_for(pid))
            for pid in self._selected_for(self._current_entry.key)
        ]
        self.run_jobs(jobs)

    def run_selected(self) -> None:
        if self._queue is None:
            return
        by_key = {entry.key: entry for entry in self._entries}
        jobs: list[tuple[Path, AnalysisPipeline, dict]] = []
        for key, pids in self._queue.all_selected():
            entry = by_key.get(key)
            if entry is None:
                continue
            for pid in pids:
                jobs.append((entry.path, pipeline_by_id(pid), self._options_for(pid)))
        self.run_jobs(jobs)

    def run_jobs(self, jobs: list[tuple[Path, AnalysisPipeline, dict]]) -> None:
        if not jobs or self._runner is not None:
            return
        self.progress_bar.setRange(0, len(jobs))
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.runner_status.setText(f"Starting {len(jobs)} job(s)…")
        self._runner = _PipelineRunner(jobs)
        self._runner.progress.connect(self._on_progress)
        self._runner.job_done.connect(self._on_job_done)
        self._runner.finished_all.connect(self._on_finished_all)
        self._update_pipeline_controls()
        self._runner.start()

    def stop_runner(self) -> None:
        if self._runner is not None:
            self._runner.cancel()
            self._runner.wait(5000)

    def _on_progress(self, done: int, total: int, message: str) -> None:
        self.progress_bar.setRange(0, max(total, 1))
        self.progress_bar.setValue(done)
        self.runner_status.setText(message)

    def _on_job_done(self, rec_dir: Path) -> None:
        self._update_pipeline_controls()
        self.pipeline_finished.emit(rec_dir)

    def _on_finished_all(self, ok_count: int, errors: list[str]) -> None:
        runner = self._runner
        self._runner = None
        if runner is not None:
            runner.wait()
            runner.deleteLater()
        self.progress_bar.hide()
        if errors:
            self.runner_status.setText(f"{ok_count} done, {len(errors)} failed: {errors[0]}")
        else:
            self.runner_status.setText(f"Completed {ok_count} pipeline job(s).")
        self._update_pipeline_controls()

    @staticmethod
    def _format_duration(seconds: float | None) -> str:
        if seconds is None:
            return "—"
        mins, secs = divmod(max(0, round(seconds)), 60)
        return f"{mins:02d}:{secs:02d}"
