from flask import Flask, request, Response
import sqlite3
from pathlib import Path
import csv
import io

app = Flask(__name__)

DB_PATH = Path("data/report.db")


def query_report(month: str | None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    where = ""
    params = ()
    if month:
        where = "WHERE date LIKE ?"
        params = (month + "%",)

    cur.execute(f'SELECT COALESCE(SUM("count"), 0) FROM reports {where}', params)
    total = cur.fetchone()[0]

    cur.execute(
        f'''
        SELECT category, SUM("count") AS total
        FROM reports
        {where}
        GROUP BY category
        ORDER BY total DESC
        ''',
        params,
    )
    rows_cat = cur.fetchall()

    cur.execute(
        f'''
        SELECT date, SUM("count") AS total
        FROM reports
        {where}
        GROUP BY date
        ORDER BY date
        ''',
        params,
    )
    rows_date = cur.fetchall()

    conn.close()
    return total, rows_cat, rows_date

def list_months() -> list[str]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT SUBSTR(date, 1, 7) AS month
        FROM reports
        ORDER BY month
    """)
    months = [row[0] for row in cur.fetchall()]
    conn.close()
    return months

@app.get("/")
def index():
    months = list_months() if DB_PATH.exists() else []
    options = "\n".join(f'<option value="{m}">{m}</option>' for m in months)

    return f"""
    <!doctype html>
    <html lang="ja">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>monthly_report_tool</title>
        <style>
          body {{ font-family: system-ui, -apple-system, sans-serif; padding: 16px; line-height: 1.7; }}
          a, button, select {{ font-size: 16px; }}
          select, button {{ padding: 8px; }}
        </style>
      </head>
      <body>
        <h1>monthly_report_tool</h1>
        <p>対象月を選択して月次レポートを表示します。空欄なら全期間です。</p>

        <form action="/report" method="get">
          <label for="month">対象月（YYYY-MM）</label><br>
          <select id="month" name="month">
            <option value="">（全期間）</option>
            {options}
          </select>
          <button type="submit">集計</button>
        </form>
      </body>
    </html>
    """


@app.get("/report")
def report():
    month = request.args.get("month", "").strip() or None

    if not DB_PATH.exists():
        return f"""
        <h1>DBが見つかりません</h1>
        <p>{DB_PATH} が存在しません。</p>
        <p>先に以下を実行してください：</p>
        <pre>python src/import_sqlite.py --input data/report_sample.csv --db data/report.db</pre>
        <p><a href="/download?month={month or ''}">CSVをダウンロード</a></p>
        <p><a href="/">戻る</a></p>
        """

    total, rows_cat, rows_date = query_report(month)

    title = f"月次レポート（月: {month}）" if month else "月次レポート（全期間）"

    rows_cat_html = "\n".join(
        f"<tr><td>{cat}</td><td>{v}</td></tr>"
        for cat, v in rows_cat
    )
    rows_date_html = "\n".join(
        f"<tr><td>{d}</td><td>{v}</td></tr>"
        for d, v in rows_date
    )

    return f"""
    <!doctype html>
    <html lang="ja">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{title}</title>
      </head>
      <body>
        <h1>{title}</h1>
        <p>合計件数: <strong>{total}</strong></p>

        <h2>カテゴリ別</h2>
        <table border="1" cellspacing="0" cellpadding="6">
          <thead>
            <tr><th>カテゴリ</th><th>件数</th></tr>
          </thead>
          <tbody>
            {rows_cat_html}
          </tbody>
        </table>

        <h2>日付別</h2>
        <table border="1" cellspacing="0" cellpadding="6">
          <thead>
            <tr><th>日付</th><th>件数</th></tr>
          </thead>
          <tbody>
            {rows_date_html}
          </tbody>
        </table>

        <p><a href="/download?month={month or ''}">CSVをダウンロード</a></p>
        <p><a href="/">戻る</a></p>
      </body>
    </html>
    """
@app.get("/download")
def download():
    month = request.args.get("month", "").strip() or None

    if not DB_PATH.exists():
        return "DBが見つかりません", 404

    total, rows_cat, rows_date = query_report(month)

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["section", "key", "value"])
    w.writerow(["total", "total", total])

    for cat, v in rows_cat:
        w.writerow(["category", cat, v])

    for d, v in rows_date:
        w.writerow(["date", d, v])

    filename = f"report_{month}.csv" if month else "report_all.csv"
    csv_text = buf.getvalue()
    buf.close()

    return Response(
        csv_text,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

if __name__ == "__main__":
    app.run(debug=True, port=5002)