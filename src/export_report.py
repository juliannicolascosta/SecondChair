"""CLI entry point for the safe, anonymized daily report."""

import argparse
import json
from datetime import date

from src.analytics.export import anonymous_daily_report, render_anonymous_report


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m src.export_report")
    parser.add_argument("--day", type=date.fromisoformat)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = anonymous_daily_report(args.day)
    if args.json:
        print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
    else:
        render_anonymous_report(report)


if __name__ == "__main__":
    main()
