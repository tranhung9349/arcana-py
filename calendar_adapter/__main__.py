"""Try the adapter without installing dependencies."""

import argparse
from datetime import date, datetime
import json

from .vietnamese import CalendarError, VietnameseCalendar, resolve_maihoa


def main():
    parser = argparse.ArgumentParser(description="Experimental Vietnamese UTC+7 calendar")
    commands = parser.add_subparsers(dest="command", required=True)
    convert = commands.add_parser("date", help="Convert a Gregorian date to the Vietnamese lunar date")
    convert.add_argument("date", type=date.fromisoformat)
    resolve = commands.add_parser("maihoa", help="Map a supplied apparent-solar clock to Y/M/D/H")
    resolve.add_argument("--civil", type=datetime.fromisoformat, required=True)
    resolve.add_argument("--tst", type=datetime.fromisoformat, required=True)
    resolve.add_argument("--kind", choices=("birth", "casting"), default="casting")
    args = parser.parse_args()
    try:
        if args.command == "date":
            result = VietnameseCalendar().describe(args.date)
        else:
            result = resolve_maihoa(args.civil, args.tst, args.kind)
        print(json.dumps({"success": True, "data": result}, ensure_ascii=False, indent=2))
    except CalendarError as error:
        print(json.dumps({"success": False, "error_code": error.code, "message": str(error)}, ensure_ascii=False))
        raise SystemExit(2)


if __name__ == "__main__":
    main()
