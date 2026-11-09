import marimo

__generated_with = "0.18.1"
app = marimo.App(
    width="medium",
    app_title="Warehouse Location Problem",
    layout_file="layouts/warehouse_location_part_2.slides.json",
    css_file="d3.css",
)


@app.cell(hide_code=True)
def _():
    from pathlib import Path

    GH_USER = "d3group"
    GH_REPO = "GLSCM-lecture"
    BRANCH = "main"

    def raw_url(*parts: str) -> str:
        path = "/".join(parts)
        return f"https://raw.githubusercontent.com/{GH_USER}/{GH_REPO}/{BRANCH}/{path}"

    # Check if running locally or in WASM export
    # In local mode: apps/public/data exists
    # In WASM export: public/data exists
    # Path.exists() doesn't work reliably in WASM, so we also check for micropip

    local_data_dir = Path("apps/public/data")
    wasm_data_dir = Path("public/data")

    # Detect WASM by checking if micropip is available
    try:
        import micropip as _micropip
        in_wasm = True
    except ImportError:
        in_wasm = False

    use_local = local_data_dir.exists() and not in_wasm
    use_wasm = (wasm_data_dir.exists() or in_wasm) and not use_local
    # use_local = True

    print(f"Detection: use_local={use_local}, use_wasm={use_wasm}, in_wasm={in_wasm}")

    class DataURLs:
        if use_local:
            # Local development mode
            BASE = "apps/public/wlp/data"
            IMG_BASE = "apps/public/wlp/images"
        else:
            # WASM/deployed mode - use GitHub raw URLs for data files
            BASE = raw_url("apps", "public", "wlp", "data")
            IMG_BASE = "public/wlp/images"  # Images work with relative paths

    print(f"Using BASE: {DataURLs.BASE}")
    return (DataURLs,)


@app.cell(hide_code=True)
async def _():
    # Only install packages in WebAssembly environment
    try:
        import micropip

        # Install required packages
        packages = [
            "polars",
            "altair",
            "requests",
            "folium",
            "pulp",
            "pyarrow"
        ]

        for pkg in packages:
            print(f"Installing {pkg}...")
            await micropip.install(pkg)

        print("✅ All packages installed.")
    except ImportError:
        # Running locally, packages should already be installed
        print("Running in local mode, skipping micropip installation")
    return


@app.cell(hide_code=True)
def _():
    # Import required libraries
    import marimo as mo
    import altair as alt
    import polars as pl
    import numpy as np
    import pulp
    import folium
    import warnings
    warnings.filterwarnings("ignore", message=".*narwhals.*is_pandas_dataframe.*")
    return alt, folium, mo, np, pl, pulp


@app.cell(hide_code=True)
def _(np, pulp):
    # PuLP to SciPy solver for WASM compatibility
    # PuLP's CBC solver uses subprocess which doesn't work in WASM,
    # so we convert the PuLP model to scipy format and solve with HiGHS
    from scipy.sparse import coo_matrix
    from scipy.optimize import linprog

    def pulp_to_scipy_linprog(prob):
        """
        Convert a PuLP LP (prob) into the data structures expected by scipy.optimize.linprog.
        """
        variables = [v for v in prob.variables() if v.name != "__dummy"]
        n_vars = len(variables)
        var_index = {v: i for i, v in enumerate(variables)}

        c = np.zeros(n_vars, dtype=float)
        for v, coef in prob.objective.items():
            if v.name == "__dummy":
                continue
            c[var_index[v]] = float(coef)

        constant_offset = float(prob.objective.constant or 0.0)
        if prob.sense == pulp.LpMaximize:
            c = -c
            constant_offset = -constant_offset

        ub_rows, ub_cols, ub_data, b_ub = [], [], [], []
        eq_rows, eq_cols, eq_data, b_eq = [], [], [], []
        ub_count, eq_count = 0, 0

        for constr in prob.constraints.values():
            sense = constr.sense
            const_term = float(constr.constant or 0.0)

            if sense == pulp.LpConstraintLE:
                for v, coef in constr.items():
                    if v.name == "__dummy":
                        continue
                    ub_rows.append(ub_count)
                    ub_cols.append(var_index[v])
                    ub_data.append(float(coef))
                b_ub.append(-const_term)
                ub_count += 1
            elif sense == pulp.LpConstraintGE:
                for v, coef in constr.items():
                    if v.name == "__dummy":
                        continue
                    ub_rows.append(ub_count)
                    ub_cols.append(var_index[v])
                    ub_data.append(-float(coef))
                b_ub.append(const_term)
                ub_count += 1
            elif sense == pulp.LpConstraintEQ:
                for v, coef in constr.items():
                    if v.name == "__dummy":
                        continue
                    eq_rows.append(eq_count)
                    eq_cols.append(var_index[v])
                    eq_data.append(float(coef))
                b_eq.append(-const_term)
                eq_count += 1

        A_ub = coo_matrix((ub_data, (ub_rows, ub_cols)), shape=(ub_count, n_vars)).tocsr() if ub_count > 0 else None
        b_ub = np.array(b_ub, dtype=float) if ub_count > 0 else None
        A_eq = coo_matrix((eq_data, (eq_rows, eq_cols)), shape=(eq_count, n_vars)).tocsr() if eq_count > 0 else None
        b_eq = np.array(b_eq, dtype=float) if eq_count > 0 else None

        bounds = []
        integrality = np.zeros(n_vars, dtype=int)
        for i, v in enumerate(variables):
            lb = float(v.lowBound) if v.lowBound is not None else -np.inf
            ub = float(v.upBound) if v.upBound is not None else np.inf
            bounds.append((lb, ub))
            if v.cat in (pulp.LpInteger, pulp.LpBinary):
                integrality[i] = 1

        return {
            'c': c, 'A_ub': A_ub, 'b_ub': b_ub, 'A_eq': A_eq, 'b_eq': b_eq,
            'bounds': bounds, 'integrality': integrality,
            'constant_offset': constant_offset, 'variables_list': variables,
        }

    def solve_with_scipy(prob):
        """
        Solve a PuLP problem using SciPy's linprog with HiGHS solver.
        Works in WASM where PuLP's CBC solver fails due to subprocess restrictions.
        """
        data = pulp_to_scipy_linprog(prob)
        result = linprog(
            c=data['c'], A_ub=data['A_ub'], b_ub=data['b_ub'],
            A_eq=data['A_eq'], b_eq=data['b_eq'],
            bounds=data['bounds'], integrality=data['integrality'],
            method='highs',
        )

        if result.success:
            for var_obj, xval in zip(data['variables_list'], result.x):
                var_obj.varValue = xval
            obj = result.fun + data['constant_offset']
            if prob.sense == pulp.LpMaximize:
                obj = -obj
            prob.objective_value = obj
            prob.status = pulp.LpStatusOptimal
        else:
            prob.status = pulp.LpStatusNotSolved
        return prob
    return (solve_with_scipy,)


