#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import create_project_overview_summary
from services.overview_summary_service import generate_project_overview_summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate project overview summary")
    parser.add_argument("--project-id", type=int, required=True, help="Project ID")
    parser.add_argument("--month", type=str, default=None, help="Target month in YYYY-MM (default: current month)")
    parser.add_argument("--dry-run", action="store_true", help="Print summary without inserting")
    parser.add_argument("--generated-by", type=str, default=None, help="Optional generated_by value")
    args = parser.parse_args(argv)

    result = generate_project_overview_summary(args.project_id, target_month=args.month)

    print(result.summary_text)

    if args.dry_run:
        return 0

    summary_id = create_project_overview_summary(
        project_id=args.project_id,
        summary_text=result.summary_text,
        summary_json=result.summary_json,
        summary_month=result.summary_month,
        generated_by=args.generated_by,
    )
    if not summary_id:
        print("Failed to insert summary.")
        return 1

    print(f"\nInserted summary_id={summary_id} for project_id={args.project_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
