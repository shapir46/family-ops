"""CLI: python -m familyops <command>

  collect [--date YYYY-MM-DD] [--no-save]   scripted sources -> state/<date>.json; prints summary + due checks
  add --events f.json [--actions f.json] [--fyi f.json] [--date D]   merge Claude-collected items into state
  check-email --html f.html --to a,b [--shadow] [--date D]          pre-send validation (exit 1 on problems)
  checked <source> [--date D]               record that a weekly/yearly source was re-checked
  lunch [--date D]                          today's lunch line
  paper-link [--date D]                     no-login link to the day's newspaper (needs env PAPER_LINK_KEY)
"""
import argparse
import json
import sys
from datetime import date
from zoneinfo import ZoneInfo
from datetime import datetime

from . import TZ, collect, lunch, paperlink, validate


def _today(s):
    return date.fromisoformat(s) if s else datetime.now(ZoneInfo(TZ)).date()


def main(argv=None):
    ap = argparse.ArgumentParser(prog="familyops")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("collect"); c.add_argument("--date"); c.add_argument("--no-save", action="store_true")
    a = sub.add_parser("add"); a.add_argument("--date"); a.add_argument("--events"); a.add_argument("--actions"); a.add_argument("--fyi")
    v = sub.add_parser("check-email"); v.add_argument("--html", required=True); v.add_argument("--to", required=True)
    v.add_argument("--shadow", action="store_true"); v.add_argument("--date")
    k = sub.add_parser("checked"); k.add_argument("source"); k.add_argument("--date")
    l = sub.add_parser("lunch"); l.add_argument("--date")
    pl = sub.add_parser("paper-link"); pl.add_argument("--date")
    args = ap.parse_args(argv)
    today = _today(getattr(args, "date", None))

    if args.cmd == "collect":
        st = collect.collect(today)
        path = None if args.no_save else collect.save(st)
        print(json.dumps({"state": path, "events": len(st["events"]), "lunch": (st["lunch"] or {}).get("line"),
                          "weather": bool(st["weather"]), "sources": st["meta"]["sources"],
                          "warnings": st["meta"]["warnings"], "due": st["due"]}, indent=1))
    elif args.cmd == "add":
        p = collect.STATE_DIR / f"{today.isoformat()}.json"
        st = json.loads(p.read_text())
        load = lambda f: json.loads(open(f).read()) if f else []
        st = collect.add(st, load(args.events), load(args.actions), load(args.fyi))
        p.write_text(json.dumps(st, indent=1, ensure_ascii=False))
        print(f"{p}: {len(st['events'])} events, {len(st['actions'])} actions, {len(st['fyi'])} fyi")
    elif args.cmd == "check-email":
        probs = validate.outgoing(open(args.html).read(), args.to.split(","), today, args.shadow)
        print("\n".join(probs) if probs else "OK")
        return 1 if probs else 0
    elif args.cmd == "checked":
        collect.mark_checked(args.source, today)
        print(f"{args.source} checked {today}")
    elif args.cmd == "lunch":
        print(lunch.for_day(today)["line"])
    elif args.cmd == "paper-link":
        print(paperlink.link(today))
    return 0


if __name__ == "__main__":
    sys.exit(main())
