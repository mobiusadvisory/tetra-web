#!/usr/bin/env python3
"""Refresh the oil price history and rebuild portal/tools/oil-prices/data.json.

Stored CSVs in data/oil-prices are the master copy. Feeds only add or correct rows;
a row is never removed, because the EIA daily files lost about 1,600 historical rows
in September 2026. With --offline, no feeds are read.

Feeds are read in order and later ones win on any date they share, so the most
authoritative source (EIA) goes last. FRED often times out from GitHub's runners.
"""
import csv, datetime as dt, io, json, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA, OUT = ROOT / "data/oil-prices", ROOT / "portal/tools/oil-prices/data.json"
FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="
HUB = "https://raw.githubusercontent.com/datasets/"
EIA = "https://www.eia.gov/dnav/pet/hist_xls/"
FEEDS = {
    "brent_daily.csv": ("price", HUB + "oil-prices/main/data/brent-daily.csv", FRED + "DCOILBRENTEU", EIA + "RBRTEd.xls"),
    "wti_daily.csv": ("price", HUB + "oil-prices/main/data/wti-daily.csv", FRED + "DCOILWTICO", EIA + "RWTCd.xls"),
    "us_cpi_monthly.csv": ("cpi", HUB + "cpi-us/main/data/cpiai.csv", FRED + "CPIAUCNS"),
}


def read(name):
    with open(DATA / name, newline="") as f:
        return {r["date"]: float(r[list(r)[1]]) for r in csv.DictReader(f)}


def parse_eia(raw):
    """EIA history workbook: sheet 'Data 1', three header rows, Excel dates in column A."""
    import xlrd
    book = xlrd.open_workbook(file_contents=raw)
    sheet = book.sheet_by_name("Data 1")
    out = {}
    for i in range(3, sheet.nrows):
        d, v = sheet.cell_value(i, 0), sheet.cell_value(i, 1)
        if isinstance(d, float) and isinstance(v, float):
            out[xlrd.xldate_as_datetime(d, book.datemode).date().isoformat()] = v
    return out


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "tetra-oil-price-update/1.0"})
    with urllib.request.urlopen(req, timeout=40) as r:
        raw = r.read()
    if url.endswith(".xls"):
        out = parse_eia(raw)
        if len(out) < 500:
            raise ValueError("feed too short")
        return out
    rows = list(csv.reader(io.StringIO(raw.decode())))
    out = {}
    for row in rows[1:]:
        try:
            dt.date.fromisoformat(row[0])
            out[row[0]] = float(row[1])
        except (ValueError, IndexError):
            continue  # FRED marks holidays with a blank or "."
    if len(out) < 500:
        raise ValueError("feed too short")
    return out


def refresh():
    for name, (col, *urls) in FEEDS.items():
        store, merged = read(name), False
        for url in urls:
            try:
                store.update(fetch(url))
                merged = True
                print(f"{name}: {url} ok, last {max(store)}")
            except Exception as e:
                print(f"{name}: {url} failed ({e})", file=sys.stderr)
        if not merged:
            print(f"{name}: no feed reachable, keeping stored data", file=sys.stderr)
        with open(DATA / name, "w", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["date", col])
            w.writerows((d, f"{store[d]:g}") for d in sorted(store))


def epoch(d):
    return int(dt.datetime.fromisoformat(d).replace(tzinfo=dt.timezone.utc).timestamp())


def build():
    cpi = {d[:7]: v for d, v in read("us_cpi_monthly.csv").items()}
    last_month = max(cpi)
    base = cpi[last_month]
    real = lambda d, p: round(p * base / cpi.get(d[:7], base), 2)

    def daily(name):
        s = read(name)
        days = sorted(s)
        return s, {"t": [epoch(d) for d in days], "p": [round(s[d], 2) for d in days],
                   "r": [real(d, s[d]) for d in days]}

    brent_raw, brent = daily("brent_daily.csv")
    wti_raw, wti = daily("wti_daily.csv")

    # Long-run monthly grid: EI annual to 1945, WTI monthly 1946-85, then monthly means of daily WTI.
    with open(DATA / "energy_institute_annual_1861_1945.csv", newline="") as f:
        annual = [(int(r["year"]), float(r["price_usd_bbl"]), float(r["price_2024usd_bbl"])) for r in csv.DictReader(f)]
    # Before CPI starts (1913) the price level comes from the EI real/nominal ratio, chained to CPI at 1913.
    ei_1913 = next(r / n for y, n, r in annual if y == 1913)
    cpi_1913 = sum(v for m, v in cpi.items() if m.startswith("1913")) / 12
    t, p, r = [], [], []
    def add(month, price, rp):
        t.append(epoch(month + "-01")); p.append(round(price, 2)); r.append(round(rp, 2))
    for y, n, rl in annual:
        for m in range(1, 13):
            mk = f"{y}-{m:02d}"
            if y < 1913:
                add(mk, n, n * (rl / n) / ei_1913 * base / cpi_1913)
            else:
                add(mk, n, real(mk, n))
    for d, v in sorted(read("wti_monthly_1946_1985.csv").items()):
        add(d[:7], v, real(d, v))
    months = {}
    for d, v in wti_raw.items():
        months.setdefault(d[:7], []).append(v)
    for mk in sorted(months):
        v = sum(months[mk]) / len(months[mk])
        add(mk, v, real(mk, v))

    latest = max(max(brent_raw), max(wti_raw))
    label = dt.date.fromisoformat(last_month + "-01").strftime("%b %Y")
    OUT.write_text(json.dumps({"lastPrice": latest, "cpiMonth": label, "brent": brent, "wti": wti,
                               "longrun": {"t": t, "p": p, "r": r}}, separators=(",", ":")))
    print(f"built: prices to {latest}; real terms in {label} US$; points {len(brent['t'])}/{len(wti['t'])}/{len(t)}")


if __name__ == "__main__":
    if "--offline" not in sys.argv:
        refresh()
    build()
