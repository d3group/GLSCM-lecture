import marimo

__generated_with = "0.18.1"
app = marimo.App(
    width="medium",
    app_title="Center of Gravity",
    layout_file="layouts/center_of_gravity.slides.json",
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
            BASE = "apps/public/cog/data"
            IMG_BASE = "apps/public/cog/images"
        else:
            # WASM/deployed mode - use GitHub raw URLs for data files
            BASE = raw_url("apps", "public", "cog", "data")
            IMG_BASE = "public/cog/images"  # Images work with relative paths

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
    import requests
    import folium
    from typing import Optional
    import warnings
    warnings.filterwarnings("ignore", message=".*narwhals.*is_pandas_dataframe.*")
    return alt, folium, mo, np, pl, requests


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
        subtitle="Center of Gravity for Warehouse Location"
    )
    sc.styles()
    titleSlide.render()
    return


@app.cell
def _(DataURLs, mo, sc):
    phoenixRecapSlide = sc.create_slide(
        'Remember Phoenix – our case company',
        layout_type='side-by-side',
        page_number=2
    )

    phoenixRecapSlide.content1 = mo.md(
        """
        **Who is Phoenix?**

        - A **pharmaceutical wholesaler**: Phoenix buys drugs from manufacturers (e.g. Sandoz, Teva) and supplies **pharmacies**
        - Headquarters in **Mannheim**, leading pharmaceutical wholesaler in Germany

        **Some basic data**

        - **Germany:** ~5,000 employees, ~20 distribution centers (DCs), supplies ~12,000 pharmacies
        - **Worldwide:** 29 European countries, >200 DCs, revenue €47.1bn (FY 2023/24)

        **Why do we care?**

        - Phoenix is one echelon of the amoxicillin chain from Chapter I – and a serious operations problem in its own right
        """
    )

    phoenixRecapSlide.content2 = mo.image(f'{DataURLs.IMG_BASE}/phoenix_supply_chain.png')

    phoenixRecapSlide.render()
    return


@app.cell
def _(DataURLs, mo, sc):
    planningTasksSlide = sc.create_slide(
        "Phoenix's planning tasks – we now focus on Distribution Network Design",
        layout_type='1-column',
        page_number=3
    )

    planningTasksSlide.content1 = mo.vstack([
        mo.md(
            """
            In Chapter I we derived the planning tasks of Phoenix. **Distribution Network Design (DND)** is the
            **long-term task** at the top of the planning matrix: it sets the frame in which all other tasks operate.
            """
        ),
        mo.image(f'{DataURLs.IMG_BASE}/phoenix_planning_tasks_dnd.png', width=1150),
    ], gap=1)

    planningTasksSlide.render()
    return


@app.cell
def _(DataURLs, mo, sc):
    dndTasksSlide = sc.create_slide(
        'Distribution Network Design – tasks and objectives',
        layout_type='side-by-side',
        page_number=4
    )

    dndTasksSlide.content1 = mo.md(
        """
        - In Germany, Phoenix has **one DC per sales region** (~20 DCs) that serves the pharmacies in this region

        - **Core task of DND:** determine **how many** DCs a company should have in a country (or larger region),
          **where** they are located, and **which DC** fulfills the orders of the customers in a particular region

        - DND is a **strategic task**: it determines the distribution system for a rather long period of time (**3–10 years**)

        - **Objective:** fulfill the customers' requirements (availability, delivery times) at **minimum costs**:
          - **fixed costs** of the DCs (rent, personnel, infrastructure, utilities)
          - **costs of fulfilling the customers' orders** (costs of the last mile)
        """
    )

    dndTasksSlide.content2 = mo.vstack([
        mo.image(f'{DataURLs.IMG_BASE}/phoenix_germany_dcs.png', height=500),
        mo.md("*Phoenix's DCs in Germany*"),
    ], align="center", gap=0.5)

    dndTasksSlide.render()
    return


@app.cell
def _(mo, sc):
    redesignSlide = sc.create_slide(
        'Why do companies have to re-design their distribution network?',
        layout_type='1-column',
        page_number=5
    )

    redesignSlide.content1 = mo.md(
        """
        **Typical reasons:**

        - **Demand changes** (e.g. long positive or negative demand trend, shifts in the regional distribution of demand)
        - Changes in the **product portfolio**
        - **Expansion into new markets**
        - **Mergers and acquisitions**
        - **Political and regulatory changes** (e.g. Brexit)

        Oftentimes, the design of the distribution network "evolved" over time and companies wish to reconsider
        whether their current setup is still optimal.

        **Our case:** Phoenix wants to **expand into a new market – Spain**. Where should its warehouses be located?
        """
    )

    redesignSlide.render()
    return