@app.cell(hide_code=True)
def _(mo):
    # For WASM compatibility, we inline the slides classes here
    # (marimo doesn't bundle utils/ in WASM exports)
    from __future__ import annotations
    from dataclasses import dataclass
    from typing import Optional as _Optional
    import html as _html

    # Slide constants
    SLIDE_WIDTH = 1280
    SLIDE_HEIGHT = 720
    GAP = 24
    PADDING_X = 24
    PADDING_Y = 16
    TITLE_FONT_SIZE = 28
    FOOTER_FONT_SIZE = 12

    @dataclass
    class Slide:
        title: str
        chair: str
        course: str
        presenter: str
        logo_url: _Optional[str]
        page_number: int
        layout_type: str = "side-by-side"
        subtitle: _Optional[str] = None
        content1: _Optional[mo.core.MIME] = None
        content2: _Optional[mo.core.MIME] = None

        def _header(self) -> mo.core.MIME:
            safe_title = _html.escape(self.title)
            return mo.Html(
                f"""
                <div class="slide-header">
                  <div class="slide-title" style="font-size: {TITLE_FONT_SIZE}px; font-weight: 700; line-height: 1.2; margin: 0;">{safe_title}</div>
                  <div class="slide-hr" style="height: 1px; background: #E5E7EB; margin: 8px 0;"></div>
                </div>
                """
            )

        def _footer(self) -> mo.core.MIME:
            safe_page = _html.escape(str(self.page_number))
            safe_chair = _html.escape(self.chair)
            left_html = f"Page {safe_page} &nbsp;&nbsp;|&nbsp;&nbsp; {safe_chair}"
            center_img = (
                f'<img class="slide-logo" src="{_html.escape(self.logo_url)}" alt="logo" style="display: block; max-height: 28px; max-width: 160px; margin: 0 auto; object-fit: contain;">'
                if self.logo_url else "&nbsp;"
            )
            return mo.Html(
                f"""
                <div class="slide-footer">
                  <div class="slide-hr" style="height: 1px; background: #E5E7EB; margin: 8px 0;"></div>
                  <div class="slide-footer-row" style="display: grid; grid-template-columns: 1fr auto 1fr; align-items: center;">
                    <div class="slide-footer-left" style="font-size: {FOOTER_FONT_SIZE}px; color: #6B7280; white-space: nowrap;">{left_html}</div>
                    <div class="slide-footer-center">{center_img}</div>
                    <div class="slide-footer-right">&nbsp;</div>
                  </div>
                </div>
                """
            )

        def _title_layout(self) -> mo.core.MIME:
            safe_title = _html.escape(self.title)
            sub = f'<div class="title-slide-sub" style="font-size: 40px; margin: 0 0 16px 0; color: #374151;">{_html.escape(self.subtitle)}</div>' if self.subtitle else ""
            body = mo.Html(
                f"""
                <div class="slide-body title-center" style="flex: 1 1 auto; min-height: 0; display: flex; align-items: center; justify-content: center; height: 100%;">
                  <div class="title-stack" style="text-align: center;">
                    <div class="title-slide-title" style="font-size: 50px; font-weight: 800; margin: 0 0 8px 0;">{safe_title}</div>
                    {sub}
                    <div class="title-slide-meta" style="font-size: 30px; color: #6B7280;">{_html.escape(self.course)}</div>
                    <div class="title-slide-meta" style="font-size: 22px; color: #6B7280;">{_html.escape(self.presenter)}</div>
                  </div>
                </div>
                """
            )
            return mo.Html(
                f"""
                <div class="slide" style="width: {SLIDE_WIDTH}px; height: {SLIDE_HEIGHT}px; min-width: {SLIDE_WIDTH}px; min-height: {SLIDE_HEIGHT}px; max-width: {SLIDE_WIDTH}px; max-height: {SLIDE_HEIGHT}px; box-sizing: border-box; background: #ffffff; padding: {PADDING_Y}px {PADDING_X}px; display: flex; flex-direction: column; border-radius: 6px; box-shadow: 0 0 0 1px #f3f4f6; overflow: hidden; page-break-after: always; break-after: page;">
                  {self._header()}
                  {body}
                  {self._footer()}
                </div>
                """
            )

        def _one_column_layout(self) -> mo.core.MIME:
            content = mo.md(self.content1) if isinstance(self.content1, str) else (self.content1 or mo.md(""))
            content_wrapped = mo.vstack([content], gap=0).style({"gap": "0", "margin": "0", "padding": "0"})
            body = mo.Html(
                f"""
                <div class="slide-body" style="flex: 1 1 auto; min-height: 0; display: flex; flex-direction: column;">
                    <div class="slide-col tight-md" style="min-height: 0; overflow: auto; padding-right: 2px;">
                        <style>
                            ul {{ margin-top: -0.2em !important; }}
                            .slide-col.tight-md .paragraph {{ margin-block: 0 !important; margin: 0 0 4px 0 !important; font-size: 19px !important; }}
                            .slide-col.tight-md span.paragraph {{ margin-block: 0 !important; margin: 0 0 4px 0 !important; font-size: 19px !important; }}
                            li {{ font-size: 19px !important; }}
                            li * {{ font-size: 19px !important; }}
                        </style>
                        {content_wrapped}
                    </div>
                </div>
                """
            )
            return mo.Html(
                f"""
                <div class="slide" style="width: {SLIDE_WIDTH}px; height: {SLIDE_HEIGHT}px; min-width: {SLIDE_WIDTH}px; min-height: {SLIDE_HEIGHT}px; max-width: {SLIDE_WIDTH}px; max-height: {SLIDE_HEIGHT}px; box-sizing: border-box; background: #ffffff; padding: {PADDING_Y}px {PADDING_X}px; display: flex; flex-direction: column; border-radius: 6px; box-shadow: 0 0 0 1px #f3f4f6; overflow: hidden; page-break-after: always; break-after: page;">
                  {self._header()}
                  {body}
                  {self._footer()}
                </div>
                """
            )

        def _side_by_side_layout(self) -> mo.core.MIME:
            left_content = mo.md(self.content1) if isinstance(self.content1, str) else (self.content1 or mo.md(""))
            right_content = mo.md(self.content2) if isinstance(self.content2, str) else (self.content2 or mo.md(""))

            # CSS styles as separate element (not embedding marimo elements)
            styles = mo.Html(
                f"""
                <style>
                    ul {{ margin-top: -0.2em !important; }}
                    .paragraph {{ margin-block: 0 !important; margin: 0 0 4px 0 !important; font-size: 19px !important; }}
                    span.paragraph {{ margin-block: 0 !important; margin: 0 0 4px 0 !important; font-size: 19px !important; }}
                    li {{ font-size: 19px !important; }}
                    li * {{ font-size: 19px !important; }}
                </style>
                """
            )

            # Style each column with percentage widths (45% each, ~10% gap)
            left_styled = left_content.style({"width": "47%", "min-width": "0"})
            right_styled = right_content.style({"width": "47%", "min-width": "0"})

            # Use marimo's native hstack for two columns (avoids HTML string embedding)
            cols = mo.hstack(
                [left_styled, right_styled],
                gap=0,
                align="start",
                justify="space-between",
            ).style({"flex": "1 1 auto", "min-height": "0", "overflow": "auto", "width": "100%"})

            # Build body using vstack
            body = mo.vstack([styles, cols], gap=0)

            # Build slide using vstack
            slide = mo.vstack(
                [self._header(), body, self._footer()],
                gap=0,
            ).style({
                "width": f"{SLIDE_WIDTH}px",
                "height": f"{SLIDE_HEIGHT}px",
                "min-width": f"{SLIDE_WIDTH}px",
                "min-height": f"{SLIDE_HEIGHT}px",
                "max-width": f"{SLIDE_WIDTH}px",
                "max-height": f"{SLIDE_HEIGHT}px",
                "box-sizing": "border-box",
                "background": "#ffffff",
                "padding": f"{PADDING_Y}px {PADDING_X}px",
                "display": "flex",
                "flex-direction": "column",
                "border-radius": "6px",
                "box-shadow": "0 0 0 1px #f3f4f6",
                "overflow": "hidden",
                "page-break-after": "always",
                "break-after": "page",
            })

            return slide

        def render(self) -> mo.core.MIME:
            if self.layout_type == "title":
                return self._title_layout()
            elif self.layout_type == "1-column":
                return self._one_column_layout()
            return self._side_by_side_layout()

    class SlideCreator:
        def __init__(self, chair: str, course: str, presenter: str, logo_url: _Optional[str] = None):
            self.chair = chair
            self.course = course
            self.presenter = presenter
            self.logo_url = logo_url
            self._page_counter = 0

        def styles(self) -> mo.core.MIME:
            return mo.Html(
                f"""
                <style>
                  :root {{
                    --slide-w: {SLIDE_WIDTH}px;
                    --slide-h: {SLIDE_HEIGHT}px;
                    --gap: {GAP}px;
                    --pad-x: {PADDING_X}px;
                    --pad-y: {PADDING_Y}px;
                    --title-size: {TITLE_FONT_SIZE}px;
                    --footer-size: {FOOTER_FONT_SIZE}px;
                    --border-color: #E5E7EB;
                    --text-muted: #6B7280;
                    --bg: #ffffff;
                  }}
                  div.slide, .slide {{
                    width: var(--slide-w) !important;
                    height: var(--slide-h) !important;
                    min-width: var(--slide-w) !important;
                    min-height: var(--slide-h) !important;
                    max-width: var(--slide-w) !important;
                    max-height: var(--slide-h) !important;
                    box-sizing: border-box !important;
                    background: var(--bg) !important;
                    padding: var(--pad-y) var(--pad-x) !important;
                    display: flex !important;
                    flex-direction: column !important;
                    border-radius: 6px;
                    box-shadow: 0 0 0 1px #f3f4f6;
                    overflow: hidden !important;
                  }}
                  div.slide-title, .slide-title {{
                    font-size: var(--title-size) !important;
                    font-weight: 700 !important;
                    line-height: 1.2 !important;
                    margin: 0 !important;
                  }}
                  div.slide-hr, .slide-hr {{
                    height: 1px !important;
                    background: var(--border-color) !important;
                    margin: 8px 0 !important;
                  }}
                  div.slide-body, .slide-body {{
                    flex: 1 1 auto !important;
                    min-height: 0 !important;
                    display: flex !important;
                    flex-direction: column !important;
                  }}
                  div.slide-cols, .slide-cols {{
                    display: grid !important;
                    grid-template-columns: 1fr 1fr !important;
                    gap: var(--gap) !important;
                    height: 100% !important;
                    min-height: 0 !important;
                  }}
                  div.slide-col, .slide-col {{
                    min-height: 0 !important;
                    overflow: auto !important;
                    padding-right: 2px !important;
                  }}
                  div.slide-footer div.slide-footer-row, .slide-footer .slide-footer-row {{
                    display: grid !important;
                    grid-template-columns: 1fr auto 1fr !important;
                    align-items: center !important;
                  }}
                  div.slide-footer-left, .slide-footer-left {{
                    font-size: var(--footer-size) !important;
                    color: var(--text-muted) !important;
                    white-space: nowrap !important;
                  }}
                  img.slide-logo, .slide-logo {{
                    display: block !important;
                    max-height: 28px !important;
                    max-width: 160px !important;
                    margin: 0 auto !important;
                    object-fit: contain !important;
                  }}
                  div.title-center, .title-center {{
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    height: 100% !important;
                  }}
                  div.title-stack, .title-stack {{
                    text-align: center !important;
                  }}
                  div.title-slide-title, .title-slide-title {{
                    font-size: 40px !important;
                    font-weight: 800 !important;
                    margin: 0 0 8px 0 !important;
                  }}
                  div.title-slide-sub, .title-slide-sub {{
                    font-size: 20px !important;
                    margin: 0 0 16px 0 !important;
                    color: #374151 !important;
                  }}
                  div.title-slide-meta, .title-slide-meta {{
                    font-size: 16px !important;
                    color: var(--text-muted) !important;
                  }}
                  .tight-md p {{ margin: 0 0 4px 0 !important; }}
                  .tight-md .paragraph {{ margin-block: 0 !important; margin: 0 0 4px 0 !important; display: block !important; font-size: 19px !important; }}
                  .tight-md span.paragraph {{ margin-block: 0 !important; margin: 0 0 4px 0 !important; display: block !important; font-size: 19px !important; }}
                  ul {{ margin-top: -0.2em !important; margin-bottom: 6px !important; margin-left: 1.25em !important; margin-right: 0 !important; }}
                  .tight-md li {{ margin: 2px 0 !important; font-size: 19px !important; }}
                  li {{ font-size: 19px !important; }}
                  li * {{ font-size: 19px !important; }}
                  .tight-md h1, .tight-md h2, .tight-md h3, .tight-md h4 {{ margin: 0 0 6px 0 !important; }}
                </style>
                """
            )

        def create_slide(self, title: str, layout_type: str = "side-by-side", page_number: _Optional[int] = None) -> Slide:
            if page_number is None:
                self._page_counter += 1
                page_number = self._page_counter
            return Slide(
                title=title,
                chair=self.chair,
                course=self.course,
                presenter=self.presenter,
                logo_url=self.logo_url,
                page_number=page_number,
                layout_type=layout_type,
            )

        def create_title_slide(self, title: str, subtitle: _Optional[str] = None, page_number: _Optional[int] = None) -> Slide:
            slide = self.create_slide(title, layout_type="title", page_number=page_number)
            slide.subtitle = subtitle
            return slide
    return (SlideCreator,)


