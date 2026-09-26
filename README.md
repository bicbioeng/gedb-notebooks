# GeDB notebooks

One ready-to-run Colab notebook per crystal-growth dataset in [GeDB](https://gedb.bicbioeng.org).
GeDB's **Run AI/ML** opens `https://colab.research.google.com/github/bicbioeng/gedb-notebooks/blob/main/<env>/<dataset-id>.ipynb`.

- `template/crystal_growth.ipynb` — the Ge-STAR analysis template (EDA → outliers → growth phases → PCA/ML with per-run CV).
- `generate.py` — swaps the template's data cell for one that pulls that dataset's rows from the public GeDB API, for every dataset in `dev` (gedb-dev) and `prod` (gedb). Stdlib only.
- `.github/workflows/generate.yml` — regenerates every 30 min, on dispatch, or when the template changes; commits with this repo's `GITHUB_TOKEN`.

No data is stored here and no personal account or token is involved, so nothing breaks when someone leaves the lab.
To change the analysis, edit the template (a data engineer reviews it like any PR); every notebook picks it up on the next run.
