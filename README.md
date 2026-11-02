# Global Logistics and Supply Chain Management – marimo notebooks

Interactive [marimo](https://marimo.io) slide notebooks for the master course
**Global Logistics and Supply Chain Management (GLSCM)** at the Chair of Logistics
and Quantitative Methods, University of Würzburg.

The notebooks are exported to WebAssembly and hosted on GitHub Pages, so students
can run them in the browser without installing anything.

## Notebooks (Chapter III – Distribution Network Design)

| Notebook | In the browser |
| --- | --- |
| `apps/center_of_gravity.py` – Phoenix enters Spain: Center of Gravity | https://d3group.github.io/GLSCM-lecture/center_of_gravity/ |
| `apps/warehouse_location_part_1.py` – Warehouse Location Problem (model) | https://d3group.github.io/GLSCM-lecture/warehouse_location_part_1/ |
| `apps/warehouse_location_part_2.py` – Warehouse Location Problem (solution and analyses) | https://d3group.github.io/GLSCM-lecture/warehouse_location_part_2/ |

Jupyter versions are available under `https://d3group.github.io/GLSCM-lecture/downloads/<notebook>.ipynb`.

## Repository structure

```
apps/
  *.py              marimo notebooks
  d3.css            shared styling
  layouts/          slide layouts
  public/           data and images (cog/, wlp/)
.github/workflows/  export to WebAssembly and deploy to GitHub Pages
```

In the browser, the notebooks load their data from the raw GitHub URLs of this
repository (`GH_REPO = "GLSCM-lecture"` in the first cell), so this repository has to stay public.

## Running locally

```bash
uv run --with marimo==0.18.1 --with polars --with altair --with pandas --with numpy \
  --with requests --with folium --with pulp --with scipy --with pyarrow \
  marimo edit apps
```

## Deployment

Every push to `main` exports the notebooks with `marimo export html-wasm` and deploys
them to GitHub Pages (Settings → Pages → Source: GitHub Actions). To add a notebook,
add an export step to `.github/workflows/deploy.yml`.