@app.cell(hide_code=True)
def _(DataURLs, mo, sc):
    phoenixSpainSlide = sc.create_slide(
        'Phoenix in Spain',
        layout_type='side-by-side',
        page_number=6
    )

    phoenixSpainSlide.content1 = mo.md(
        """
        - Phoenix already runs **warehouse networks in many European countries**.

        - Now the company plans to **enter the Spanish market**:
          - Pharmacies are spread across many regions and cities.
          - Spain is geographically large and heterogeneous.

        - **Key strategic question:** Where should we locate warehouse(s) in Spain to serve pharmacies efficiently?

        - This is a **strategic, long-term decision**:
          - Once you build a warehouse, it is expensive to move it.
          - Location choices affect **costs**, **service times**, and **reliability** for many years.


        - In this session we take a **first, simplified step**:
          - Aggregate Spain into **demand regions**.
          - Use the **Center of Gravity** idea to find good candidate locations.
        """
    )

    phoenixSpainSlide.content2 = mo.image(f'{DataURLs.IMG_BASE}/cog_spain_planner.png')

    phoenixSpainSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    decisionProblemSlide = sc.create_slide(
        'The underlying decision problem – warehouse location in Spain',
        layout_type='1-column',
        page_number=7
    )

    decisionProblemSlide.content1 = mo.md(
    """
    **Intuition**
    - Finding optimal warehouse locations is a well studied problem in operations management.
    - We must choose **where to locate warehouse(s)** so that all demand is served and long-term costs stay low.

    **What goes in (parameters)**
    - **Demand points:** locations in Spain where we have demand  
    - **Network / distances:** travel distance between warehouse locations and demand points.

    **What we decide (decisions)**
    - A **geographic location** for a warehouse.

    **What must be respected (constraints)**
    - **Coverage:** every demand point must be served by the network.

    **What we optimize (objective)**
    - Keep **average distance to demand** as small as possible.
    """
    )

    decisionProblemSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    demandPointsSlide = sc.create_slide(
        "From pharmacies to demand points",
        layout_type="1-column",
        page_number=8
    )

    demandPointsSlide.content1 = mo.md(
    """
    - In reality, demand comes from **individual pharmacies**.

    - For a **national warehouse location** decision, modelling
      every single pharmacy is not aligned with the operational realities as we:
      - visit individual pharmacies in tours
      - need clusters with sufficient demand to achieve full truckloads

    - Going forwards, our plan is the following:
      1. Start from **all pharmacies in Spain** (OpenStreetMap / Overpass).
      2. See their **raw spatial pattern** on a map.
      3. **Aggregate** pharmacies into larger **demand regions**.
      4. Use these regions as our **demand points** in the Center of Gravity model.
    """
    )

    demandPointsSlide.render()
    return


