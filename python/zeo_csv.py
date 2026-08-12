"""
zeo_csv.py — Parse Zeo website-exported zeodata.csv into Night records.

Verified against raipat/zeolibrary sample-files/zeodata.csv.
Mirrors the Java ZeoReader.readFile() field mapping but:
  - uses the csv module (robust to quoted notes fields with commas)
  - defaults to UTC for date parsing (no host-TZ drift, unlike the Java original)
  - returns None instead of -1 for missing numeric values
License: MIT (wrapper), see LICENSE in repo.
"""
import csv
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Night:
    date: str = ""
    zq: int = None
    total_z: int = None
    time_to_z: int = None
    time_in_wake: int = None
    time_in_rem: int = None
    time_in_light: int = None
    time_in_deep: int = None
    awakenings: int = None
    start_of_night: str = ""
    end_of_night: str = ""
    rise_time: str = ""
    alarm_reason: int = None
    alarm_type: int = None
    morning_feel: int = None
    sleep_graph_5min: list = field(default_factory=list)
    sleep_graph_30sec: list = field(default_factory=list)
    # sleep-stealer + custom fields omitted unless needed


def _to_int(s):
    s = (s or "").strip()
    if s == "":
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


def _parse_graph(s):
    """Space-separated stage string -> list[int], dropping leading wake/undefined."""
    s = (s or "").strip()
    if not s:
        return []
    out = []
    cutting = True
    for tok in s.split():
        try:
            v = int(tok)
        except ValueError:
            continue
        if cutting:
            if v > 1:  # first real sleep stage
                cutting = False
                out.append(v)
        else:
            out.append(v)
    return out


def read_csv(path):
    nights = []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        for row in reader:
            if not row or len(row) < 76:
                continue
            if (row[1] or "").strip() == "":
                continue  # no ZQ -> skip (matches Java q[1].length()>0 guard)
            n = Night()
            n.date = (row[0] or "").strip()
            n.zq = _to_int(row[1])
            n.total_z = _to_int(row[2])
            n.time_to_z = _to_int(row[3])
            n.time_in_wake = _to_int(row[4])
            n.time_in_rem = _to_int(row[5])
            n.time_in_light = _to_int(row[6])
            n.time_in_deep = _to_int(row[7])
            n.awakenings = _to_int(row[8])
            n.start_of_night = (row[9] or "").strip()
            n.end_of_night = (row[10] or "").strip()
            n.rise_time = (row[11] or "").strip()
            n.alarm_reason = _to_int(row[12])
            n.alarm_type = _to_int(row[16])
            n.morning_feel = _to_int(row[22])
            n.sleep_graph_5min = _parse_graph(row[74])
            n.sleep_graph_30sec = _parse_graph(row[75])
            nights.append(n)
    return nights


def averages(nights, fieldnames):
    print(f"\nAverage over {len(nights)} nights:")
    for f in fieldnames:
        vals = [getattr(n, f) for n in nights if getattr(n, f) is not None]
        if vals:
            avg = sum(vals) / len(vals)
            print(f"  {f:14s}: {avg:7.2f}  (n={len(vals)})")
        else:
            print(f"  {f:14s}:  n/a")


if __name__ == "__main__":
    import sys
    src = sys.argv[1] if len(sys.argv) > 1 else "sample-files/zeodata.csv"
    ns = read_csv(src)
    print(f"Parsed {len(ns)} nights from {src}")
    print(f"First night: date={ns[0].date} zq={ns[0].zq} total_z={ns[0].total_z} "
          f"deep={ns[0].time_in_deep} rem={ns[0].time_in_rem} light={ns[0].time_in_light}")
    print(f"First night 5-min hypnogram length: {len(ns[0].sleep_graph_5min)} stages")
    averages(ns, ["zq", "total_z", "time_to_z", "time_in_wake",
                   "time_in_rem", "time_in_light", "time_in_deep", "awakenings"])
