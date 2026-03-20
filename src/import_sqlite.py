import argparse
import csv
import sqlite3
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/report_sample.csv", help="入力CSVパス")
    parser.add_argument("--db", default="data/report.db", help="出力DBパス")
    args = parser.parse_args()

    csv_path = Path(args.input)
    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            count INTEGER NOT NULL,
            memo TEXT
        )
        """
    )

    cur.execute("DELETE FROM reports")

    inserted = 0
    with csv_path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = (row.get("date") or "").strip()
            category = (row.get("category") or "").strip()
            memo = (row.get("memo") or "").strip()
            count_raw = (row.get("count") or "").strip()

            if not date or not category or not count_raw:
                continue

            try:
                count = int(count_raw)
            except ValueError:
                continue

            cur.execute(
                "INSERT INTO reports(date, category, count, memo) VALUES (?, ?, ?, ?)",
                (date, category, count, memo),
            )
            inserted += 1

    conn.commit()
    cur.execute("CREATE INDEX IF NOT EXISTS idx_reports_date ON reports(date)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_reports_category ON reports(category)")
    conn.commit()
    conn.close()

    print(f"✅ imported: {inserted} rows -> {db_path}")


if __name__ == "__main__":
    main()