@app.cell
def _(pl, requests):
    # Public Overpass servers - if one is busy, we try the next one
    OVERPASS_URLS = [
        "https://overpass-api.de/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    ]

    def get_pharmacies(country_code: str = "ES", around: tuple | None = None, timeout: int = 180) -> pl.DataFrame:
        """
        Fetch all pharmacies with postal codes from Overpass API.

        Args:
            country_code: ISO 3166-1 alpha-2 country code (e.g., 'ES' for Spain)
            around: optional (lat, lon, radius_km) to search only around one point
            timeout: Query timeout in seconds
        """
        if around is None:
            # All pharmacies in the specified country
            area = f'area["ISO3166-1"="{country_code}"][admin_level=2];'
            where = "(area)"
        else:
            # All pharmacies within radius_km of (lat, lon)
            lat, lon, radius_km = around
            area = ""
            where = f"(around:{int(radius_km * 1000)},{lat},{lon})"

        query = f"""
        [out:json][timeout:{timeout}];
        {area}
        (
          node["amenity"="pharmacy"]{where};
          way["amenity"="pharmacy"]{where};
          relation["amenity"="pharmacy"]{where};
        );
        out center tags;
        """

        # Overpass rejects the default python-requests user agent; browsers send their own
        import sys
        headers = {} if sys.platform == "emscripten" else {"User-Agent": "GLSCM-lecture (JMU Wuerzburg)"}

        # Query Overpass API
        data, last_err = None, None
        for url in OVERPASS_URLS:
            try:
                response = requests.get(url, params={"data": query}, headers=headers, timeout=timeout)
                response.raise_for_status()
                data = response.json()
                break
            except Exception as e:
                last_err = e
        if data is None:
            raise requests.RequestException(f"All Overpass servers failed. Last error: {last_err}")

        # Extract pharmacy data
        rows = []
        for el in data["elements"]:
            # Get coordinates
            if el["type"] == "node":
                lat, lon = el["lat"], el["lon"]
            elif "center" in el:
                lat, lon = el["center"]["lat"], el["center"]["lon"]
            else:
                continue

            # Get postal code (skip if not available)
            tags = el.get("tags", {})
            postal_code = tags.get("addr:postcode") or tags.get("postal_code")
            if not postal_code:
                continue

            rows.append({
                "id": el["id"],
                "name": tags.get("name", f"Pharmacy {el['id']}"),
                "lat": lat,
                "lon": lon,
                "postal_code": str(postal_code).zfill(5),
            })

        df = pl.DataFrame(
            rows,
            schema={"id": pl.Int64, "name": pl.Utf8, "lat": pl.Float64, "lon": pl.Float64, "postal_code": pl.Utf8},
        )

        # Filter for mainland Spain only (exclude islands and North Africa)
        # Remove: Balearic Islands (07), Canary Islands (35, 38), Ceuta (51), Melilla (52)
        return df.filter(
            ~pl.col("postal_code").str.slice(0, 2).is_in(["07", "35", "38", "51", "52"])
        )
    return (get_pharmacies,)


@app.cell
def _(folium, np, pl):
    def plot_pharmacies_map(df: pl.DataFrame, center: tuple | None = None, radius_km: float | None = None, loading: str | None = None):
        """
        Plot pharmacies as dots on an interactive folium map.

        Args:
            df: DataFrame with 'lat' and 'lon' columns (may be empty)
            center: optional (lat, lon) of a search area; without it the map shows mainland Spain
            radius_km: radius of the search area around center
            loading: optional message shown as a loading overlay on top of the map
        """
        m = folium.Map(location=[40.2, -3.7], zoom_start=5, tiles="OpenStreetMap", prefer_canvas=True)

        if center is None:
            # Zoom to mainland Spain
            m.fit_bounds([[36.0, -9.3], [43.8, 3.3]])
        else:
            # Draw the search area and zoom so that it is fully visible (1° latitude ≈ 111 km)
            folium.Circle(location=list(center), radius=radius_km * 1000, color="gray", weight=1, fill=False).add_to(m)
            dlat = radius_km / 111
            dlon = radius_km / (111 * np.cos(np.radians(center[0])))
            m.fit_bounds([[center[0] - dlat, center[1] - dlon], [center[0] + dlat, center[1] + dlon]])

        # Add all pharmacies as small circles in one GeoJSON layer (much faster than one marker each).
        # No tooltips/popups: their folium JavaScript breaks when marimo embeds the map.
        if df.height > 0:
            points = {"type": "FeatureCollection", "features": [
                {"type": "Feature", "geometry": {"type": "Point", "coordinates": [row["lon"], row["lat"]]}, "properties": {}}
                for row in df.iter_rows(named=True)
            ]}
            folium.GeoJson(
                points,
                marker=folium.CircleMarker(radius=2 if center is None else 3, color="blue", fill=True, fill_color="blue", fill_opacity=0.6),
            ).add_to(m)

        if loading:
            # Semi-transparent overlay with a spinner, only on the map
            m.get_root().html.add_child(folium.Element(f"""
                <style>@keyframes map-spin {{ to {{ transform: rotate(360deg); }} }}</style>
                <div style="position:absolute; inset:0; z-index:1000; background:rgba(255,255,255,0.6);
                            display:flex; flex-direction:column; align-items:center; justify-content:center;
                            font-family:sans-serif; font-size:16px; color:#374151;">
                  <div style="width:36px; height:36px; border:4px solid #d1d5db; border-top-color:#2563eb;
                              border-radius:50%; animation:map-spin 1s linear infinite; margin-bottom:10px;"></div>
                  {loading}
                </div>
            """))

        return m

    def pharmacies_within(df: pl.DataFrame, center: tuple, radius_km: float) -> pl.DataFrame:
        """Keep only pharmacies within radius_km of center (lat, lon), using the haversine distance."""
        lat0, lon0 = np.radians(center[0]), np.radians(center[1])
        lat, lon = np.radians(df["lat"].to_numpy()), np.radians(df["lon"].to_numpy())
        a = np.sin((lat - lat0) / 2) ** 2 + np.cos(lat0) * np.cos(lat) * np.sin((lon - lon0) / 2) ** 2
        distance_km = 2 * 6371 * np.arcsin(np.sqrt(a))
        return df.filter(pl.Series(distance_km <= radius_km))
    return pharmacies_within, plot_pharmacies_map


@app.cell(hide_code=True)
def _(DataURLs, pl):
    pharmacies_raw = pl.read_csv(
        f'{DataURLs.BASE}/pharmacies_spain.csv',
        schema_overrides={"postal_code": pl.Utf8}
    )
    return (pharmacies_raw,)


@app.cell(hide_code=True)
def _(mo):
    # Cities for the live Overpass query on the raw-data slide (lat, lon)
    CITIES = {
        "Madrid": (40.4168, -3.7038),
        "Barcelona": (41.3874, 2.1686),
        "Valencia": (39.4699, -0.3763),
        "Sevilla": (37.3891, -5.9845),
        "Zaragoza": (41.6488, -0.8891),
        "Bilbao": (43.2630, -2.9350),
    }
    city_selector = mo.ui.dropdown(options=list(CITIES), value="Madrid", label="City")
    radius_selector = mo.ui.slider(start=1, stop=10, step=1, value=3, label="Radius (km)", show_value=True)
    city_button = mo.ui.run_button(label="Query city (live)")
    spain_button = mo.ui.run_button(label="All of Spain (saved)")

    # What the map on the raw-data slide shows: empty, loading, city, failed or spain
    get_map_view, set_map_view = mo.state({"mode": "empty"})
    return (
        CITIES,
        city_button,
        city_selector,
        get_map_view,
        radius_selector,
        set_map_view,
        spain_button,
    )


@app.cell(hide_code=True)
def _(
    CITIES,
    city_button,
    city_selector,
    get_pharmacies,
    mo,
    pharmacies_raw,
    pharmacies_within,
    radius_selector,
    set_map_view,
    spain_button,
):
    import sys

    def run_city_query(city: str, center: tuple, radius_km: float):
        """Query Overpass for one city and put the result on the map (saved data if Overpass fails)."""
        view = {"city": city, "center": center, "radius_km": radius_km}
        try:
            set_map_view({**view, "mode": "city", "df": get_pharmacies(around=(*center, radius_km), timeout=30)})
        except Exception:
            set_map_view({**view, "mode": "failed", "df": pharmacies_within(pharmacies_raw, center, radius_km)})

    if spain_button.value:
        set_map_view({"mode": "spain"})

    if city_button.value:
        _city = city_selector.value
        set_map_view({"mode": "loading", "city": _city, "center": CITIES[_city], "radius_km": radius_selector.value})
        if sys.platform == "emscripten":
            # The browser version has no threads: query directly
            run_city_query(_city, CITIES[_city], radius_selector.value)
        else:
            # Query in the background, so only the map shows the loading state
            mo.Thread(target=run_city_query, args=(_city, CITIES[_city], radius_selector.value)).start()
    return


@app.cell(hide_code=True)
def _(
    city_button,
    city_selector,
    get_map_view,
    mo,
    pharmacies_raw,
    plot_pharmacies_map,
    radius_selector,
    sc,
    spain_button,
):
    rawPharmaciesSlide = sc.create_slide(
        'Pharmacies in Spain – raw data',
        layout_type='side-by-side',
        page_number=9
    )

    rawPharmaciesSlide.content1 = mo.md(
    f"""
    **Idea**:
    - To place warehouses, we first need to know **where demand is**: the pharmacies Phoenix supplies
    - Without Phoenix's customer list, we can use **open data**: all pharmacies in OpenStreetMap

    **Solution**:
    - Location data is available via APIs, e.g. Google Places (commercial) or the **Overpass API** (OpenStreetMap, free)
    - `get_pharmacies("ES")` queries all objects tagged `amenity=pharmacy` in **Spain** (see the [documentation](https://wiki.openstreetmap.org/wiki/Key:amenity) for a full list of available categories)
    - We keep pharmacies with a postal code (needed for aggregation later) on the mainland → **{pharmacies_raw.height:,} pharmacies**
    - As querying all of Spain takes a while, we load a saved result
    """
    )

    _view = get_map_view()
    _mode = _view["mode"]
    _empty = pharmacies_raw.clear()

    if _mode == "spain":
        _map = plot_pharmacies_map(pharmacies_raw)
        _caption = f"Saved data: **{pharmacies_raw.height:,}** pharmacies in mainland Spain"
    elif _mode == "loading":
        _map = plot_pharmacies_map(_empty, _view["center"], _view["radius_km"], loading=f"Querying OpenStreetMap for {_view['city']} …")
        _caption = f"Live query: pharmacies within {_view['radius_km']} km of {_view['city']}"
    elif _mode == "city":
        _map = plot_pharmacies_map(_view["df"], _view["center"], _view["radius_km"])
        _caption = f"Live query: **{_view['df'].height}** pharmacies within {_view['radius_km']} km of {_view['city']}"
    elif _mode == "failed":
        _map = plot_pharmacies_map(_view["df"], _view["center"], _view["radius_km"])
        _caption = f"Overpass did not respond · saved data: **{_view['df'].height}** pharmacies within {_view['radius_km']} km"
    else:
        _map = plot_pharmacies_map(_empty)
        _caption = "Query one city live or show the saved data for all of Spain"

    rawPharmaciesSlide.content2 = mo.vstack([
        mo.hstack([city_selector, radius_selector], justify="start", align="center", gap=1),
        mo.hstack([city_button, spain_button], justify="start", gap=0.5),
        _map,
        mo.md(_caption),
    ], gap=0.5)

    rawPharmaciesSlide.render()
    return


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
def _(folium, np, pl):
    def plot_demand_regions_map(df: pl.DataFrame, zoom_start: int = 5):
        """
        Plot aggregated demand regions on a folium map with circle size proportional to demand.

        Args:
            df: DataFrame with 'region_id', 'lat', 'lon', 'demand' columns
            zoom_start: Initial zoom level for the map
        """
        # Calculate center
        center_lat = df["lat"].median()
        center_lon = df["lon"].median()

        # Create base map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom_start,
            tiles="OpenStreetMap"
        )

        # Add each region as a circle with size proportional to demand
        for row in df.iter_rows(named=True):
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=np.log(1+row["demand"]/5),  # Scale radius based on demand
                color="blue",
                fill=True,
                fillColor="blue",
                fillOpacity=1,
                popup=f"Region: {row['region_id']}<br>Demand: {row['demand']}"
            ).add_to(m)

        return m
    return (plot_demand_regions_map,)


