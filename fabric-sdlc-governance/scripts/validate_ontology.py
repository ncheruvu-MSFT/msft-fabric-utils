"""Validate ontology YAML — terms have definitions, triples reference known terms."""
import sys, glob, yaml

def main(patterns):
    files=[]
    for p in patterns: files += glob.glob(p)
    if not files: print(f"WARN no ontology files matched {patterns}"); return 0
    bad=0
    for f in files:
        d = yaml.safe_load(open(f, encoding="utf-8"))
        terms = {t["name"]: t for t in d.get("terms", [])}
        for t in d.get("terms", []):
            if "definition" not in t: print(f"FAIL {f} term {t['name']} missing definition"); bad+=1
        for tr in d.get("triples", []):
            s,p,o = tr
            if s not in terms: print(f"FAIL {f} triple subject not in terms: {s}"); bad+=1
            if o not in terms: print(f"FAIL {f} triple object  not in terms: {o}"); bad+=1
        print(f"OK   {f}  ({len(terms)} terms, {len(d.get('triples',[]))} triples)")
    return 1 if bad else 0

if __name__=="__main__":
    sys.exit(main(sys.argv[1:] or ["contracts/ontology/*.yml"]))
