#!/usr/bin/env python3

import os
import sys
import sqlite3
import argparse
from datetime import datetime, timedelta
from pathlib import Path

def get_db():
    db_dir = Path.home() / ".local" / "share" / "done"
    db_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_dir / "done.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            message TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn

def parse_date(date_str, end_of_day=False):
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(date_str, fmt)
            if end_of_day:
                return dt.replace(hour=23, minute=59, second=59)
            return dt.replace(hour=0, minute=0, second=0)
        except ValueError:
            pass
    raise ValueError(f"Invalid date format: '{date_str}'. Expected format DD.MM.YYYY")

def log_action(message):
    conn = get_db()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("INSERT INTO logs (timestamp, message) VALUES (?, ?)", (now_str, message))
    conn.commit()
    conn.close()

def show_stats(from_str=None, until_str=None):
    now = datetime.now()
    
    if from_str:
        start_dt = parse_date(from_str, end_of_day=False)
    else:
        start_dt = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0)

    if until_str:
        end_dt = parse_date(until_str, end_of_day=True)
    else:
        end_dt = now.replace(hour=23, minute=59, second=59)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, timestamp, message FROM logs WHERE timestamp >= ? AND timestamp <= ? ORDER BY timestamp ASC",
        (start_dt.strftime("%Y-%m-%d %H:%M:%S"), end_dt.strftime("%Y-%m-%d %H:%M:%S"))
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("No logs found for the specified period.")
        return

    formatted_rows = []
    for row in rows:
        row_id, ts_str, msg = row
        dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
        date_formatted = dt.strftime("%d.%m.%Y")
        time_formatted = dt.strftime("%H:%M")
        formatted_rows.append({
            "id": str(row_id),
            "date": date_formatted,
            "time": time_formatted,
            "message": msg,
            "dt_date": dt.date()
        })

    id_width = max(len("ID"), max(len(r["id"]) for r in formatted_rows))
    date_width = max(len("Date"), max(len(r["date"]) for r in formatted_rows))
    time_width = max(len("Time"), max(len(r["time"]) for r in formatted_rows))
    msg_width = max(len("Action"), max(len(r["message"]) for r in formatted_rows))

    header = f"{'ID':<{id_width}}  {'Date':<{date_width}}  {'Time':<{time_width}}  {'Action':<{msg_width}}"
    separator = f"{'-' * id_width}  {'-' * date_width}  {'-' * time_width}  {'-' * msg_width}"

    print(header)
    print(separator)

    last_date = None
    for r in formatted_rows:
        if last_date is not None and r["dt_date"] != last_date:
            print()
        print(f"{r['id']:<{id_width}}  {r['date']:<{date_width}}  {r['time']:<{time_width}}  {r['message']:<{msg_width}}")
        last_date = r["dt_date"]

def main():
    parser = argparse.ArgumentParser(prog="done", description="Simple activity logger.")
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--from", dest="from_date", type=str)
    parser.add_argument("--until", dest="until_date", type=str)
    parser.add_argument("message", nargs="*", type=str)

    args = parser.parse_args()

    if args.stats or args.from_date or args.until_date:
        show_stats(args.from_date, args.until_date)
    elif args.message:
        msg = " ".join(args.message)
        log_action(msg)
        print(f"Logged: {msg}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
