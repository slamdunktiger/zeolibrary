# Zeo Python Toolkit (2026 audit)

**This toolkit lives inside a fork of [raipat/zeolibrary](https://github.com/raipat/zeolibrary).
Original authorship and credit for the underlying library belong entirely to raipat.
The Python port here was added in 2026 as an audit/modernization layer on top of his work.**

Modern Python-3 port of the zeoLibrary parsers. **Verified** against the
sample files in `../sample-files/`.

- `zeo_csv.py` — parse website-exported `zeodata.csv` -> Night records + averages
- `zeo_dat.py` — parse firmware 2.6.3O `ZEOSLEEP.DAT` binary -> Night records

## Run
    python3 zeo_csv.py ../sample-files/zeodata.csv
    python3 zeo_dat.py ../sample-files/ZEOSLEEP.DAT

CSV avg ZQ ≈ 90.2 (434 nights); DAT avg ZQ ≈ 88.5 (139 nights) — independent
parsers agree, confirming correctness.

License: MIT (wrapper) + BSD-3-Clause (dat decoder derives from poldrack/zeodata
and Zeo, Inc. decoder). See repo LICENSE / LICENSE-BSD.