@app.cell(hide_code=True)
def _():
    lehrstuhl = "Chair of Logistics and Quantitative Methods"
    vorlesung = "Global Logistics and Supply Chain Management"
    presenter = "Nikolai Stein, Richard Pibernik"
    return lehrstuhl, presenter, vorlesung


@app.cell(hide_code=True)
def _(SlideCreator, lehrstuhl, presenter, vorlesung):
    sc = SlideCreator(lehrstuhl, vorlesung, presenter)
    return (sc,)


@app.cell(hide_code=True)
def _(sc):
    titleSlide = sc.create_title_slide(
        "Phoenix enters Spain",
        subtitle="Analysis and Results"
    )
    sc.styles()
    titleSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    completeModelSlide = sc.create_slide(
        'Recap - Warehouse Location Problem',
        layout_type='side-by-side',
        page_number=2
    )

    completeModelSlide.content1 = mo.md(
        r"""
    **Sets**
    - $I$: regions in Spain  
    - $J$: possible warehouse locations (here $J = I$)

    **Parameters**
    - \(d_i\): annual demand in region \(i \in I\)  
      (number of pharmacy visits per year)  
    - \(f_j\): annual fixed cost of a warehouse in location \(j \in J\)  
    - \(c_{ij}\): annual transport cost if region \(i\) is served from \(j \in J\)

    **Decision variables**
    - \(y_j \in \{0,1\}\): 1 if a warehouse is opened in \(j\), 0 otherwise  
    - \(x_{ij} \in \{0,1\}\): 1 if region \(i\) is served from warehouse \(j\), 0 otherwise  
    """
    )

    completeModelSlide.content2 = mo.md(
    r"""
    **Objective**

    $\min \quad \sum_{j \in J} f_j \, y_j \;+\;\sum_{i \in I} \sum_{j \in J} c_{ij} \, x_{ij}$

    **Constraints**

    - Each region is assigned to exactly one warehouse:

        $\sum_{j \in J} x_{ij} = 1 \quad \forall i \in I$

    - Regions can only be assigned to open warehouses:

        $x_{ij} \le y_j \quad \forall i \in I,\; j \in J$

    - Binary decisions:

        $x_{ij} \in \{0,1\}, \quad y_j \in \{0,1\}$
    """
    )

    completeModelSlide.render()
    return


