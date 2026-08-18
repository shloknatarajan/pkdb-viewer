#!/usr/bin/env python3
"""Estimate the scope of PMC papers annotatable for PK-DB.

Idea: PK-DB's own 779 curated papers are a labeled positive set. 152 of them live
in PMC. We build candidate PMC search queries from PK-DB's characteristic terms,
count how many PMC papers each returns (the candidate pool), and CALIBRATE each
query by its RECALL against those 152 known positives. A recall-corrected estimate
is (hits in universe) / (recall on the positives).

Two universes:
  * open access[filter]  -> PMC's CC-licensed, text-mineable Open Access Subset
  * (no filter)          -> all of PMC full text

Run: python3 estimate_pmc_scope.py   (needs only stdlib + network; ~1 min)
"""
import csv, json, time, urllib.parse, urllib.request

EMAIL = "shlok.natarajan@stanford.edu"
POS_CSV = "pkdb-api/pmid_to_pmcid.csv"   # sid,pmid,pmcid for every PK-DB study

def esearch(term):
    """PMC result count for `term`. POST so long PMCID-OR lists don't overflow the URL."""
    data = urllib.parse.urlencode(
        {"db": "pmc", "retmode": "json", "retmax": 0, "email": EMAIL, "term": term}
    ).encode()
    req = urllib.request.Request(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", data=data
    )
    for _ in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return int(json.load(r)["esearchresult"]["count"])
        except Exception:
            time.sleep(1.5)
    raise RuntimeError(f"esearch failed: {term[:60]}")

# --- labeled positives: PK-DB papers that are in PMC ---
pmcids = sorted({(r.get("pmcid") or "").strip()[3:]
                 for r in csv.DictReader(open(POS_CSV))
                 if (r.get("pmcid") or "").startswith("PMC")})
POS = " OR ".join(f"{i}[pmcid]" for i in pmcids)
in_pmc = esearch(f"({POS})"); time.sleep(.4)

# --- query building blocks ---
PK    = ('(pharmacokinetics[MeSH Terms] OR pharmacokinetics[MeSH Subheading] '
         'OR pharmacokinetic*[Title/Abstract] OR "concentration-time"[Title/Abstract])')
HUM   = 'humans[MeSH Terms]'
PARAM = ('("area under the curve"[Title/Abstract] OR AUC[Title/Abstract] OR Cmax[Title/Abstract] '
         'OR clearance[Title/Abstract] OR "half-life"[Title/Abstract] OR "volume of distribution"[Title/Abstract])')
DOSE  = ('("single dose"[Title/Abstract] OR "oral administration"[Title/Abstract] '
         'OR "healthy volunteers"[Title/Abstract] OR "healthy subjects"[Title/Abstract] OR "steady state"[Title/Abstract])')

FUNNEL = [
    ("1 any PK mention",         PK),
    ("2 + humans",               f"{PK} AND {HUM}"),
    ("3 + reported PK params",   f"{PK} AND {HUM} AND {PARAM}"),
    ("4 + dosing / clinical",    f"{PK} AND {HUM} AND {PARAM} AND {DOSE}"),
]

pmc_total = esearch("all[sb]"); time.sleep(.4)
oa_total  = esearch("open access[filter]"); time.sleep(.4)
oa_pos    = esearch(f"open access[filter] AND ({POS})"); time.sleep(.4)

print(f"PK-DB curated papers: {sum(1 for _ in csv.DictReader(open(POS_CSV)))}")
print(f"  in PMC full text : {in_pmc}  ({in_pmc/779:.0%} of PK-DB)")
print(f"  in OA-subset     : {oa_pos}  ({oa_pos/779:.0%} of PK-DB)")
print(f"PMC full text total: {pmc_total:,}   OA-subset: {oa_total:,}\n")
print(f"{'query tier':26s} {'recall':>7s} | {'ALL-PMC hits':>12s} {'est':>9s} | {'OA hits':>8s} {'est':>8s}")
print("-" * 86)
out = {"pmc_total": pmc_total, "oa_total": oa_total, "in_pmc": in_pmc, "oa_pos": oa_pos, "tiers": {}}
for name, q in FUNNEL:
    recall = esearch(f"({q}) AND ({POS})") / in_pmc; time.sleep(.4)
    h_all  = esearch(f"({q})"); time.sleep(.4)
    h_oa   = esearch(f"open access[filter] AND ({q})"); time.sleep(.4)
    e_all  = round(h_all / recall) if recall else 0
    e_oa   = round(h_oa / recall) if recall else 0
    out["tiers"][name] = dict(recall=recall, all_hits=h_all, all_est=e_all, oa_hits=h_oa, oa_est=e_oa)
    print(f"{name:26s} {recall:>7.0%} | {h_all:>12,} {e_all:>9,} | {h_oa:>8,} {e_oa:>8,}")

json.dump(out, open("pmc_scope_estimate.json", "w"), indent=2)
print("\nsaved -> pmc_scope_estimate.json")
