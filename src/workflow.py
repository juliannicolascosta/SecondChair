"""CLI for manually delimited workflow traces."""

import argparse
import json

from src.workflows.repository import WorkflowTraceRepository
from src.workflows.reports import anonymous_trace, compare_traces, render_trace


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m src.workflow")
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("start")
    start.add_argument("label")
    commands.add_parser("stop")
    commands.add_parser("cancel")
    show = commands.add_parser("show")
    show.add_argument("trace_id")
    compare = commands.add_parser("compare")
    compare.add_argument("first_id")
    compare.add_argument("second_id")
    export = commands.add_parser("export")
    export.add_argument("trace_id")
    args = parser.parse_args(argv)
    repository = WorkflowTraceRepository()

    if args.command == "start":
        render_trace(repository.start(args.label))
    elif args.command == "stop":
        render_trace(repository.finish())
    elif args.command == "cancel":
        render_trace(repository.finish(cancelled=True))
    elif args.command == "show":
        render_trace(repository.get(args.trace_id))
    elif args.command == "compare":
        print(json.dumps(compare_traces(repository.get(args.first_id), repository.get(args.second_id)), indent=2))
    elif args.command == "export":
        print(json.dumps(anonymous_trace(repository.get(args.trace_id)), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