@app.cell(hide_code=True)
def _(aggregate_by_zipcode, mo, pharmacies_raw, plot_demand_regions_map, sc):
    demandRegionsSlide = sc.create_slide(
        'From pharmacies to demand regions',
        layout_type='side-by-side',
        page_number=10
    )

    demandRegionsSlide.content1 = mo.md(
    """
    - For **warehouse location**, modelling every pharmacy is:
      - too detailed and
      - not aligned with **truckload / regional** planning.

    - We therefore **group pharmacies** into larger **demand regions**:
      - In this example, we group pharmacies by the first 2 digits of the postal code (province code).
    Each province becomes one demand region.
      - Alternatively, we could also cluster by **city** or apply more advanced clustering algorithms such as k-means.

    - For each demand region we compute:
      - a **representative location** (centroid),
      - an **annual demand** value (number of pharmacies or volume).

    On the right you see the **aggregated map**: each symbol represents one **demand region** with its total demand.

    """
    )

    pharmacies_aggregated = aggregate_by_zipcode(pharmacies_raw)
    _pharmacies_aggregated_map = plot_demand_regions_map(pharmacies_aggregated)

    demandRegionsSlide.content2 = mo.vstack([
        _pharmacies_aggregated_map
    ])

    demandRegionsSlide.render()
    return (pharmacies_aggregated,)