@app.cell(hide_code=True)
def _(DataURLs, pl):
    # Base case from Part 1: 7,000 m², 6 €/m², 75 % markup, 400 € per tour
    pharmacies_aggregated = pl.read_csv(
        f'{DataURLs.BASE}/pharmacies_aggregated.csv',
        schema_overrides={"region_id": pl.Utf8}
    )

    fixed_costs = pl.read_csv(
        f'{DataURLs.BASE}/fixed_costs.csv',
        schema_overrides={"region_id": pl.Utf8}
    )

    transportation_costs = pl.read_csv(
        f'{DataURLs.BASE}/transportation_costs.csv',
        schema_overrides={"i": pl.Utf8, "j": pl.Utf8}
    )

    I = pharmacies_aggregated["region_id"].unique().to_list()
    J = I
    f = {
        row["region_id"]: row["fixed_cost"] 
        for row in fixed_costs.iter_rows(named=True)
    }
    c = {
        (row["i"], row["j"]): row["c_ij"]
        for row in transportation_costs.iter_rows(named=True)
    }
    return I, J, c, f, fixed_costs, pharmacies_aggregated


@app.cell(hide_code=True)
def _(mo, sc):
    dataToPythonSlide = sc.create_slide(
        'From Phoenix data to model inputs in Python',
        layout_type='side-by-side',
        page_number=3
    )

    dataToPythonSlide.content1 = mo.md(
    r"""
    On the previous recap slide we saw the warehouse location model for Phoenix:

    - sets of regions \(I\) and candidate warehouse locations \(J\),
    - fixed warehouse costs \(f_j\),
    - transport costs \(c_{ij}\).

    In the notebook, we have already used the demand data and the fulfillment assumptions to compute the fixed costs \(f_j\) and the transport costs \(c_{ij}\).

    For the optimization model, we now only need to translate

    - the set \(J\),
    - the fixed costs \(f_j\),
    - and the transport costs \(c_{ij}\)

    into Python objects.
    """
    )

    dataToPythonSlide.content2 = mo.md(
    """
    ```python
    #Sets of regions and possible warehouse locations
    I = pharmacies_aggregated["region_id"].unique().to_list()

    #Every region is a possible warehouse location
    J = I

    #Fixed cost for each candidate warehouse
    f = {
        row["region_id"]: row["fixed_cost"] 
        for row in fixed_costs.iter_rows(named=True)
    }

    #Transport cost for each pair (i, j)
    c = {
        (row["i"], row["j"]): row["c_ij"]
        for row in transportation_costs.iter_rows(named=True)
    }
    ```
    """
    )

    dataToPythonSlide.render()
    return


@app.cell(hide_code=True)
def _(J, c, pulp):
    # Create the optimization problem
    problem = pulp.LpProblem("Phoenix_Warehouse_Location", pulp.LpMinimize)

    # Binary variable y_j: 1 if warehouse j is open
    y = pulp.LpVariable.dicts(
        "y",
        J,
        lowBound=0,
        upBound=1,
        cat="Binary",
    )

    # Binary variable x_ij: 1 if region i is served from warehouse j
    x = pulp.LpVariable.dicts(
        "x",
        c,
        lowBound=0,
        upBound=1,
        cat="Binary",
    )
    return problem, x, y


@app.cell(hide_code=True)
def _(mo, sc):
    decisionVarsSlide = sc.create_slide(
        'Decision variables and optimization problem in PuLP',
        layout_type='side-by-side',
        page_number=4
    )

    decisionVarsSlide.content1 = mo.md(
        r"""
    Now we translate the decision variables and the goal of our model
    into PuLP.

    Decision variables in the math model:

    - \(y_j\): 1 if we open a warehouse in location \(j\), 0 otherwise  
    - \(x_{ij}\): 1 if region \(i\) is served from warehouse \(j\), 0 otherwise  

    We create the same variables in PuLP as binary variables
    and define an optimization problem that we will later fill
    with the objective and constraints.
    """
    )

    decisionVarsSlide.content2 = mo.md(
    r"""
    ```python
    # Create the optimization problem
    problem = pulp.LpProblem(
        "Phoenix_Warehouse_Location", pulp.LpMinimize
    )

    # Binary variable y_j: 1 if warehouse j is open
    y = pulp.LpVariable.dicts(
        "y",
        J,
        lowBound=0,
        upBound=1,
        cat="Binary"
    )

    # Binary variable x_ij: 1 if region i is served from warehouse j
    x = pulp.LpVariable.dicts(
        "x",
        c,
        lowBound=0,
        upBound=1,
        cat="Binary"
    )
    ```
    """
    )

    decisionVarsSlide.render()
    return


@app.cell(hide_code=True)
def _(J, c, f, problem, pulp, x, y):
    fixed_cost_term = pulp.lpSum(
        f[j] * y[j] 
        for j in J
    )
    transport_cost_term = pulp.lpSum(
        c[(i, j)] * x[(i,j)] 
        for i,j in c
    )
    problem.setObjective(
        fixed_cost_term + transport_cost_term
    )
    return fixed_cost_term, transport_cost_term


@app.cell(hide_code=True)
def _(mo, sc):
    objectiveSlide = sc.create_slide(
        'Objective: total annual cost in PuLP',
        layout_type='side-by-side',
        page_number=5
    )

    objectiveSlide.content1 = mo.md(
        r"""
    Our mathematical objective was:

    \[
    \min \sum_{j \in J} f_j \, y_j
    \;+\;
    \sum_{i \in I} \sum_{j \in J} c_{ij} \, x_{ij}
    \]

    Interpretation:

    - the first term adds up the fixed costs \(f_j\) for all open warehouses \(y_j = 1\),
    - the second term adds up the transport costs \(c_{ij}\) for all assignments \(x_{ij} = 1\).

    We now write exactly the same expression in PuLP.
    """
    )

    objectiveSlide.content2 = mo.md(
    r"""

    ```python
    #Fixed cost term
    fixed_cost_term = pulp.lpSum(
        f[j] * y[j] 
        for j in J
    )

    #Transport cost term
    transport_cost_term = pulp.lpSum(
        c[(i, j)] * x[(i,j)] 
        for i,j in c
    )

    #Set the objective
    problem.setObjective(
        fixed_cost_term + transport_cost_term
    )
    ```
    """
    )

    objectiveSlide.render()
    return


@app.cell(hide_code=True)
def _(I, J, c, problem, pulp, x, y):
    for i in I:
        problem.addConstraint(
        pulp.lpSum(x[(i,j)] for j in J if (i,j) in c) == 1
    )

    for i,j in c:
        problem.addConstraint(x[(i,j)] <= y[j])
    return


@app.cell(hide_code=True)
def _(mo, sc):
    constraintsSlide = sc.create_slide(
        'Constraints in PuLP',
        layout_type='side-by-side',
        page_number=6
    )

    constraintsSlide.content1 = mo.md(
        r"""
    Our model has two core constraints.

    - Each region is assigned to exactly one warehouse

        $\sum_{j \in J} x_{ij} = 1 \quad \forall i \in I$.

    - Regions can only be assigned to open warehouses

        $x_{ij} \le y_j \quad \forall i \in I, \forall j \in J$.

    We now write exactly the same expression in PuLP.
    """
    )

    constraintsSlide.content2 = mo.md(
    r"""
    Each region is assigned to exactly one warehouse:
    ```python
    for i in I:
        problem.addConstraint(
        pulp.lpSum(x[(i,j)] for j in J if (i,j) in c) == 1
    )
    ```

    Regions can only be assigned to open warehouses:
    ```python
    for i,j in c:
        problem.addConstraint(x[(i,j)] <= y[j])
    ```
    """
    )
    constraintsSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    solveSlide = sc.create_slide(
        'Solving the model and reading the solution',
        layout_type='side-by-side',
        page_number=7
    )

    solveSlide.content1 = mo.md(
        r"""
    Once the objective and constraints are in place,
    we can ask the solver to find an optimal solution.

    The solver will:

    - decide which warehouses to open (values of \(y_j\)),
    - decide how each region is assigned (values of \(x_{ij}\)),
    - report the minimum total annual cost.

    After solving, we are mainly interested in:

    - the solver status (did it find an optimal solution?),
    - the total annual cost,
    - the list of open warehouses,
    - and the assignment of regions to warehouses.
    """
    )

    solveSlide.content2 = mo.md(
        r"""
    ```python
    # Solve the problem with the default solver
    status = problem.solve()

    print("Solver status:", pulp.LpStatus[status])
    print("Total annual cost:", pulp.value(problem.objective))

    # Which warehouses are open?
    open_warehouses = [j for j in J if y[j].value() > 0.5]
    print("Open warehouses:", open_warehouses)
    ```
    """
    )
    solveSlide.render()
    return


