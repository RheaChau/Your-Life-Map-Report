#!/usr/bin/env python3
"""Calculate forecast windows relative to a verified as-of date."""
import argparse
import calendar
import json
from datetime import date


def add_months(value, months):
    year = value.year + (value.month - 1 + months) // 12
    month = (value.month - 1 + months) % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", required=True, help="YYYY-MM-DD")
    args = parser.parse_args()
    try:
        anchor = date.fromisoformat(args.as_of)
    except ValueError:
        parser.error("as-of 必须为 YYYY-MM-DD")
    try:
        three_years = anchor.replace(year=anchor.year + 3)
    except ValueError:  # Feb 29 in a non-leap target year
        three_years = anchor.replace(year=anchor.year + 3, day=28)
    three_months = add_months(anchor, 3)
    result = {
        "anchor_date": anchor.isoformat(),
        "next_3_years": {"start": anchor.isoformat(), "end": three_years.isoformat(), "years": [anchor.year, anchor.year + 1, anchor.year + 2]},
        "next_3_months": {"start": anchor.isoformat(), "end": three_months.isoformat()}
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