@app.cell(hide_code=True)
def _(mo, pharmacies_aggregated, sc):
    demandPointsSpainSlide = sc.create_slide(
        "Demand points for Spain",
        layout_type="side-by-side",
        page_number=11
    )

    demandPointsSpainSlide.content1 = mo.md(
    """
    - After aggregation, each **demand region** is now a single  
      **demand point** in our model.

    - For every demand point we store:
      - a **Region ID / name**,
      - a **location** (representative coordinates),
      - a **demand** value  (here: the number of pharmacies in the region).

    - The table on the right shows our **final demand dataset for Spain**.

    This is the data we will use to find the location for the new warehouse.
    """
    )

    _pharmacies_aggregated_table = mo.ui.table(
        pharmacies_aggregated,
        show_data_types=False,
        selection=None,
        show_column_summaries=False
    )


    demandPointsSpainSlide.content2 = mo.vstack([_pharmacies_aggregated_table])

    demandPointsSpainSlide.render()
    return


@app.cell(hide_code=True)
def _(alt, pl):
    def create_cog_example_data():
        """Create 5 example demand points for CoG demonstration."""
        return pl.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'x': [10, 50, 20, 90, 80],
            'y': [20, 20, 80, 90, 5],
            'demand': [50, 200, 300, 80, 400]
        })

    def create_interactive_cog_chart():
        """
        Create an interactive chart where points can be clicked to select/unselect.
        The CoG is calculated and displayed dynamically based on selection.
        """
        points = create_cog_example_data().to_pandas()

        # Create click selection (multi-select with toggle, start empty)
        # toggle='true' (string) makes every click toggle without needing shift key
        # empty=False means no points are selected initially
        click = alt.selection_point(fields=['id'], toggle='true', clear=False, empty=False)

        # Demand points
        points_chart = alt.Chart(points).mark_circle().encode(
            x=alt.X('x:Q', scale=alt.Scale(domain=[0, 100]), title='X Coordinate'),
            y=alt.Y('y:Q', scale=alt.Scale(domain=[0, 100]), title='Y Coordinate'),
            size=alt.Size('demand:Q', scale=alt.Scale(range=[200, 1000]), legend=None),
            color=alt.condition(
                click,
                alt.value('steelblue'),
                alt.value('lightgray')
            ),
            opacity=alt.condition(
                click,
                alt.value(0.8),
                alt.value(0.3)
            ),
            tooltip=[
                alt.Tooltip('id:O', title='Point ID'),
                alt.Tooltip('x:Q', title='X'),
                alt.Tooltip('y:Q', title='Y'),
                alt.Tooltip('demand:Q', title='Demand')
            ]
        ).add_params(click)

        # Point labels
        labels = alt.Chart(points).mark_text(dy=-15, fontSize=12, fontWeight='bold').encode(
            x='x:Q',
            y='y:Q',
            text='id:O',
            color=alt.condition(
                click,
                alt.value('black'),
                alt.value('gray')
            )
        ).add_params(click)

        # Calculate CoG from selected points using Altair transforms
        cog_chart = alt.Chart(points).transform_filter(
            click
        ).transform_calculate(
            xq='datum.x * datum.demand',
            yq='datum.y * datum.demand'
        ).transform_aggregate(
            sum_xq='sum(xq)',
            sum_yq='sum(yq)',
            sum_q='sum(demand)',
            groupby=[]
        ).transform_calculate(
            cog_x='datum.sum_xq / datum.sum_q',
            cog_y='datum.sum_yq / datum.sum_q'
        ).mark_point(
            shape='cross',
            size=500,
            color='red',
            strokeWidth=4
        ).encode(
            x='cog_x:Q',
            y='cog_y:Q',
            tooltip=[
                alt.Tooltip('cog_x:Q', title='CoG X', format='.1f'),
                alt.Tooltip('cog_y:Q', title='CoG Y', format='.1f')
            ]
        )

        # CoG label
        cog_label = alt.Chart(points).transform_filter(
            click
        ).transform_calculate(
            xq='datum.x * datum.demand',
            yq='datum.y * datum.demand'
        ).transform_aggregate(
            sum_xq='sum(xq)',
            sum_yq='sum(yq)',
            sum_q='sum(demand)',
            groupby=[]
        ).transform_calculate(
            cog_x='datum.sum_xq / datum.sum_q',
            cog_y='datum.sum_yq / datum.sum_q'
        ).mark_text(
            dy=-15,
            fontSize=14,
            fontWeight='bold',
            color='red'
        ).encode(
            x='cog_x:Q',
            y='cog_y:Q'
        )

        # Lines from CoG to selected points
        lines_base = alt.Chart(points).transform_filter(
            click
        ).transform_calculate(
            xq='datum.x * datum.demand',
            yq='datum.y * datum.demand'
        ).transform_joinaggregate(
            sum_xq='sum(xq)',
            sum_yq='sum(yq)',
            sum_q='sum(demand)'
        ).transform_calculate(
            cog_x='datum.sum_xq / datum.sum_q',
            cog_y='datum.sum_yq / datum.sum_q'
        )

        # Draw lines
        lines = lines_base.mark_line(
            color='red',
            strokeWidth=2,
            opacity=0.4,
            strokeDash=[5, 5]
        ).encode(
            x='x:Q',
            y='y:Q',
            x2='cog_x:Q',
            y2='cog_y:Q'
        )

        # Demand labels on lines (at midpoint)
        line_labels = lines_base.transform_calculate(
            mid_x='(datum.x + datum.cog_x) / 2',
            mid_y='(datum.y + datum.cog_y) / 2'
        ).mark_text(
            fontSize=11,
            fontWeight='bold',
            color='red',
            dx=0,
            dy=-5
        ).encode(
            x='mid_x:Q',
            y='mid_y:Q',
            text=alt.Text('demand:Q', format='d')
        )

        return (points_chart + labels + lines + line_labels + cog_chart + cog_label).properties(
            width=500,
            height=500,
            title='Click points to select/unselect for CoG calculation'
        )
    return (create_interactive_cog_chart,)


