import csv
import argparse
from pathlib import Path
from collections import defaultdict


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="data/report_sample.csv",
        help="入力CSVのパス（例: data/report_sample.csv）"
    )
    parser.add_argument(
        "--month",
        default="",
        help="対象月（YYYY-MM）で絞り込み（例: 2026-01）"
    )
    parser.add_argument(
        "--out",
        default="",
        help="出力CSVのパス（例: out/report_2026-01.csv）"
    )
    args = parser.parse_args()

    csv_path = Path(args.input)

    rows = []
    with csv_path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = (row.get("date") or "").strip()
            category = (row.get("category") or "").strip()
            memo = (row.get("memo") or "").strip()
            count_raw = (row.get("count") or "").strip()

            if args.month and not date.startswith(args.month):
                continue

            if not date or not category or not count_raw:
                continue

            try:
                count = int(count_raw)
            except ValueError:
                continue

            rows.append({
                "date": date,
                "category": category,
                "count": count,
                "memo": memo,
            })

    total = sum(r["count"] for r in rows)

    by_cat = defaultdict(int)
    by_date = defaultdict(int)

    for r in rows:
        by_cat[r["category"]] += r["count"]
        by_date[r["date"]] += r["count"]

    print("合計件数:", total)

    print("\nカテゴリ別:")
    for k, v in sorted(by_cat.items(), key=lambda kv: kv[1], reverse=True):
        print(f"  {k}: {v}")

    print("\n日付別:")
    for d, v in sorted(by_date.items()):
        print(f"  {d}: {v}")

    print("\n明細:")
    for r in rows:
        print(f'{r["date"]} {r["category"]} {r["count"]}件 {r["memo"]}')

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        with out_path.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["section", "key", "value"])
            w.writerow(["total", "total", total])

            for cat, v in sorted(by_cat.items(), key=lambda kv: kv[1], reverse=True):
                w.writerow(["category", cat, v])

            for d, v in sorted(by_date.items()):
                w.writerow(["date", d, v])

        print(f"\n✅ レポート保存: {out_path}")


if __name__ == "__main__":
    main()