@app.cell(hide_code=True)
def _(J, problem, solve_with_scipy, y):
    # Solve using scipy's HiGHS (works in WASM, unlike PuLP's CBC which uses subprocess)
    solve_with_scipy(problem)
    open_warehouses = [j for j in J if y[j].value() > 0.5]
    return (open_warehouses,)


@app.cell(hide_code=True)
def _(c, folium, np, pharmacies_aggregated, pl, x):
    def plot_assignments_map(
        df: pl.DataFrame,
        zoom_start: int = 5,
    ):
        """
        Plot demand points on a folium map, colored by assigned warehouse,
        and add a marker for each open warehouse.

        Args:
            df: DataFrame with columns:
                - 'region_id'
                - 'lat', 'lon'
                - 'demand'
                - 'assigned_warehouse'
                - 'warehouse_lat', 'warehouse_lon'
            zoom_start: Initial zoom level for the map
        """
        # Center of the map (median of demand point coordinates)
        center_lat = df["lat"].median()
        center_lon = df["lon"].median()

        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom_start,
            tiles="OpenStreetMap",
        )

        # Color palette
        map_colors = [
            '#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231',
            '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe',
            '#008080', '#e6beff', '#9a6324', '#fffac8', '#800000',
            '#aaffc3', '#808000', '#ffd8b1', '#000075', '#808080',
            '#ff6347', '#4169e1', '#32cd32', '#ff1493', '#00ced1',
            '#ff8c00', '#9370db', '#00fa9a', '#dc143c', '#00bfff',
            '#adff2f', '#ff69b4', '#1e90ff', '#ff4500', '#da70d6',
            '#20b2aa', '#ff6347', '#7b68ee', '#00ff7f', '#ff1493',
            '#ffa500', '#9932cc', '#00ffff', '#ff0000', '#0000ff',
            '#32cd32', '#ff00ff', '#008b8b', '#b8860b', '#a52a2a',
        ]

        # Unique warehouses and colors
        warehouses = df["assigned_warehouse"].unique().sort().to_list()
        warehouse_colors = {
            w: map_colors[i % len(map_colors)]
            for i, w in enumerate(warehouses)
        }

        # 1) Demand points (colored by assigned warehouse)
        for row in df.iter_rows(named=True):
            w = row["assigned_warehouse"]
            color = warehouse_colors[w]
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=np.log(1 + row["demand"] / 5),
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7,
                popup=(
                    f"Region: {row['region_id']}<br>"
                    f"Assigned warehouse: {w}<br>"
                    f"Demand: {row['demand']}"
                ),
            ).add_to(m)

        # 2) One marker per warehouse (star icon)
        warehouses_df = df.select(
            ["assigned_warehouse", "warehouse_lat", "warehouse_lon"]
        ).unique(subset=["assigned_warehouse"])

        for row in warehouses_df.iter_rows(named=True):
            w = row["assigned_warehouse"]
            color = warehouse_colors[w]
            folium.Marker(
                location=[row["warehouse_lat"], row["warehouse_lon"]],
                popup=f"Warehouse {w}",
                icon=folium.Icon(color="red", icon="star", prefix="fa"),
                tooltip=f"Warehouse {w}",
            ).add_to(m)

        return m


    # 1) Extract assignments (i -> j) from the PuLP solution
    assignments_list = []

    for _i, _j in c:
        if x[(_i,_j)].value() > 0.5:   # assigned
            assignments_list.append(
                {
                    "region_id": _i,
                    "assigned_warehouse": _j,
                }
            )

    assignments_df = pl.DataFrame(assignments_list)

    # 2) Join with region coordinates and demand
    regions_info = pharmacies_aggregated.select(
        ["region_id", "lat", "lon", "demand"]
    )

    assignments_df = assignments_df.join(
        regions_info,
        on="region_id",
        how="left",
    )

    # 3) (Optional but handy) add coordinates of the assigned warehouse itself
    warehouses_info = regions_info.rename(
        {
            "region_id": "assigned_warehouse",
            "lat": "warehouse_lat",
            "lon": "warehouse_lon",
            "demand": "warehouse_demand",  # not needed for the map, but might be useful
        }
    )

    assignments_df = assignments_df.join(
        warehouses_info,
        on="assigned_warehouse",
        how="left",
    )
    return assignments_df, plot_assignments_map


@app.cell(hide_code=True)
def _(
    assignments_df,
    fixed_cost_term,
    mo,
    open_warehouses,
    pl,
    plot_assignments_map,
    problem,
    sc,
    transport_cost_term,
):
    networkSlide = sc.create_slide(
        'Phoenix Spain network solution',
        layout_type='side-by-side',
        page_number=8
    )

    networkSlide.content1 = mo.md(
        r"""
    This map shows the **solution** of our warehouse location model.

    - Each dot represents a demand region (group of pharmacies).
    - The color of a dot indicates the **warehouse it is assigned to**.
    - Regions with the same color are served from the same warehouse.

    By solving the model, we have chosen

    - which warehouses to open,
    - and which regions they should serve,

    such that the total annual cost (fixed cost + transport cost) is minimized.
    """
    )

    metrics_df = pl.DataFrame(
        {
            "Metric": [
                "Number of warehouses",
                "Fixed costs",
                "Transportation costs",
                "Total costs",
            ],
            "Value": [
                f"{len(open_warehouses)}",
                f"{fixed_cost_term.value():,.0f} €",
                f"{transport_cost_term.value():,.0f} €",
                f"{problem.objective.value():,.0f} €",
            ],
        }
    )

    summary_table = mo.ui.table(
        metrics_df,
        show_data_types=False,
        selection=None,
        show_column_summaries=False,
    )
    assignments_map_component = plot_assignments_map(assignments_df)

    networkSlide.content2 = mo.vstack([
        assignments_map_component,
        summary_table
    ])

    networkSlide.render()
    return