@app.cell
def _(pl):
    def calculate_cog(df: pl.DataFrame, x_col: str = 'x', y_col: str = 'y', demand_col: str = 'demand'):
        """
        Calculate the Center of Gravity from demand points.

        Args:
            df: DataFrame with coordinate and demand columns
            x_col: Name of the x-coordinate column (default: 'x')
            y_col: Name of the y-coordinate column (default: 'y')
            demand_col: Name of the demand/weight column (default: 'demand')

        Returns:
            Tuple of (cog_x, cog_y) or (None, None) if no data
        """
        if len(df) == 0:
            return None, None

        # Calculate weighted coordinates
        sum_xq = (df[x_col] * df[demand_col]).sum()
        sum_yq = (df[y_col] * df[demand_col]).sum()
        sum_q = df[demand_col].sum()

        # Center of Gravity formula
        cog_x = sum_xq / sum_q
        cog_y = sum_yq / sum_q

        return cog_x, cog_y
    return (calculate_cog,)


@app.cell(hide_code=True)
def _(create_interactive_cog_chart, mo, sc):
    cogFormulaSlide = sc.create_slide(
        "Center of Gravity – idea and formula",
        layout_type="side-by-side",
        page_number=12
    )

    cogFormulaSlide.content1 = mo.md(
    r"""
    We now have a set of **demand points**:

    - indexed by \(i = 1, \dots, n\),
    - each with coordinates \((x_i, y_i)\),
    - and a demand (weight) \(q_i\).

    For a **single warehouse**, the Center of Gravity (CoG) suggests the location

    \[
    X^* = \frac{\sum_i x_i q_i}{\sum_i q_i},
    \quad
    Y^* = \frac{\sum_i y_i q_i}{\sum_i q_i}.
    \]

    **Intuition**
    - The CoG is a **weighted average** of all demand locations.
    - Demand points with larger \(q_i\) **pull** the warehouse closer.
    - This gives us a *geometric* "best compromise" location,
      ignoring detailed road network and fixed costs.

    In the code cells, you can use our helper function
    `calculate_cog(...)` to compute \((X^*, Y^*)\) for any set of
    demand points.
    """
    )

    _cog_example_plot = create_interactive_cog_chart()

    cogFormulaSlide.content2 = mo.vstack([_cog_example_plot])

    cogFormulaSlide.render()
    return


@app.cell(hide_code=True)
def _(folium, np, pl):
    def plot_demand_regions_with_cog(df: pl.DataFrame, cog_lat: float, cog_lon: float, zoom_start: int = 5):
        """
        Plot aggregated demand regions and Center of Gravity on a folium map.

        Args:
            df: DataFrame with 'region_id', 'lat', 'lon', 'demand' columns
            cog_lat: Latitude of the Center of Gravity
            cog_lon: Longitude of the Center of Gravity
            zoom_start: Initial zoom level for the map
        """
        # Calculate center for map
        center_lat = df["lat"].median()
        center_lon = df["lon"].median()

        # Create base map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom_start,
            tiles="OpenStreetMap"
        )

        # Add each region as a circle with size proportional to demand
        for row in df.iter_rows(named=True):
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=np.log(1+row["demand"]/5),
                color="blue",
                fill=True,
                fillColor="blue",
                fillOpacity=1,
                popup=f"Region: {row['region_id']}<br>Demand: {row['demand']}"
            ).add_to(m)

        # Add Center of Gravity marker
        folium.Marker(
            location=[cog_lat, cog_lon],
            popup=f"Center of Gravity<br>Lat: {cog_lat:.2f}<br>Lon: {cog_lon:.2f}",
            icon=folium.Icon(color='red', icon='star', prefix='fa'),
            tooltip="Center of Gravity"
        ).add_to(m)

        return m
    return (plot_demand_regions_with_cog,)


@app.cell(hide_code=True)
def _(
    calculate_cog,
    mo,
    pharmacies_aggregated,
    plot_demand_regions_with_cog,
    sc,
):
    cogSpainSlide = sc.create_slide(
        "Center of Gravity for Spain",
        layout_type="side-by-side",
        page_number=13
    )

    cogSpainSlide.content1 = mo.md(
    r"""
    - We now apply the Center of Gravity idea to our **real demand data**:

      - all **province-level demand points**,

      - each with coordinates \((x_i, y_i)\) and demand \(q_i\).

    - Using our helper function `calculate_cog(...)`, we compute the CoG
      location \((X^*, Y^*)\) for **all of Spain**.

    - On the right:

      - blue circles = **demand points** (size reflects demand),

      - the red marker = **Center of Gravity** for the Spanish market.

    **Interpretation**

    - The CoG sits in a position that balances the **overall demand distribution**:
      large demand regions pull it closer, while more remote, smaller regions
      have less influence.

    This gives us a **first candidate location** for a national warehouse in Spain,
    purely from a **geometric** perspective.
    """
    )

    _cog_lon, _cog_lat = calculate_cog(pharmacies_aggregated, x_col='lon', y_col='lat')
    _cog_spain_plot = plot_demand_regions_with_cog(pharmacies_aggregated, _cog_lat, _cog_lon)

    cogSpainSlide.content2 = mo.vstack(
        [
            _cog_spain_plot
        ]
    )

    cogSpainSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    cogLimitations = sc.create_slide(
        "Is one warehouse enough for Spain?",
        layout_type="1-column",
        page_number=14
    )

    cogLimitations.content1 = mo.md(
    r"""
    - The CoG gives a **nice first candidate** location:
      - balances the **overall demand distribution**,
      - is simple to compute and explain.

    - But a **single warehouse for all of Spain** would likely mean:
      - very **long delivery distances** for many provinces,
      - problems meeting **service targets**,
      - high **risk concentration** in one site.

    - At the other extreme, we could imagine:
      - **one warehouse per province** → very short distances,
      - but we have not yet checked its **cost**.

    **Takeaway**
    - Phoenix will need **several warehouses**, somewhere **between** these extremes.
    - Next, we use the **Center of Gravity idea with multiple warehouses** to find a solution for the **one warehouse per province** case.
    """
    )


    cogLimitations.render()
    return


