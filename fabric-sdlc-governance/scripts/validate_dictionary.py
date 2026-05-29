"""Validate data-dictionary YAML files for shape + required fields."""
import sys, glob, yaml

REQUIRED = {"dataset","description","owner","tier","columns"}
COL_REQUIRED = {"name","type"}

def main(patterns):
    files = []
    for p in patterns: files += glob.glob(p)
    if not files:
        print(f"WARN no dictionary files matched {patterns}"); return 0
    bad = 0
    for f in files:
        try:
            d = yaml.safe_load(open(f, encoding="utf-8"))
        except Exception as e:
            print(f"FAIL {f} parse: {e}"); bad += 1; continue
        miss = REQUIRED - set(d or {})
        if miss: print(f"FAIL {f} missing top-level {miss}"); bad += 1; continue
        for c in d["columns"]:
            cm = COL_REQUIRED - set(c)
            if cm: print(f"FAIL {f} column {c.get('name')} missing {cm}"); bad += 1
        print(f"OK   {f}  ({len(d['columns'])} cols, sensitivity_default={d.get('sensitivity_default','-')})")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or ["contracts/dictionary/*.yml"]))