@app.cell(hide_code=True)
def _(fixed_costs, np, pharmacies_aggregated, pl):
    # Scenario engine for the slides below: rebuilds f_j and c_ij from the
    # assumptions of Part 1 and solves the WLP directly with SciPy's HiGHS
    # (faster than going through PuLP, so the sliders react quickly).

    BASE_PARAMS = {
        "size": 7000,       # warehouse size (m²)
        "rent": 6.0,        # rent (€/m² per month)
        "markup": 75,       # markup for staff, energy, overhead (%)
        "tour": 400,        # cost per tour (€)
        "speed": 70,        # average speed (km/h)
        "day": 8.0,         # working day (h)
        "min_stop": 9,      # minutes per pharmacy (9 reproduces the stops line of Part 1)
        "deliveries": 1,    # deliveries per pharmacy and day
        "share": 100,       # market share (%)
        "max_drive": 4.0,   # maximum one-way driving time (h)
    }

    def make_scenario_engine(regions_df, fixed_costs_df):
        from scipy.optimize import milp, LinearConstraint, Bounds
        from scipy.sparse import coo_matrix

        regions = regions_df.join(
            fixed_costs_df.select(["region_id", "cost_index"]), on="region_id", how="left"
        ).sort("region_id")
        ids = regions["region_id"].to_list()
        n = len(ids)
        lat, lon = regions["lat"].to_numpy(), regions["lon"].to_numpy()
        la, lo = np.radians(lat), np.radians(lon)
        hav = (
            np.sin((la[:, None] - la[None, :]) / 2) ** 2
            + np.cos(la[:, None]) * np.cos(la[None, :]) * np.sin((lo[:, None] - lo[None, :]) / 2) ** 2
        )
        dist_km = 2 * 6371 * np.arcsin(np.sqrt(hav))  # haversine distance, as in Part 1
        pharmacies = regions["pharmacies"].to_numpy()
        cost_index = regions["cost_index"].to_numpy()

        def inputs(p):
            f = p["size"] * p["rent"] * 12 * (1 + p["markup"] / 100) * cost_index
            drive = dist_km / p["speed"]                  # one-way driving time (h)
            time_in_region = p["day"] - 2 * drive
            stops = np.maximum(1, (time_in_region - 0.5) * 60 / p["min_stop"])
            demand = pharmacies * 250 * p["deliveries"] * p["share"] / 100
            c = np.ceil(demand[:, None] / stops) * p["tour"]
            feasible = (drive <= p["max_drive"]) & (time_in_region >= 0)
            return f, c, feasible

        def solve(f, c, feasible, k=None):
            ii, jj = np.nonzero(feasible)
            m = len(ii)
            nv = n + m
            xi = n + np.arange(m)
            cons = [
                # each region is assigned to exactly one warehouse
                LinearConstraint(coo_matrix((np.ones(m), (ii, xi)), shape=(n, nv)), 1, 1),
                # x_ij <= y_j
                LinearConstraint(
                    coo_matrix(
                        (np.r_[np.ones(m), -np.ones(m)], (np.r_[np.arange(m), np.arange(m)], np.r_[xi, jj])),
                        shape=(m, nv),
                    ),
                    -np.inf, 0,
                ),
            ]
            if k is not None:  # exactly k warehouses
                cons.append(LinearConstraint(
                    coo_matrix((np.ones(n), (np.zeros(n, dtype=int), np.arange(n))), shape=(1, nv)), k, k
                ))
            res = milp(np.r_[f, c[ii, jj]], constraints=cons, integrality=np.ones(nv), bounds=Bounds(0, 1))
            if not res.success:
                return None
            y = res.x[:n] > 0.5
            x = res.x[n:] > 0.5
            assigned = np.empty(n, dtype=int)
            assigned[ii[x]] = jj[x]
            fixed = float(f[y].sum())
            transport = float(c[ii[x], jj[x]].sum())
            return {"k": int(y.sum()), "fixed": fixed, "transport": transport,
                    "total": fixed + transport, "assigned": assigned}

        def min_warehouses(feasible):
            # smallest number of warehouses that can reach every region
            ii, jj = np.nonzero(feasible)
            cover = coo_matrix((np.ones(len(ii)), (ii, jj)), shape=(n, n))
            res = milp(np.ones(n), constraints=[LinearConstraint(cover, 1, np.inf)],
                       integrality=np.ones(n), bounds=Bounds(0, 1))
            return int(round(res.fun))

        def run(p):
            f, c, feasible = inputs(p)
            best = solve(f, c, feasible)
            k_min = min_warehouses(feasible)
            curve = []
            for k in range(k_min, min(n, max(25, best["k"] + 8)) + 1):
                s = best if k == best["k"] else solve(f, c, feasible, k)
                if s is not None:
                    curve.append({"k": k, "Fixed costs": s["fixed"] / 1e6,
                                  "Transport costs": s["transport"] / 1e6,
                                  "Total costs": s["total"] / 1e6})
            a = best["assigned"]
            best["k_min"] = k_min
            best["curve"] = curve
            best["assignments"] = pl.DataFrame({
                "region_id": ids,
                "lat": lat,
                "lon": lon,
                "demand": regions["demand"],
                "assigned_warehouse": [ids[j] for j in a],
                "warehouse_lat": lat[a],
                "warehouse_lon": lon[a],
            })
            return best

        return run

    run_scenario = make_scenario_engine(pharmacies_aggregated, fixed_costs)
    return BASE_PARAMS, run_scenario


@app.cell(hide_code=True)
def _(BASE_PARAMS, run_scenario):
    base_result = run_scenario(BASE_PARAMS)
    return (base_result,)


@app.cell(hide_code=True)
def _(alt):
    COST_COLORS = {
        "Fixed costs": "#2a78d6",
        "Transport costs": "#eb6834",
        "Total costs": "#3a3a38",
    }

    def cost_curve_chart(base, scenario=None, width=460, height=200):
        """Fixed, transport and total costs over the number of warehouses.
        With a scenario, the base case is drawn dashed and faded."""
        cases = [("Base case", base)]
        if scenario is not None:
            cases.append(("Scenario", scenario))
        lines, optima = [], []
        for case, res in cases:
            for r in res["curve"]:
                for cost_type in COST_COLORS:
                    lines.append({"Warehouses": r["k"], "Cost type": cost_type,
                                  "Million €": round(r[cost_type], 2), "Case": case})
            optima.append({"Warehouses": res["k"], "Million €": round(res["total"] / 1e6, 2),
                           "Case": case, "label": f"optimum: {res['k']}"})
        y_max = 1.6 * max(res["total"] for _, res in cases) / 1e6
        x_max = max(r["k"] for _, res in cases for r in res["curve"])
        k_min = cases[-1][1]["k_min"]

        case_scale = ["Base case", "Scenario"]
        with_scenario = scenario is not None
        x = alt.X("Warehouses:Q", title="Number of warehouses",
                  scale=alt.Scale(domain=[0.5, x_max + 0.5], nice=False),
                  axis=alt.Axis(tickMinStep=1, format="d", grid=False))
        y = alt.Y("Million €:Q", title="Annual cost (million €)",
                  scale=alt.Scale(domain=[0, y_max], nice=False),
                  axis=alt.Axis(gridColor="#eeeeee"))
        opacity = alt.Opacity("Case:N", legend=None,
                              scale=alt.Scale(domain=case_scale, range=[0.45 if with_scenario else 1, 1]))

        line_data = alt.Chart(alt.Data(values=lines))
        line_layer = line_data.mark_line(strokeWidth=2, clip=True).encode(
            x=x, y=y, opacity=opacity,
            color=alt.Color("Cost type:N", legend=alt.Legend(orient="top", title=None),
                            scale=alt.Scale(domain=list(COST_COLORS), range=list(COST_COLORS.values()))),
            strokeDash=alt.StrokeDash(
                "Case:N",
                legend=alt.Legend(orient="top", title=None) if with_scenario else None,
                scale=alt.Scale(domain=case_scale, range=[[6, 4] if with_scenario else [1, 0], [1, 0]]),
            ),
        )
        hover_layer = line_data.mark_circle(size=150, opacity=0, clip=True).encode(
            x=x, y=y,
            tooltip=[alt.Tooltip("Case:N"), alt.Tooltip("Warehouses:Q"), alt.Tooltip("Cost type:N"),
                     alt.Tooltip("Million €:Q", format=".1f")],
        )
        opt_data = alt.Chart(alt.Data(values=optima))
        opt_points = opt_data.mark_point(filled=True, size=110, color="#3a3a38", stroke="white",
                                         strokeWidth=1.5).encode(x=x, y=y, opacity=opacity)
        opt_label = opt_data.transform_filter(alt.datum.Case == cases[-1][0]).mark_text(
            dy=-14, fontSize=12, fontWeight="bold", color="#3a3a38"
        ).encode(x=x, y=y, text="label:N")

        layers = [line_layer, hover_layer, opt_points, opt_label]
        if k_min > 1:  # shade numbers of warehouses that cannot reach every region
            band = alt.Data(values=[{"x0": 0.5, "x1": k_min - 0.5, "xm": k_min / 2}])
            layers = [
                alt.Chart(band).mark_rect(color="#9ca3af", opacity=0.18).encode(x="x0:Q", x2="x1:Q"),
                alt.Chart(band).mark_text(angle=270, fontSize=11, color="#6b7280", text="infeasible").encode(
                    x="xm:Q", y=alt.value(height / 2)
                ),
            ] + layers
        return (
            alt.layer(*layers)
            .properties(width=width, height=height)
            .configure_view(stroke=None)
            .configure_axis(labelFontSize=12, titleFontSize=13, labelColor="#52514e", titleColor="#52514e")
            .configure_legend(labelFontSize=13, symbolStrokeWidth=2)
        )
    return (cost_curve_chart,)