@app.cell(hide_code=True)
def _(DataURLs, mo, sc):
    multiCogFormalSlide = sc.create_slide(
        "Multiple warehouses – Center of Gravity per region",
        layout_type="side-by-side",
        page_number=15
    )

    multiCogFormalSlide.content1 = mo.md(
    r"""
    We now extend the CoG idea from **one** warehouse to **many**:

    - We split Spain into **regions** \(r = 1, \dots, m\)  
      (here: provinces, defined by the first two postal-code digits).

    - Each region \(r\) contains a set of **demand points** \(i \in R_r\)  
      with coordinates \((x_i, y_i)\) and demands \(q_i\).

    - For every region \(r\) we compute a **regional Center of Gravity**:

    \[
    X_r^* = \frac{\sum_{i \in R_r} x_i q_i}{\sum_{i \in R_r} q_i},
    \quad
    Y_r^* = \frac{\sum_{i \in R_r} y_i q_i}{\sum_{i \in R_r} q_i}.
    \]

    - The points \((X_r^*, Y_r^*)\) are our suggested locations if we want
      **one warehouse per region**.
    """
    )

    multiCogFormalSlide.content2 = mo.image(f'{DataURLs.IMG_BASE}/cog_multi_location_planner.png')

    multiCogFormalSlide.render()
    return


@app.cell(hide_code=True)
def _(aggregate_by_zipcode, folium, np, pharmacies_raw, pl):
    # Aggregate by full postal code (5 digits)
    pharmacies_by_zipcode = aggregate_by_zipcode(pharmacies_raw, digits=5)

    # Assign each 5-digit postal code to a province (first 2 digits)
    pharmacies_by_zipcode_with_region = pharmacies_by_zipcode.with_columns(
        pl.col("region_id").str.slice(0, 2).alias("province")
    )

    def plot_demand_points_by_region(
        df: pl.DataFrame,
        regional_cogs_df: pl.DataFrame = None,
        zoom_start: int = 5
    ):
        """
        Plot demand points on a folium map, colored by province.
        Optionally show regional Centers of Gravity.

        Args:
            df: DataFrame with 'region_id', 'lat', 'lon', 'demand', 'province' columns
            regional_cogs_df: Optional DataFrame with 'province', 'cog_lat', 'cog_lon' columns
            zoom_start: Initial zoom level for the map
        """
        # Calculate center
        center_lat = df["lat"].median()
        center_lon = df["lon"].median()

        # Create base map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom_start,
            tiles="OpenStreetMap"
        )

        # Map-friendly colors - bright, distinct, visible on light backgrounds
        map_colors = [
            '#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231',  # Red, Green, Yellow, Blue, Orange
            '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe',  # Purple, Cyan, Magenta, Lime, Pink
            '#008080', '#e6beff', '#9a6324', '#fffac8', '#800000',  # Teal, Lavender, Brown, Beige, Maroon
            '#aaffc3', '#808000', '#ffd8b1', '#000075', '#808080',  # Mint, Olive, Apricot, Navy, Grey
            '#ff6347', '#4169e1', '#32cd32', '#ff1493', '#00ced1',  # Tomato, RoyalBlue, LimeGreen, DeepPink, DarkTurquoise
            '#ff8c00', '#9370db', '#00fa9a', '#dc143c', '#00bfff',  # DarkOrange, MediumPurple, MediumSpringGreen, Crimson, DeepSkyBlue
            '#adff2f', '#ff69b4', '#1e90ff', '#ff4500', '#da70d6',  # GreenYellow, HotPink, DodgerBlue, OrangeRed, Orchid
            '#20b2aa', '#ff6347', '#7b68ee', '#00ff7f', '#ff1493',  # LightSeaGreen, Tomato, MediumSlateBlue, SpringGreen, DeepPink
            '#ffa500', '#9932cc', '#00ffff', '#ff0000', '#0000ff',  # Orange, DarkOrchid, Cyan, Red, Blue
            '#32cd32', '#ff00ff', '#008b8b', '#b8860b', '#a52a2a'   # LimeGreen, Magenta, DarkCyan, DarkGoldenrod, Brown
        ]

        # Get unique provinces and assign colors
        provinces = df["province"].unique().sort().to_list()
        province_colors = {prov: map_colors[i % len(map_colors)] for i, prov in enumerate(provinces)}

        # Add each demand point as a circle
        opacity = 0.5 if regional_cogs_df is not None else 0.7
        for row in df.iter_rows(named=True):
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=np.log(1 + row["demand"] / 5),
                color=province_colors[row["province"]],
                fill=True,
                fillColor=province_colors[row["province"]],
                fillOpacity=opacity,
                popup=f"Postal: {row['region_id']}<br>Province: {row['province']}<br>Demand: {row['demand']}"
            ).add_to(m)

        # Add regional CoG markers if provided
        if regional_cogs_df is not None:
            for row in regional_cogs_df.iter_rows(named=True):
                folium.Marker(
                    location=[row["cog_lat"], row["cog_lon"]],
                    popup=f"CoG Province {row['province']}<br>Total Demand: {row['total_demand']}",
                    icon=folium.Icon(color='red', icon='star', prefix='fa'),
                    tooltip=f"CoG: {row['province']}"
                ).add_to(m)

        return m
    return pharmacies_by_zipcode_with_region, plot_demand_points_by_region


