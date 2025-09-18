from flask import Flask, request, jsonify
from flask_cors import CORS
import csv, os, datetime

CSV_FILE = os.environ.get("CSV_FILE", "records.csv")

app = Flask(__name__)
CORS(app)

FIELDS = ["ts","date_shift","inspector","part_no","lot_prefix","lot_mid","lot_tail","lot_full","qty","remark"]

def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat(timespec="seconds")

def read_rows():
    if not os.path.exists(CSV_FILE):
        return []
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_row(row: dict):
    write_header = not os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if write_header:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in FIELDS})

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/api/records")
def get_records():
    rows = read_rows()
    date = request.args.get("date")
    shift = request.args.get("shift")
    limit = int(request.args.get("limit", "50"))
    if date or shift:
        out = []
        for r in rows:
            ds = r.get("date_shift","")
            ok = True
            if date:
                ok = (date in ds) or (r.get("ts","").startswith(date))
            if ok and shift:
                ok = (f"-{shift}" in ds)
            if ok:
                out.append(r)
        rows = out
    return jsonify(list(reversed(rows[-limit:])))

@app.post("/api/records")
def post_record():
    data = request.get_json(silent=True) or {}
    lot_full = data.get("lot_full") or "-".join([p for p in [data.get("lot_prefix"), data.get("lot_mid"), data.get("lot_tail")] if p])
    row = {
        "ts": data.get("ts") or now_iso(),
        "date_shift": data.get("date_shift",""),
        "inspector": data.get("inspector",""),
        "part_no": data.get("part_no",""),
        "lot_prefix": data.get("lot_prefix",""),
        "lot_mid": data.get("lot_mid",""),
        "lot_tail": data.get("lot_tail",""),
        "lot_full": lot_full,
        "qty": str(data.get("qty","")),
        "remark": data.get("remark",""),
    }
    missing = [k for k in ["date_shift","inspector","part_no","qty"] if not row[k]]
    if missing:
        return jsonify({"error":"missing_fields","fields":missing}), 400

    force = request.args.get("force") == "1"
    if not force:
        rows = read_rows()
        for r in reversed(rows):
            if (r.get("date_shift")==row["date_shift"] and
                r.get("part_no")==row["part_no"] and
                r.get("lot_full")==row["lot_full"] and
                r.get("inspector")!=row["inspector"]):
                return jsonify({"error":"conflict_other_inspector","existing":r}), 409

    write_row(row)
    return jsonify({"status":"ok"}), 201

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)
