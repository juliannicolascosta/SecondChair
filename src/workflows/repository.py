"""SQLite persistence for manual workflow boundaries and aggregate sessions."""

import json
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from src.storage.database import DATABASE, connect, initialize
from src.workflows.models import WorkflowTrace


METRICS = (
    "interaction_count", "mouse_clicks", "keyboard_actions", "scroll_actions",
    "text_fields_used", "buttons_used", "combo_boxes_used", "menus_used",
    "window_switches",
)


class WorkflowTraceRepository:
    def __init__(self, database=DATABASE, clock=datetime.now):
        self.database = Path(database)
        self.clock = clock
        initialize(self.database)

    def start(self, label):
        label = " ".join(label.split())
        if not label or len(label) > 120:
            raise ValueError("label must contain 1 to 120 characters")
        now = self.clock()
        trace_id = str(uuid4())
        try:
            with closing(connect(self.database)) as conn, conn:
                conn.execute(
                    "INSERT INTO workflow_traces VALUES (?,?,?,?,?,?)",
                    (trace_id, label, now.isoformat(), None, "running", now.isoformat()),
                )
        except sqlite3.IntegrityError as error:
            raise RuntimeError("a workflow trace is already running") from error
        return self.get(trace_id)

    def attach_session(self, session):
        with closing(connect(self.database)) as conn, conn:
            active = conn.execute(
                "SELECT id FROM workflow_traces WHERE status='running'"
            ).fetchone()
            if active is None:
                return False
            conn.execute(
                """INSERT OR IGNORE INTO workflow_trace_sessions VALUES (
                ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (active[0], session.learning_id, session.start_time.isoformat(),
                 session.end_time.isoformat(), session.duration,
                 json.dumps(session.applications_used), json.dumps(session.processes_used),
                 session.events_count, session.context_switches,
                 *(getattr(session, name, 0) for name in METRICS),
                 session.control_metrics_status),
            )
        return True

    def finish(self, cancelled=False, end_time=None):
        now = end_time or self.clock()
        status = "cancelled" if cancelled else "completed"
        with closing(connect(self.database)) as conn, conn:
            row = conn.execute(
                "SELECT id FROM workflow_traces WHERE status='running'"
            ).fetchone()
            if row is None:
                raise RuntimeError("no workflow trace is running")
            conn.execute(
                "UPDATE workflow_traces SET end_time=?, status=? WHERE id=?",
                (now.isoformat(), status, row[0]),
            )
        return self.get(row[0])

    def finalize_pending(self, collector):
        """Persist exact interaction slices for traces closed by the manual CLI."""
        with closing(connect(self.database)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT t.id, t.start_time, t.end_time
                FROM workflow_traces t
                LEFT JOIN workflow_trace_intervals i ON i.trace_id=t.id
                WHERE t.status='completed' AND t.end_time IS NOT NULL AND i.trace_id IS NULL
                ORDER BY t.end_time
            """).fetchall()
        for row in rows:
            result = collector.aggregate_between(
                datetime.fromisoformat(row["start_time"]),
                datetime.fromisoformat(row["end_time"]),
            )
            counters = result["counters"]
            with closing(connect(self.database)) as conn, conn:
                conn.execute(
                    """INSERT OR IGNORE INTO workflow_trace_intervals VALUES (
                    ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (row["id"], json.dumps(result["applications"]),
                     json.dumps(result["processes"]),
                     *(getattr(counters, name) for name in METRICS),
                     result["control_metrics_status"], result["control_metrics_reason"],
                     self.clock().isoformat()),
                )
        return len(rows)

    def get(self, trace_id):
        with closing(connect(self.database)) as conn:
            conn.row_factory = sqlite3.Row
            trace = conn.execute(
                "SELECT * FROM workflow_traces WHERE id=?", (trace_id,)
            ).fetchone()
            if trace is None:
                raise KeyError(trace_id)
            sessions = conn.execute(
                "SELECT * FROM workflow_trace_sessions WHERE trace_id=? ORDER BY start_time",
                (trace_id,),
            ).fetchall()
            interval = conn.execute(
                "SELECT * FROM workflow_trace_intervals WHERE trace_id=?", (trace_id,)
            ).fetchone()
        return self._build(trace, sessions, interval)

    def current(self):
        with closing(connect(self.database)) as conn:
            row = conn.execute(
                "SELECT id FROM workflow_traces WHERE status='running'"
            ).fetchone()
        return self.get(row[0]) if row is not None else None

    def list(self, label=None):
        sql = "SELECT id FROM workflow_traces"
        params = ()
        if label is not None:
            sql += " WHERE label=?"
            params = (label,)
        with closing(connect(self.database)) as conn:
            rows = conn.execute(sql + " ORDER BY start_time DESC", params).fetchall()
        return [self.get(row[0]) for row in rows]

    @staticmethod
    def _build(row, sessions, interval=None):
        applications, processes = [], []
        for session in sessions:
            for target, column in ((applications, "applications"), (processes, "processes")):
                for value in json.loads(session[column]):
                    if value not in target:
                        target.append(value)
        statuses = {session["control_metrics_status"] for session in sessions}
        controls_available = bool(sessions) and statuses != {"unavailable"}
        control_status = (
            "partial" if len(statuses) > 1 or "partial" in statuses
            else (next(iter(statuses)) if statuses else "unavailable")
        )
        summed = lambda name: sum(session[name] for session in sessions)
        controls = {
            name: summed(name) if controls_available else None
            for name in ("text_fields_used", "buttons_used", "combo_boxes_used", "menus_used")
        }
        if interval is not None:
            applications = json.loads(interval["applications"])
            processes = json.loads(interval["processes"])
            control_status = interval["control_metrics_status"]
            controls_available = control_status != "unavailable"
            controls = {
                name: interval[name] if controls_available else None
                for name in ("text_fields_used", "buttons_used", "combo_boxes_used", "menus_used")
            }
            interaction_values = {name: interval[name] for name in METRICS}
        else:
            interaction_values = {name: summed(name) for name in METRICS}
        return WorkflowTrace(
            id=row["id"], label=row["label"], start_time=datetime.fromisoformat(row["start_time"]),
            end_time=datetime.fromisoformat(row["end_time"]) if row["end_time"] else None,
            status=row["status"], work_session_ids=tuple(s["session_key"] for s in sessions),
            applications_used=tuple(applications), processes_used=tuple(processes),
            window_count=summed("window_count"), context_switches=summed("context_switches"),
            interaction_count=interaction_values["interaction_count"],
            mouse_clicks=interaction_values["mouse_clicks"],
            keyboard_actions=interaction_values["keyboard_actions"],
            scroll_actions=interaction_values["scroll_actions"],
            window_switches=interaction_values["window_switches"],
            control_metrics_status=control_status,
            interaction_metrics_status=(
                "exact" if interval is not None else
                "session_aggregate" if sessions else
                "collecting" if row["status"] == "running" else "pending"
            ),
            **controls,
        )
