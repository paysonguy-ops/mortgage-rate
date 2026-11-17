import csv, io, json, sys, urllib.request, datetime, os, time

URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US"
# FRED (Akamai) tarpits unknown User-Agents: paysonguy-mortgage-rate/1.0 timed out
# on the Nov 5 and Nov 12 scheduled runs, so rate.json stayed at Oct 29. A
# Mozilla-compatible UA is accepted and the same CSV returns immediately.
UA = "Mozilla/5.0 (compatible; paysonguy-mortgage-rate/1.1; +https://www.paysonguy.com)"

def fetch():
    last_err = None
    for attempt in range(1, 4):
        try:
            req = urllib.request.Request(URL, headers={"User-Agent": UA})
            txt = urllib.request.urlopen(req, timeout=60).read().decode()
            rows = [r for r in csv.reader(io.StringIO(txt))][1:]
            last = None
            for r in rows:
                if len(r) >= 2 and r[1].strip() not in ("", "."):
                    try:
                        v = float(r[1])
                        datetime.date.fromisoformat(r[0])
                        last = (r[0], v)
                    except ValueError:
                        pass
            if not last:
                raise ValueError("no data")
            return last
        except Exception as e:
            last_err = e
            print("attempt", attempt, "failed:", e)
            if attempt < 3:
                time.sleep(15 * attempt)
    raise last_err

try:
    last = fetch()
except Exception as e:
    print("fetch/parse failed, keeping old rate.json:", e)
    sys.exit(1)

old = {}
if os.path.exists("rate.json"):
    try:
        old = json.load(open("rate.json"))
    except Exception:
        old = {}
rate = round(last[1], 2)
if old.get("rate") == rate and old.get("asOf") == last[0]:
    print("unchanged")
    sys.exit(0)
out = {
    "rate": rate,
    "asOf": last[0],
    "source": "Freddie Mac PMMS via FRED (MORTGAGE30US)",
    "updated": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
}
json.dump(out, open("rate.json", "w"), indent=1)
print("updated", out)