@app.cell(hide_code=True)
def _(mo, pharmacies_by_zipcode_with_region, plot_demand_points_by_region, sc):
    intraRegionSlide = sc.create_slide(
        "Demand points inside each region",
        layout_type="side-by-side",
        page_number=16
    )

    intraRegionSlide.content1 = mo.md(
    r"""
    How do we get the **demand points** \(i \in R_r\) inside a region?

    - For each **province** \(r\) we start again from the **pharmacies**.

    - We then **aggregate pharmacies within the province** into smaller
      demand points, for example by:
      - grouping by the **full postal code**, or
      - clustering pharmacies that are very close to each other.
      - This is similar to what we did for all of Spain, but now **inside one province at a time**.

    - For each demand point \(i\) we compute:
      - a representative **location** \((x_i, y_i)\),
      - a **demand** \(q_i\) (number of pharmacies or volume).

    These intra-region demand points are the inputs for the
    **regional CoG** calculation in each province.
    """
    )

    _regions_plot = plot_demand_points_by_region(pharmacies_by_zipcode_with_region)

    intraRegionSlide.content2 = _regions_plot

    intraRegionSlide.render()
    return


@app.cell(hide_code=True)
def _(calculate_cog, pharmacies_by_zipcode_with_region, pl):
    provinces = pharmacies_by_zipcode_with_region["province"].unique().sort().to_list()

    regional_cogs = []
    for province in provinces:
        # Filter data for this province
        province_data = pharmacies_by_zipcode_with_region.filter(
            pl.col("province") == province
        )

        # Calculate CoG for this province
        cog_lon, cog_lat = calculate_cog(province_data, x_col='lon', y_col='lat')

        regional_cogs.append({
            "province": province,
            "cog_lat": cog_lat,
            "cog_lon": cog_lon,
            "total_demand": province_data["demand"].sum()
        })

    # Create DataFrame with regional CoGs
    regional_cogs_df = pl.DataFrame(regional_cogs)
    return (regional_cogs_df,)


@app.cell(hide_code=True)
def _(
    mo,
    pharmacies_by_zipcode_with_region,
    plot_demand_points_by_region,
    regional_cogs_df,
    sc,
):
    multiCogSolutionSlide = sc.create_slide(
        "Multi-warehouse CoG network for Spain",
        layout_type="side-by-side",
        page_number=17
    )

    multiCogSolutionSlide.content1 = mo.md(
    r"""
    Using the regional CoG idea, we can now build a
    **multi-warehouse design**:

    - Spain is split into **provinces** (regions \(r\)).

    - Inside each province we use our intra-region demand points
      to compute the **regional Center of Gravity** \((X_r^*, Y_r^*)\).

    - We then place **one warehouse at each regional CoG**:
      - each province has its own suggested warehouse location,
      - distances from pharmacies to their local warehouse are
        much shorter than in the single-warehouse case.

    On the right you see the **resulting network**:
    one CoG-based warehouse per province across Spain.
    """
    )

    _regions_cog_plot = plot_demand_points_by_region(pharmacies_by_zipcode_with_region, regional_cogs_df)
    multiCogSolutionSlide.content2 = _regions_cog_plot

    multiCogSolutionSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    summarySlide = sc.create_slide(
        "Summary and next steps",
        layout_type="side-by-side",
        page_number=18
    )

    summarySlide.content1 = mo.md(
    r"""

    **What we did in this session**

    - Started from **real pharmacy data** in Spain (OpenStreetMap / Overpass).
    - Aggregated pharmacies into **province-level demand regions**.
    - Defined **demand points** inside each region and used them for:
      - a **single** Center of Gravity for all of Spain, and
      - **regional** Centers of Gravity → one CoG-based warehouse per province.

    **Strengths of the Center of Gravity approach**

    - Very **simple and transparent**.
    - Uses the **spatial distribution of demand**.
    - Provides **good candidate locations** for warehouses.
    """
    )

    summarySlide.content2 = mo.md(
    """
    **Limitations**

    - Ignores **fixed costs**, **capacities**, and detailed **service constraints**.
    - One national CoG → good geometric compromise, but long distances for many provinces.
    - One warehouse per province → short distances, but likely **too many warehouses** and too expensive.

    **Next steps**

    - In the next session, we move from these **geometric rules-of-thumb**
      to a **cost-based optimization model**:
      the **Warehouse Location Problem (WLP)**.

    - The WLP will help us decide:
      - **how many** warehouses Phoenix should operate in Spain, and
      - **where** to place them, balancing **cost** and **service**.
    """
    )

    summarySlide.render()
    return


if __name__ == "__main__":
    app.run()