@app.cell(hide_code=True)
def _(mo):
    reset_button = mo.ui.button(label="↺ Reset", value=0, on_click=lambda v: v + 1)
    return (reset_button,)


@app.cell(hide_code=True)
def _(BASE_PARAMS, mo, reset_button):
    reset_button.value  # clicking "reset" re-creates the sliders with their base values

    _settings = {  # key: (label, start, stop, step)
        "size": ("Warehouse size (m²)", 3000, 15000, 500),
        "rent": ("Rent (€/m² per month)", 2, 15, 0.5),
        "markup": ("Markup staff, energy, overhead (%)", 0, 200, 5),
        "tour": ("Cost per tour (€)", 200, 800, 10),
        "speed": ("Average speed (km/h)", 40, 100, 5),
        "day": ("Working day (h)", 6, 12, 0.5),
        "min_stop": ("Minutes per pharmacy", 5, 15, 1),
        "deliveries": ("Deliveries per pharmacy and day", 1, 3, 1),
        "share": ("Market share (%)", 10, 100, 10),
        "max_drive": ("Max. one-way driving time (h)", 1.5, 5, 0.5),
    }
    scenario_sliders = mo.ui.dictionary({
        _key: mo.ui.slider(start=_start, stop=_stop, step=_step, value=BASE_PARAMS[_key],
                           show_value=True, debounce=True)
        for _key, (_label, _start, _stop, _step) in _settings.items()
    })
    _labels = {_key: _setting[0] for _key, _setting in _settings.items()}

    def slider_row(key, labels=_labels):
        """One compact row: label on the left, slider on the right."""
        return mo.hstack(
            [mo.Html(f'<span style="font-size: 15px; color: #374151;">{labels[key]}</span>'),
             scenario_sliders[key]],
            widths=[0.48, 0.52], align="center", gap=0.5,
        )
    return scenario_sliders, slider_row


@app.cell(hide_code=True)
def _(
    BASE_PARAMS,
    base_result,
    cost_curve_chart,
    folium,
    mo,
    plot_assignments_map,
    run_scenario,
    scenario_sliders,
):
    scenario_params = dict(scenario_sliders.value)
    scenario_result = base_result if scenario_params == BASE_PARAMS else run_scenario(scenario_params)

    def _sized_map(height):
        _m = plot_assignments_map(scenario_result["assignments"])
        _m.options["zoom_snap"] = 0.25
        _m.fit_bounds([[36.0, -9.3], [43.8, 3.3]])  # mainland Spain
        _m.add_to(folium.Figure(width="100%", height=height))
        return _m

    lab_map = _sized_map(260)
    scenario_map = _sized_map(190)
    lab_chart = cost_curve_chart(base_result, scenario_result, height=210)
    scenario_chart = cost_curve_chart(base_result, scenario_result, height=150)

    _b, _s = base_result, scenario_result
    _change = (_s["total"] / _b["total"] - 1) * 100
    scenario_kpis = mo.Html(
        f'<span style="font-size: 16px; white-space: nowrap;">'
        f"<b>Warehouses:</b> {_b['k']} → <b>{_s['k']}</b> &nbsp;·&nbsp; "
        f"<b>Total cost:</b> {_b['total'] / 1e6:.1f} → <b>{_s['total'] / 1e6:.1f} M€</b> ({_change:+.0f} %)"
        f"</span>"
    )
    lab_kpis = mo.md(
        f"""
    | | Warehouses | Fixed costs | Transport costs | Total costs |
    |---|---:|---:|---:|---:|
    | Base case | {_b['k']} | {_b['fixed'] / 1e6:.1f} M€ | {_b['transport'] / 1e6:.1f} M€ | {_b['total'] / 1e6:.1f} M€ |
    | **Scenario** | **{_s['k']}** | **{_s['fixed'] / 1e6:.1f} M€** | **{_s['transport'] / 1e6:.1f} M€** | **{_s['total'] / 1e6:.1f} M€** |
    """
    )
    return (
        lab_chart,
        lab_kpis,
        lab_map,
        scenario_chart,
        scenario_kpis,
        scenario_map,
    )


@app.cell(hide_code=True)
def _(
    mo,
    reset_button,
    scenario_chart,
    scenario_kpis,
    scenario_map,
    slider_row,
):
    def scenario_panel(*keys):
        """Right column of a scenario slide: the relevant sliders, KPIs, cost curves and map."""
        controls = mo.vstack([slider_row(k) for k in keys], gap=0.2)
        return mo.vstack(
            [
                controls,
                mo.hstack([scenario_kpis, reset_button], justify="space-between", align="center"),
                scenario_chart,
                scenario_map,
            ],
            gap=0.4,
        )
    return (scenario_panel,)


@app.cell(hide_code=True)
def _(base_result, cost_curve_chart, mo, sc):
    tradeOffSlide = sc.create_slide(
        'Fixed vs. transport costs – where does the optimum come from?',
        layout_type='side-by-side',
        page_number=9
    )

    tradeOffSlide.content1 = mo.md(
        rf"""
    **Why does the solver open exactly {base_result['k']} warehouses?**

    To see the trade-off, we solve the model once for every number of warehouses \(k\)
    and add one constraint: \(\sum_{{j \in J}} y_j = k\).

    - **Fixed costs** grow with every additional warehouse.
    - **Transport costs** fall because tours get shorter – but each additional
      warehouse saves less than the one before.
    - **Total costs** are lowest where both effects balance.

    **Think about it**

    - Why does the curve only start at {base_result['k_min']} warehouses?
    - The total cost curve is very flat around the optimum.
      What does this mean for Phoenix?

    We will come back to this chart in every scenario.
    """
    )

    tradeOffSlide.content2 = mo.vstack([cost_curve_chart(base_result, height=400)])

    tradeOffSlide.render()
    return


