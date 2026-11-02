import marimo

__generated_with = "0.18.1"
app = marimo.App(
    width="medium",
    app_title="Warehouse Location Problem",
    layout_file="layouts/warehouse_location_part_1.slides.json",
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
            "numpy",
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
    import warnings
    warnings.filterwarnings("ignore", message=".*narwhals.*is_pandas_dataframe.*")
    return alt, mo, np, pl


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
            left = mo.vstack([left_content], gap=0).style({"gap": "0", "margin": "0", "padding": "0"})
            right = mo.vstack([right_content], gap=0).style({"gap": "0", "margin": "0", "padding": "0"})
            body = mo.Html(
                f"""
                <div class="slide-body" style="flex: 1 1 auto; min-height: 0; display: flex; flex-direction: column;">
                    <style>
                        ul {{ margin-top: -0.2em !important; }}
                        .slide-col.tight-md .paragraph {{ margin-block: 0 !important; margin: 0 0 4px 0 !important; font-size: 19px !important; }}
                        .slide-col.tight-md span.paragraph {{ margin-block: 0 !important; margin: 0 0 4px 0 !important; font-size: 19px !important; }}
                        li {{ font-size: 19px !important; }}
                        li * {{ font-size: 19px !important; }}
                    </style>
                    <div class="slide-cols" style="display: grid; grid-template-columns: 1fr 1fr; gap: {GAP}px; height: 100%; min-height: 0;">
                        <div class="slide-col tight-md" style="min-height: 0; overflow: auto; padding-right: 2px;">
                            {left}
                        </div>
                        <div class="slide-col tight-md" style="min-height: 0; overflow: auto; padding-right: 2px;">
                            {right}
                        </div>
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
        subtitle="Determining the optimal network"
    )
    sc.styles()
    titleSlide.render()
    return


@app.cell(hide_code=True)
def _(DataURLs, mo, sc):
    bridgeSlide = sc.create_slide(
        'From Center of Gravity to Warehouse Location',
        layout_type='side-by-side',
        page_number=2
    )

    bridgeSlide.content1 = mo.md(
        """
        In the previous session, we explored two extreme ideas:

        - **One CoG warehouse for all of Spain**  
          → simple and cheap to manage, but leads to long transport distances and a strong dependency on a single location.

        - **Many warehouses, one per region**  
          → very short transport distances and good service, but likely **far too expensive** to operate.

        Neither extreme looks like a realistic plan for Phoenix.

        In this session, we move from a geometric view to a **cost-based optimization model**:

        - We let a model decide **how many** DCs to open and **where**.
        - It balances **fixed warehouse-opening costs** and **variable transport costs**
          to serve all demand in Spain.
        """
    )

    bridgeSlide.content2 = mo.vstack(
        [
            mo.image(f'{DataURLs.IMG_BASE}/spain_cog_single_dc.png', width=551 * 0.75, height=329 * 0.75),
            mo.image(f'{DataURLs.IMG_BASE}/spain_many_warehouses.png', width=551 * 0.75, height=329 * 0.75)
        ],
        gap=3
    )

    bridgeSlide.render()
    return


@app.cell(hide_code=True)
def _(DataURLs, mo, sc):
    businessQuestionSlide = sc.create_slide(
        'Phoenix Spain: The Warehouse Location Decision',
        layout_type='side-by-side',
        page_number=3
    )

    businessQuestionSlide.content1 = mo.md(
        """
        Phoenix wants to design its distribution network for Spain:

        - Demand comes from many **regions** across the country
          (aggregated groups of pharmacies).
        - In principle, Phoenix could open a warehouse in **any region**:
          every demand region is also a possible warehouse location.
        - The key business question:

            **Which warehouses should we open, and which regions should each warehouse serve?**

        What Phoenix cares about:
        - Serving **all demand** reliably.
        - Keeping **total annual cost** under control:
          fewer warehouses are cheaper to run but mean longer delivery distances;
          more warehouses are closer to customers but more expensive to operate.
        """
    )

    businessQuestionSlide.content2 = mo.image(f'{DataURLs.IMG_BASE}/wlp_planner.png', width=551 * 0.75, height=329 * 0.75)

    businessQuestionSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    dataOverviewSlide = sc.create_slide(
        'What data does Phoenix need for this decision?',
        layout_type='1-column',
        page_number=4
    )

    dataOverviewSlide.content1 = mo.md(
        """
        To turn Phoenix's Spain story into a structured decision problem,
        we first need to collect the right data.

        At a high level, Phoenix needs three types of information:

        1. **Demand across Spain**  
           - How much demand comes from each region?  
           - Where are these regions located on the map?  

        2. **Possible warehouse locations**  
           - In which regions could Phoenix realistically operate a warehouse?  
           - How expensive would it be to run a warehouse in each of these locations?

        3. **Shipping costs between warehouses and regions**  
           - How costly is it to ship one unit (or visit) from a potential warehouse location
             to each demand region?
        """
    )

    dataOverviewSlide.render()
    return


@app.cell(hide_code=True)
def _(DataURLs, pl):
    pharmacies_raw = pl.read_csv(
        f'{DataURLs.BASE}/pharmacies_spain.csv',
        schema_overrides={"postal_code": pl.Utf8}
    )
    return (pharmacies_raw,)


@app.cell(hide_code=True)
def _(pl):
    def aggregate_by_zipcode(df: pl.DataFrame, digits: int = 2):
        """
        Aggregate pharmacies by the first N digits of their postal code.

        Args:
            df: DataFrame with 'postal_code', 'lat', 'lon' columns
            digits: Number of postal code digits to use for aggregation

        Returns:
            DataFrame with region_id, lat, lon, demand (count of pharmacies)
        """
        # Extract first N digits of postal code
        df_with_region = df.with_columns(
            pl.col("postal_code").cast(pl.Utf8).str.slice(0, digits).alias("region_id")
        )

        # Group by region and aggregate
        aggregated = df_with_region.group_by("region_id").agg([
            pl.col("lat").median().alias("lat"),
            pl.col("lon").median().alias("lon"),
            pl.len().alias("demand")
        ])

        return aggregated.sort("region_id")
    return (aggregate_by_zipcode,)


@app.cell(hide_code=True)
def _(aggregate_by_zipcode, pharmacies_raw, pl):
    pharmacies_aggregated = aggregate_by_zipcode(pharmacies_raw, 2)

    pharmacies_aggregated = pharmacies_aggregated.rename({'demand': 'pharmacies'})

    pharmacies_aggregated = pharmacies_aggregated.with_columns((pl.col("pharmacies") * 250).alias("demand"))
    return (pharmacies_aggregated,)


@app.cell(hide_code=True)
def _(mo, pharmacies_aggregated, sc):
    demandSlide = sc.create_slide(
        'Demand across Spain',
        layout_type='side-by-side',
        page_number=5
    )

    demandSlide.content1 = mo.md(
        r"""
        To design Phoenix's Spain network, we first need to know
        **how much demand** comes from each region over a whole year.

        To **translate this into regional demand**:

        - For each region, count how many **pharmacies** are located there.  
        - Multiply by the number of **business days per year** (e.g. 250)
          to get the total number of **required visits per year**.

        We will use the following **notation**:

        - Let \(I\) be the set of regions in Spain.  
        - \(d_i\): annual number of visits (pharmacy deliveries) required in region \(i\).
        """
    )

    _demand_aggregated_table = mo.ui.table(
        pharmacies_aggregated.select(['region_id', 'pharmacies', 'demand']),
        show_data_types=False,
        selection=None,
        show_column_summaries=False
    )

    demandSlide.content2 = mo.vstack([_demand_aggregated_table])

    demandSlide.render()
    return


@app.cell(hide_code=True)
def _(mo):
    monthly_rent_slider = mo.ui.slider(start=2, stop=12, value=6, show_value=True, label='Monthly rent')
    markup_slider = mo.ui.slider(start=0.5, stop=1, step=0.05, value=0.75, show_value=True, label='Markup')
    return markup_slider, monthly_rent_slider


@app.cell(hide_code=True)
def _(markup_slider, monthly_rent_slider, pl):
    cost_index_by_region = {
        # High-cost regions
        "08": 1.6,
        "28": 1.6,
        "01": 1.2,
        "17": 1.2,
        "20": 1.2,
        "25": 1.2,
        "43": 1.2,
        "48": 1.2,

        # Medium-cost regions
        "03": 1.0,
        "04": 1.0,
        "11": 1.0,
        "12": 1.0,
        "14": 1.0,
        "18": 1.0,
        "21": 1.0,
        "23": 1.0,
        "29": 1.0,
        "31": 1.0,
        "33": 1.0,
        "39": 1.0,
        "41": 1.0,
        "46": 1.0,

        # Lower-cost regions
        "02": 0.8,
        "05": 0.8,
        "06": 0.8,
        "09": 0.8,
        "10": 0.8,
        "13": 0.8,
        "15": 0.8,
        "16": 0.8,
        "19": 0.8,
        "22": 0.8,
        "24": 0.8,
        "26": 0.8,
        "27": 0.8,
        "30": 0.8,
        "32": 0.8,
        "34": 0.8,
        "36": 0.8,
        "37": 0.8,
        "40": 0.8,
        "42": 0.8,
        "44": 0.8,
        "45": 0.8,
        "47": 0.8,
        "49": 0.8,
        "50": 0.8,
    }

    region_names = {
        "01": "Álava",
        "02": "Albacete",
        "03": "Alicante",
        "04": "Almería",
        "05": "Ávila",
        "06": "Badajoz",
        "08": "Barcelona",
        "09": "Burgos",
        "10": "Cáceres",
        "11": "Cádiz",
        "12": "Castellón",
        "13": "Ciudad Real",
        "14": "Córdoba",
        "15": "A Coruña",
        "16": "Cuenca",
        "17": "Girona",
        "18": "Granada",
        "19": "Guadalajara",
        "20": "Gipuzkoa",
        "21": "Huelva",
        "22": "Huesca",
        "23": "Jaén",
        "24": "León",
        "25": "Lleida",
        "26": "La Rioja",
        "27": "Lugo",
        "28": "Madrid",
        "29": "Málaga",
        "30": "Murcia",
        "31": "Navarra",
        "32": "Ourense",
        "33": "Asturias",
        "34": "Palencia",
        "36": "Pontevedra",
        "37": "Salamanca",
        "39": "Cantabria",
        "40": "Segovia",
        "41": "Sevilla",
        "42": "Soria",
        "43": "Tarragona",
        "44": "Teruel",
        "45": "Toledo",
        "46": "Valencia",
        "47": "Valladolid",
        "48": "Bizkaia",
        "49": "Zamora",
        "50": "Zaragoza",
    }



    base_fixed_cost = 7000 * monthly_rent_slider.value * 12 * (1 + markup_slider.value)

    rows = []
    for region_id, ci in cost_index_by_region.items():
        rows.append(
            {
                "region_id": region_id,
                "name": region_names.get(region_id, "Unknown"),
                "base_fixed_cost": round(base_fixed_cost),
                "cost_index": ci,
                "fixed_cost": round(base_fixed_cost * ci),
            }
        )

    fixed_costs = pl.DataFrame(rows).sort("region_id")
    return (fixed_costs,)


@app.cell(hide_code=True)
def _(fixed_costs, markup_slider, mo, monthly_rent_slider, sc):
    fixedCostSlide = sc.create_slide(
        'Possible warehouse locations and fixed costs',
        layout_type='side-by-side',
        page_number=6
    )

    fixedCostSlide.content1 = mo.md(
    r"""
    We assume that any region can be upgraded to a distribution center location.

    We use a **simple way** to approximate the costs for the warehouses:
    - Choose a standard warehouse size for Phoenix in Spain (e.g. 7000 m²)
    - Use typical industrial rents in Spain to get a base annual cost for a standard DC (2€ - 12€ per month)
    - Add a markup for staff, energy, maintenance, and overhead to obtain a single base_fixed_cost per year (50% - 100%)
    - Let provinces differ through a regional cost index

    We will use the following **notation**:
    - Let $J$ be the set of possible warehouse locations.  
    - \(f_j\): annual fixed cost of operating a warehouse in region \(j\).
    """
    )

    _fixed_costs_table = mo.ui.table(
        fixed_costs,
        show_data_types=False,
        selection=None,
        show_column_summaries=False
    )

    fixedCostSlide.content2 = mo.vstack([
        monthly_rent_slider,
        markup_slider,
        _fixed_costs_table
    ])

    fixedCostSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    costSlide = sc.create_slide(
        'Shipping costs between warehouses and regions',
        layout_type='side-by-side',
        page_number=7
    )

    costSlide.content1 = mo.md(
    r"""
    Now we want to estimate the annual transport cost if a warehouse in region \(j\)
    serves all demand of region \(i\).

    We use two **ingredients**:
    - The annual demand \(d_i\) (number of visits per year).
    - How many pharmacies fit into one tour: this depends on
      travel time and service time (we will look at tour planning
      in detail in the last-mile part of this chapter).

    We will use the following **notation**:
    - **\(c_{ij}\)** = annual transport cost if region \(i\) is served from warehouse \(j\).
    """
    )

    costSlide.content2 = mo.md(
    r"""
    We use a simple approach to estimate these costs:
    1. For each pair (warehouse \(j\), region \(i\)), compute the
    round-trip distance between their centers and convert it into
    a driving time.
    2. Assume:
       - a fixed working day length (e.g. 8 hours),
       - a fixed service time per pharmacy (e.g. 5 minutes).
       This tells us how many stops per tour are feasible from \(j\) to \(i\):
           more travel time ⇒ fewer pharmacies per tour.
    3. Convert annual demand into tours per year:

        $\text{tours}_{ij} \approx \frac{\text{annual visits } d_i}{\text{stops per tour from } j \text{ to } i}.$

    4. Estimate the cost per tour including vehicle, driver, fuel
       (for example 400€ for an 8-hour day).

        $c_{ij} = \text{tours}_{ij} \times \text{cost\_per\_tour}.$

    **Note:** We exclude pairs where one-way driving exceeds 4 hours (infeasible for same-day service).
    """
    )

    costSlide.render()
    return


@app.cell(hide_code=True)
def _(alt, np, pl):
    def stops_per_hour_plot():
        time_values = np.linspace(2, 8, 7)  # 0, 0.5, ..., 8

        m = (50 - 10) / (8 - 2)   # slope
        b = 10 - m * 2            # intercept

        stops_values = m * time_values + b
        stops_values = np.clip(stops_values, a_min=0, a_max=None)  # no negative stops

        stops_df = pl.DataFrame(
            {
                "time_in_region_hours": time_values,
                "stops_per_tour": stops_values,
            }
        )

        # Altair line chart
        stops_chart = (
            alt.Chart(stops_df.to_pandas(), height = 170, width=500)
            .mark_line(point=True)
            .encode(
                x=alt.X("time_in_region_hours", title="Time spent in region (hours)"),
                y=alt.Y("stops_per_tour", title="Number of stops per tour"),
            )
        )
        return stops_chart
    return (stops_per_hour_plot,)


@app.cell(hide_code=True)
def _(np, pl):
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great-circle distance between two points on Earth (in km).
        """
        R = 6371  # Earth's radius in km

        lat1_rad, lat2_rad = np.radians(lat1), np.radians(lat2)
        dlat = np.radians(lat2 - lat1)
        dlon = np.radians(lon2 - lon1)

        a = np.sin(dlat / 2) ** 2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2) ** 2
        c = 2 * np.arcsin(np.sqrt(a))

        return R * c

    def create_transportation_costs(
        df: pl.DataFrame,
        avg_speed_kmh: float = 70.0
    ) -> pl.DataFrame:
        """
        Create a dataframe with transportation costs between all pairs of regions.

        Args:
            df: DataFrame with 'region_id', 'lat', 'lon', 'demand' columns
            avg_speed_kmh: Average driving speed in km/h (default: 70)

        Returns:
            DataFrame with columns: i_region_id, j_region_id, distance_km, driving_time_hours,
                                   time_in_region, demand_i, stops_per_tour, annual_tours
        """
        regions = df.select(["region_id", "lat", "lon", "demand"]).to_dicts()

        # Stops per tour formula: stops = m * time_in_region + b
        m = (50 - 10) / (8 - 2)  # slope
        b = 10 - m * 2           # intercept

        rows = []
        for i_region in regions:
            for j_region in regions:
                distance = haversine_distance(
                    i_region["lat"], i_region["lon"],
                    j_region["lat"], j_region["lon"]
                )
                driving_time = distance / avg_speed_kmh

                if driving_time > 4:
                    continue

                time_in_region = 8 - 2 * driving_time
                stops_per_tour = max(1, m * time_in_region + b)  # at least 1 stop
                demand_i = i_region["demand"]
                annual_tours = demand_i / stops_per_tour

                rows.append({
                    "i_region_id": i_region["region_id"],
                    "j_region_id": j_region["region_id"],
                    "distance_km": round(distance, 2),
                    "driving_time_hours": round(driving_time, 2),
                    "time_in_region": round(time_in_region, 2),
                    "demand_i": demand_i,
                    "stops_per_tour": round(stops_per_tour, 2),
                    "annual_tours": np.ceil(annual_tours),
                    'c_ij': np.ceil(annual_tours) * 400
                })

        return pl.DataFrame(rows)
    return (create_transportation_costs,)


@app.cell(hide_code=True)
def _(create_transportation_costs, pharmacies_aggregated):
    transportation_costs = create_transportation_costs(pharmacies_aggregated, avg_speed_kmh=70.0)
    return (transportation_costs,)


@app.cell(hide_code=True)
def _(mo, sc, stops_per_hour_plot, transportation_costs):
    stopsCostSlide = sc.create_slide(
        'From time in region to transport costs',
        layout_type='side-by-side',
        page_number=8
    )

    stops_plot = stops_per_hour_plot()

    stopsCostSlide.content1 = mo.vstack(
        [
            mo.md(
                r"""
    The more time a vehicle can spend inside a region, the more pharmacies it can visit in a single tour.
    **Rule of thumb:** ≈ 10 minutes per pharmacy (≈ 5 min service + ≈ 5 min driving to the next one).

    To keep things simple, we approximate this relationship with a straight line:
    - If a vehicle can only spend 2 hours in the region, it can visit about 10 pharmacies.
    - If it can spend the full 8-hour working day in the region, it can visit about 50 pharmacies.
    """
            ),
            stops_plot,
        ]
    )

    transportation_costs_table = mo.ui.table(
        transportation_costs.rename(
            {
                'i_region_id': 'i',
                'j_region_id': 'j',
                'distance_km': 'dist',
                'driving_time_hours': 'driving_time',
            }
        ),
        show_data_types=False,
        selection=None,
        show_column_summaries=False,
        page_size=8
    )

    stopsCostSlide.content2 = mo.vstack(
        [
            mo.md(
                r"""
    To get from **distance** to **driving time**, we proceed in two steps:
    - For each pair of regions \((i, j)\), we compute the one-way distance between their centers using the haversine formula.
    - We assume an average driving speed of 70 km/h to get the one-way driving time; the round trip (2×) is factored into the time-in-region calculation.
    """
            ),
            transportation_costs_table,
        ]
    )

    stopsCostSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    modelParamsSlide = sc.create_slide(
        'Sets and parameters of the Warehouse Location Problem',
        layout_type='1-column',
        page_number=9
    )

    modelParamsSlide.content1 = mo.md(
        r"""
    Now that we have defined demand, fixed warehouse costs and transport costs,
    we can summarize the building blocks of our Warehouse Location Problem.

    **Sets:**

    - \(I\): set of regions in Spain (each region aggregates pharmacies and their demand).
    - \(J\): set of possible warehouse locations (here we take \(J = I\): every region can host a warehouse).

    **Parameters:**

    - \(d_i\): annual demand in region \(i \in I\) (number of pharmacy visits / deliveries per year).

    - \(f_j\): annual fixed cost of operating a warehouse in location \(j \in J\) (rent, staff, energy, overhead).  

    - \(c_{ij}\): annual transport cost if region \(i \in I\) is served from a warehouse in location \(j \in J\).  

    These sets and parameters describe the **world as it is**:
    where demand appears and how costly it is to operate warehouses and ship goods.
    On top of this, we will now define **decision variables** that describe
    the network Phoenix can choose.
    """
    )

    modelParamsSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    decisionVarsSlide = sc.create_slide(
        'Decision variables: what Phoenix can choose',
        layout_type='1-column',
        page_number=10
    )

    decisionVarsSlide.content1 = mo.md(
        r"""
    So far, our sets and parameters describe the world as it is.
    Now we define the decision variables that describe the network
    Phoenix can choose.

    **Decision variables:**
    - \(y_j \in \{0,1\}\) for each \(j \in J\):

      - \(y_j = 1\) if Phoenix opens a warehouse in location \(j\),  
      - \(y_j = 0\) if there is no warehouse in location \(j\).

    - \(x_{ij} \in \{0,1\}\) for each \(i \in I, j \in J\):

      - \(x_{ij} = 1\) if region \(i\) is assigned to (served from) warehouse \(j\),  
      - \(x_{ij} = 0\) otherwise.

    You can read these variables in business language:
    - If \(y_{\text{Madrid}} = 1\), Phoenix opens a warehouse in Madrid.
    - If \(x_{\text{Sevilla},\,\text{Madrid}} = 1\), the demand of Sevilla
      is served from the warehouse in Madrid.

    The optimization model will choose values for \(x_{ij}\) and \(y_j\)
    to decide which warehouses to open and how each region is assigned.
    """
    )

    decisionVarsSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    objectiveSlide = sc.create_slide(
        'Objective: total annual cost of the network',
        layout_type='1-column',
        page_number=11
    )

    objectiveSlide.content1 = mo.md(
        r"""
    With sets, parameters and decision variables in place,
    we can now define the goal of the Warehouse Location Problem.

    Phoenix wants to design a network that:
    - serves all regions, and  
    - minimizes the total annual cost.

    We can formalize this objective as:

    \[
    \min \quad \underbrace{\sum_{j \in J} f_j \, y_j}_{\text{fixed warehouse costs}} \;+\; \underbrace{\sum_{i \in I} \sum_{j \in J} c_{ij} \, x_{ij}}_{\text{transport costs}}.
    \]

    You can read this as:
    - The first term adds up the annual fixed cost \(f_j\) for every location \(j\)
      where we actually open a warehouse (\(y_j = 1\)).
    - The second term adds up the annual transport cost \(c_{ij}\) for every
      region–warehouse pair \((i,j)\) that we use (\(x_{ij} = 1\)).

    This objective captures the central trade-off:

    - Fewer warehouses → lower fixed cost, but higher transport cost  
    - More warehouses → higher fixed cost, but shorter distances and lower transport cost
    """
    )

    objectiveSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    constraintsSlide = sc.create_slide(
        'Constraints: a consistent warehouse network',
        layout_type='1-column',
        page_number=12
    )

    constraintsSlide.content1 = mo.md(
        r"""
    The objective tells us what Phoenix wants to optimize.
    The constraints describe what a valid network must satisfy.

    We use two core constraints:
    - Each region is served by exactly one warehouse

        $\sum_{j \in J} x_{ij} = 1 \quad \forall i \in I.$

        Interpretation:
        - Each region must be assigned to one warehouse.
        - No region can be forgotten.
        - In this simple model, we do not split a region across multiple warehouses.

    - You can only assign regions to open warehouses

        $x_{ij} \le y_j \quad \forall i \in I, \forall j \in J$.

        Interpretation:
        - If \(y_j = 0\), the right-hand side is 0, so all \(x_{ij}\) with that \(j\) must be 0.
        - A location without a warehouse cannot serve any region.
        - Only locations with \(y_j = 1\) are allowed to supply regions.

    Together with the objective, these constraints define the basic
    warehouse location model we will use for Phoenix Spain.
    """
    )

    constraintsSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    completeModelSlide = sc.create_slide(
        'The complete Warehouse Location Problem for Phoenix Spain',
        layout_type='side-by-side',
        page_number=13
    )

    completeModelSlide.content1 = mo.md(
        r"""
    We now collect all pieces of the Phoenix Spain model.

    **Sets**
    - $I$: regions in Spain  
    - $J$: possible warehouse locations (here $J = I$)

    **Parameters**
    - \(d_i\): annual demand in region \(i \in I\)  
      (number of pharmacy visits per year)  
    - \(f_j\): annual fixed cost of a warehouse in location \(j \in J\)  
    - \(c_{ij}\): annual transport cost if region \(i\) is served from \(j \in J\)

    These sets and parameters describe where demand appears
    and how costly it is to operate warehouses and ship goods.
    """
    )

    completeModelSlide.content2 = mo.md(
        r"""
    **Decision variables**
    - \(y_j \in \{0,1\}\): 1 if a warehouse is opened in \(j\), 0 otherwise  
    - \(x_{ij} \in \{0,1\}\): 1 if region \(i\) is served from warehouse \(j\), 0 otherwise  

    **Objective**

    $\min \quad \sum_{j \in J} f_j \, y_j \;+\;\sum_{i \in I} \sum_{j \in J} c_{ij} \, x_{ij}$

    **Constraints**

    - Each region is assigned to exactly one warehouse:

        $\sum_{j \in J} x_{ij} = 1 \quad \forall i \in I$

    - Regions can only be assigned to open warehouses:

        $x_{ij} \le y_j \quad \forall i \in I,\; j \in J$

    - Binary decisions:

        $x_{ij} \in \{0,1\}, \quad y_j \in \{0,1\}$

    This is the model we will solve in the next session
    to design Phoenix’s distribution network for Spain.
    """
    )

    completeModelSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    recapSlide = sc.create_slide(
        'Recap and what comes next',
        layout_type='1-column',
        page_number=14
    )

    recapSlide.content1 = mo.md(
    r"""
    In this session, we

    - started from Phoenix’s question:
      which warehouses should we open and which regions should they serve?
    - identified the data needed for this decision:
      regional demand, fixed warehouse costs, and transport costs.
    - built a simple but realistic way to estimate:
      - annual demand \(d_i\) in each region,
      - fixed costs \(f_j\) for possible warehouse locations,
      - transport costs \(c_{ij}\) between regions and warehouses.
    - translated the business story into a warehouse location model with
      decision variables \(x_{ij}\) and \(y_j\),
      a total cost objective, and a small set of constraints.

    In the next session, we will

    - solve this model for Phoenix using an optimization solver,
    - see which warehouses open and how regions are assigned,
    - compare different scenarios by changing cost assumptions,
    - and look at simple extensions of the model.
    """
    )

    recapSlide.render()
    return


if __name__ == "__main__":
    app.run()
