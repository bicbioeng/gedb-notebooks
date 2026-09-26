"""Generate one Colab notebook per GeDB crystal-growth dataset.

Each notebook is template/crystal_growth.ipynb with its data cell swapped for one that pulls that
dataset's rows from the public GeDB API — no data is stored here and no token is needed.
Output: <env>/<dataset id>.ipynb, opened from GeDB as
https://colab.research.google.com/github/bicbioeng/gedb-notebooks/blob/main/<env>/<id>.ipynb
Run: python generate.py            (stdlib only; CI runs it on a schedule)
"""
import json, os, re, urllib.request

ENVS = {
    "dev": "https://graphql-gedb-dev.bicbioeng.org/graphql/gedb",
    "prod": "https://graphql.bicbioeng.org/graphql/gedb",
}
INDEX = "gedb_datasets_mei_lab_datasets"
QUERY = """query($t:String!,$e:String!,$g:String!,$p:Int,$s:Int){
  nfbResult(target:$t, entity:$e, tag:$g, pageNumber:$p, pageSize:$s){ name total bulk } }"""


def gql(api, variables):
    req = urllib.request.Request(api, json.dumps({"query": QUERY, "variables": variables}).encode(),
                                 {"Content-Type": "application/json", "User-Agent": "curl/8 gedb-notebooks"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)["data"]["nfbResult"]


def datasets(api):
    page, out = 1, []
    while True:
        rows = gql(api, {"t": "", "e": "datasets", "g": INDEX, "p": page, "s": 100})
        out += rows
        if not rows or len(out) >= rows[0]["total"]:
            return out
        page += 1


def data_cell(api, dataset_id, name):
    src = f'''# ─── Data: pulled live from GeDB ──────────────────────────────────────
# Dataset: {name}
# Opened from GeDB → Run AI/ML. Rows come from the GeDB API (same data you see on the site).
import json, os, shutil, urllib.request
import pandas as pd

GEDB_API = "{api}"
DATASET_ID = "{dataset_id}"

_q = {{"query": "query($t:String!,$e:String!,$g:String!){{ nfbResult(target:$t, entity:$e, tag:$g, pageNumber:1, pageSize:25){{ bulk }} }}",
      "variables": {{"t": '"' + DATASET_ID + '"', "e": "datasets", "g": "{INDEX}"}}}}
_req = urllib.request.Request(GEDB_API, json.dumps(_q).encode(), {{"Content-Type": "application/json", "User-Agent": "curl/8 colab"}})
_hits = [json.loads(h["bulk"]) for h in json.load(urllib.request.urlopen(_req, timeout=120))["data"]["nfbResult"]]
_rows = next(b["csv_file"] for b in _hits if b.get("id") == DATASET_ID and b.get("csv_file"))

shutil.rmtree("datasets", ignore_errors=True)   # only this dataset, even on re-run
os.makedirs("datasets")
_df = pd.DataFrame(_rows)
if "SheetName" in _df:   # merged file → one run per crystal, so per-run plots and CV work
    for sheet, part in _df.groupby("SheetName", sort=False):
        part.drop(columns="SheetName").to_csv(f"datasets/crystal_growth_{{sheet.replace(' ', '_')}}.csv", index=False)
else:
    _df.to_csv(f"datasets/crystal_growth_{{DATASET_ID.replace('crystal_growth_', '')}}.csv", index=False)
print(f"✅ {{len(_df)}} rows of '{{DATASET_ID}}' → datasets/")

CSV_URLS = []   # empty → the loader below reads datasets/crystal_growth_*.csv

POWER_OUTLIER_THRESHOLD = 30_000   # Watts — values above this are flagged
EXCLUDE_OUTLIERS_FROM_ML = True    # Set False to include outliers in ML training
'''
    return {"cell_type": "code", "id": "csv_urls", "metadata": {}, "execution_count": None, "outputs": [],
            "source": src.splitlines(keepends=True)}


def main():
    template = json.load(open("template/crystal_growth.ipynb"))
    for env, api in ENVS.items():
        os.makedirs(env, exist_ok=True)
        keep = set()
        for d in datasets(api):
            bulk = json.loads(d["bulk"]) if d.get("bulk") else {}
            dataset_id = bulk.get("id") or ""
            if not bulk.get("csv_file") or not re.fullmatch(r"[A-Za-z0-9._-]+", dataset_id):
                continue
            nb = json.loads(json.dumps(template))
            nb["cells"] = [data_cell(api, dataset_id, d["name"]) if c.get("id") == "csv_urls" else c for c in nb["cells"]]
            nb["cells"][0] = {**nb["cells"][0], "source": [f"# 🔬 {d['name']}\n\n"] + nb["cells"][0]["source"]}
            path = f"{env}/{dataset_id}.ipynb"
            with open(path, "w") as f:
                json.dump(nb, f, indent=1)
            keep.add(path)
        for fn in os.listdir(env):   # datasets that disappeared
            if f"{env}/{fn}" not in keep:
                os.remove(f"{env}/{fn}")
        print(f"{env}: {len(keep)} notebooks")


if __name__ == "__main__":
    main()