@app.cell(hide_code=True)
def _(lab_chart, lab_kpis, lab_map, mo, reset_button, sc, slider_row):
    labSlide = sc.create_slide(
        'Scenario lab: change the assumptions',
        layout_type='side-by-side',
        page_number=10
    )

    labSlide.content1 = mo.vstack(
        [
            mo.md("**Warehouse (fixed costs)**"),
            slider_row("size"), slider_row("rent"), slider_row("markup"),
            mo.md("**Transport**"),
            slider_row("tour"), slider_row("speed"), slider_row("day"), slider_row("min_stop"),
            mo.md("**Demand and service**"),
            slider_row("deliveries"), slider_row("share"), slider_row("max_drive"),
            reset_button,
            lab_kpis,
        ],
        gap=0.3,
    )

    labSlide.content2 = mo.vstack([lab_map, lab_chart], gap=0.5)

    labSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc, scenario_panel):
    interestSlide = sc.create_slide(
        'Scenario 1: Rising interest rates',
        layout_type='side-by-side',
        page_number=11
    )

    interestSlide.content1 = mo.md(
        r"""
    **Situation:** The ECB raises interest rates. Rents for logistics
    properties in Spain rise from 6 to 8 €/m² per month, and higher financing
    costs push the markup from 75 % to 90 %.

    **1 · Predict** – before you touch a slider: more, fewer or the same
    number of warehouses? Which cost curve moves?

    **2 · Test** – set rent and markup on the right.

    **3 · Explain** – use the cost curves (dashed = base case).

    **4 · Dig deeper** – How high do rents have to rise before Phoenix
    closes a warehouse?

    **Discuss:** Higher interest rates also make inventory more expensive –
    and our model ignores inventory. Would this push Phoenix towards
    fewer or more warehouses?
    """
    )

    interestSlide.content2 = scenario_panel("rent", "markup")

    interestSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc, scenario_panel):
    dieselSlide = sc.create_slide(
        'Scenario 2: Diesel price shock',
        layout_type='side-by-side',
        page_number=12
    )

    dieselSlide.content1 = mo.md(
        r"""
    **Situation:** The diesel price jumps from 1.50 € to 2.25 € per litre.

    **1 · Estimate** – How much does this increase the cost per tour
    (today 400 €)?

    **2 · Predict, test, explain** – set the new cost per tour on the right.

    **3 · Dig deeper** – From which cost per tour does the network change?
    Which real-world shocks could push tour costs that high?

    **Discuss:** In our model, a tour costs the same no matter how far it
    goes – but fuel costs depend on kilometres. Which regions does the
    price shock really hit hardest?
    """
    )

    dieselSlide.content2 = scenario_panel("tour")

    dieselSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc, scenario_panel):
    congestionSlide = sc.create_slide(
        'Scenario 3: Congestion and low-emission zones',
        layout_type='side-by-side',
        page_number=13
    )

    congestionSlide.content1 = mo.md(
        r"""
    **Situation:** More traffic and new low-emission zones in Spanish cities
    slow down Phoenix's vans: the average speed drops from 70 to 55 km/h.

    **1 · Predict** – How strong is the effect compared to the diesel shock?

    **2 · Test** – set the average speed on the right.

    **3 · Explain** – Which parts of our transport cost calculation depend
    on the speed? Also look at where the cost curves start.

    **Discuss:** Why does the network react so differently to slower vans
    than to the diesel price shock?
    """
    )

    congestionSlide.content2 = scenario_panel("speed")

    congestionSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, pharmacies_aggregated, sc, scenario_panel):
    deliveriesSlide = sc.create_slide(
        'Scenario 4: Two deliveries per day',
        layout_type='side-by-side',
        page_number=14
    )

    _n_pharmacies = int(pharmacies_aggregated["pharmacies"].sum())
    deliveriesSlide.content1 = mo.md(
        rf"""
    **Situation:** German pharmacies receive several deliveries per day.
    Spanish pharmacies now ask Phoenix for the same service:
    two deliveries per day instead of one.

    **1 · Predict** – How does the network change? Which cost curve moves?

    **2 · Test and explain** – set the deliveries per day on the right.

    **3 · Business case** – Phoenix serves {_n_pharmacies:,} pharmacies on
    250 days per year. Which surcharge per additional delivery covers
    the extra cost?

    **Discuss:** Re-optimising saves about 1.1 M€ per year compared with
    keeping today's 9 warehouses – but Phoenix would have to open 6 and
    close 2. Would you do it? What else would you need to know?
    """
    )

    deliveriesSlide.content2 = scenario_panel("deliveries")

    deliveriesSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc, scenario_panel):
    marketEntrySlide = sc.create_slide(
        'Scenario 5: Entering a new market',
        layout_type='side-by-side',
        page_number=15
    )

    marketEntrySlide.content1 = mo.md(
        r"""
    **Situation:** Phoenix will not win all Spanish pharmacies at once.
    For the first years, it expects a market share of about 30 %.

    **1 · Predict** – How many warehouses – and where?

    **2 · Test** – set the market share and compare the map with the
    base case (page 8).

    **3 · Explain** – Why is there no warehouse in Madrid,
    Spain's largest market?

    **Discuss:** Phoenix plans to reach 100 % within five years. Should it
    build the network that is optimal for 30 % today – or start with part
    of the network that is optimal for 100 %?
    """
    )

    marketEntrySlide.content2 = scenario_panel("share")

    marketEntrySlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc, scenario_panel):
    technologySlide = sc.create_slide(
        'Scenario 6: New technologies',
        layout_type='side-by-side',
        page_number=16
    )

    technologySlide.content1 = mo.md(
        r"""
    **Situation:** Two technologies could change pharmaceutical distribution:
    autonomous trucks and delivery drones.

    **1 · Translate** – Which assumptions does each technology change,
    and in which direction?

    **2 · Build your scenario** – set the sliders and note how many
    warehouses Phoenix needs.

    **3 · Defend it** – Compare your scenario with your neighbours'.
    Why do you end up with different networks?

    **Discuss:** A delivery drone carries one small parcel and flies about
    20 km. What does that mean for Phoenix's warehouse network? For which
    deliveries would drones make sense?
    """
    )

    technologySlide.content2 = scenario_panel("tour", "speed", "day", "max_drive")

    technologySlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    limitationsSlide = sc.create_slide(
        'How simple is our model – and what could we add?',
        layout_type='1-column',
        page_number=17
    )

    limitationsSlide.content1 = mo.md(
        r"""
    To keep the Phoenix Spain model tractable, we made several simplifying choices:

    - **Sites:** every region can host a warehouse  
      → in practice, we would restrict this to a few realistic sites.

    - **Capacity:** warehouses have unlimited capacity  
      → we could add a maximum demand each site can handle.

    - **Demand:** one fixed demand number per region  
      → we could analyse demand scenarios or growth.

    Each of these “shortcuts” could be turned into a richer extension
    if we wanted a more realistic but also more complex model.
    """
    )

    limitationsSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    blockSummarySlide = sc.create_slide(
        'Phoenix enters Spain – what you should take away',
        layout_type='1-column',
        page_number=18
    )

    blockSummarySlide.content1 = mo.md(
        r"""
    Across the three sessions, we went from intuition to an optimization model and back to business insight.

    1. **Center of Gravity (CoG)**  
       - Started from real pharmacy data in Spain and aggregated it into demand regions.  
       - Used CoG to get simple, geometric candidate locations and to see extremes:
         one national DC vs. one DC per province.

    2. **Warehouse Location Problem (WLP)**  
       - Turned Phoenix’s story into a cost-based model with
         demand \(d_i\), fixed costs \(f_j\), and transport costs \(c_{ij}\).  
       - Defined decision variables \(x_{ij}\), \(y_j\), an objective function,
         and a small set of constraints.

    3. **Solving and analysing the network**  
       - Implemented the WLP in Python with PuLP and solved it for Spain.  
       - Visualised the optimal network on a map and separated fixed and transport costs.  
       - Used the trade-off between fixed and transport costs to analyse business
         scenarios: interest rates, fuel prices, congestion, service level,
         market entry and new technologies.
    """
    )

    blockSummarySlide.render()
    return


if __name__ == "__main__":
    app.run()
