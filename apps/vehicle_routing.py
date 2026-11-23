import marimo

__generated_with = "0.16.5"
app = marimo.App(
    width="medium",
    app_title="Vehicle Routing",
    css_file="d3.css",
    layout_file="layouts/vehicle_routing.slides.json",
    on_startup="autorun",
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

    print(f"Detection: use_local={use_local}, use_wasm={use_wasm}, in_wasm={in_wasm}")

    class DataURLs:
        if use_local:
            # Local development mode
            BASE = "apps/public/vrptw/data"
            IMG_BASE = "apps/public/vrptw/images"
            SCENARIOS = f"{BASE}/scenarios.csv"
            PHARMACIES = f"{BASE}/pharmacies.parquet"
            METADATA = f"{BASE}/metadata.json"
            POIS = f"{BASE}/fuerth_pois_10km.csv"  # preloaded get_customers_overpass results
        else:
            # WASM/deployed mode - use GitHub raw URLs for data files
            BASE = raw_url("apps", "public", "vrptw", "data")
            IMG_BASE = "public/vrptw/images"  # Images work with relative paths
            SCENARIOS = f"{BASE}/scenarios.csv"
            PHARMACIES = f"{BASE}/pharmacies.parquet"
            METADATA = f"{BASE}/metadata.json"
            POIS = f"{BASE}/fuerth_pois_10km.csv"  # preloaded get_customers_overpass results

    print(f"Using BASE: {DataURLs.BASE}")
    return (DataURLs,)


@app.cell(hide_code=True)
async def _():
    # Only install packages in WebAssembly environment
    try:
        import micropip

        # Install required packages for VRPTW analysis
        packages = [
            "polars",
            "folium",
            "pyarrow",
            "requests"
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
    # Import required libraries for VRPTW analysis
    import polars as pl
    import folium
    import json
    import marimo as mo
    import requests
    import math
    import altair as alt
    import pandas as pd
    import colorsys
    import numpy as np
    from typing import Iterable, Optional
    from folium import plugins
    import warnings
    warnings.filterwarnings("ignore", message=".*narwhals.*is_pandas_dataframe.*")
    return (
        Iterable,
        Optional,
        alt,
        colorsys,
        folium,
        json,
        math,
        mo,
        pd,
        pl,
        plugins,
        requests,
    )


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
def _(mo):
    def slide_table(markdown: str) -> mo.Html:
        """Markdown table with a readable font size and compact rows (alignment comes from :--- / ---:)."""
        _style = (
            "<style>div.slide-table table th, div.slide-table table td "
            "{ font-size: 16px !important; padding: 3px 8px !important; line-height: 1.3 !important; vertical-align: top; }</style>"
        )
        return mo.Html(f'<div class="slide-table">{_style}{mo.md(markdown).text}</div>')
    return (slide_table,)


@app.cell(hide_code=True)
def _():
    lehrstuhl = "Chair of Logistics and Quantitative Methods"
    vorlesung = "Global Logistics and Supply Chain Management"
    presenter = "Nikolai Stein, Richard Pibernik"
    return lehrstuhl, presenter, vorlesung


@app.cell(hide_code=True)
def _(SlideCreator, lehrstuhl, presenter, vorlesung):
    DEPOT_LAT, DEPOT_LON = 49.504896, 11.015822

    sc = SlideCreator(lehrstuhl, vorlesung, presenter)
    return DEPOT_LAT, DEPOT_LON, sc


@app.cell(hide_code=True)
def _(sc):
    titleSlide = sc.create_title_slide(
        "Vehicle Routing with Time Windows",
        subtitle="Optimizing Last-Mile Delivery"
    )
    sc.styles()
    titleSlide.render()
    return


@app.cell(hide_code=True)
def _(DataURLs, mo, sc):
    fulfillmentIntroSlide = sc.create_slide(
        'From the network to the order: fulfillment',
        layout_type='1-column',
        page_number=2
    )

    fulfillmentIntroSlide.content1 = mo.vstack([
        mo.image(f'{DataURLs.IMG_BASE}/phoenix_planning_tasks_fulfillment.png', width=1100),
        mo.md(
            """
            So far we designed the **structure** of the distribution network. Now we zoom into the task
            that runs on it **every single day**: **fulfillment** – back at Phoenix, where Chapter I started.
            """
        ),
    ], gap=1)

    fulfillmentIntroSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    fulfillmentTasksSlide = sc.create_slide(
        'Fulfillment: tasks and objectives',
        layout_type='1-column',
        page_number=3
    )

    fulfillmentTasksSlide.content1 = mo.md(
        """
        **Fulfillment** is the end-to-end process of converting a customer order into a completed delivery:

        1. **Order promising** – check inventory and capacity against the requested quantity and time;
           confirm (or reject) the order. Uses the available-inventory information from inventory planning!
        2. **Order preparation** – picking, packing, staging; handover to carrier or in-house fleet
        3. **Vehicle routing** – determine routes, allocate orders to routes
        4. **Order delivery** – ship, capture proof-of-delivery, handle returns and exceptions – the **last mile**

        Especially in B2C, fulfillment is often simply called "the last mile". It is where the **design** row
        meets the **execution** row: every promise made here is kept – or broken – by the network we just designed.
        """
    )

    fulfillmentTasksSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc, slide_table):
    servicePromiseSlide = sc.create_slide(
        'Fulfillment at Phoenix: the service promise',
        layout_type='1-column',
        page_number=4
    )

    servicePromiseSlide.content1 = mo.vstack([
        mo.md(
            """
            Fulfillment systems of pharmaceutical wholesalers in Germany (like Phoenix) are probably one of the
            most powerful systems in the world. Consider the following delivery schedules for pharmacies:
            """
        ),
        slide_table(
        """
        | Delivery option | Order cut-off (pharmacy must transmit the order) | Typical van departure from depot | Target arrival window at the pharmacy | Coverage & purpose |
        |:---|:---|:---|:---|:---|
        | **Main (overnight) run** | **18:30** the previous day (D-1) | 04:30–05:30 | **07:00–09:00** | All pharmacies; delivers the bulk of prescription demand for the day |
        | **Mid-day top-up** | **10:30** (same day) | 11:00–11:30 | **12:00–14:00** | All pharmacies; fills morning stock-outs and lunchtime e-prescriptions |
        | **Late top-up** *(urban depots only)* | **13:30** (same day) | 14:00–14:30 | **15:30–17:00** | Large-city pharmacies needing an extra same-day refill (≈ 15 % of national volume) |
        | **Emergency courier** | None – phone or portal 24 × 7 | Within 30 min of call | **≤ 2 h** from order | Life-critical medicines, out-of-hours and weekends; surcharge applies |
        """
        ),
    ], gap=1)

    servicePromiseSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc, slide_table):
    cutOffSlide = sc.create_slide(
        'Inside the 18:30 cut-off',
        layout_type='1-column',
        page_number=5
    )

    cutOffSlide.content1 = mo.vstack([
        slide_table(
        """
        | # | Stage | When (typical) | What happens | What the pharmacy sees |
        |:---|:---|:---|:---|:---|
        | 1 | **Order promising** | Until 18:30 (instant decision) | Order arrives; stock & inbound checked; immediate confirmation or alternatives offered | Order confirmation with next-morning window 07:00–09:00 |
        | 2 | **Preparation** | 19:00–23:00; D-day 00:00–04:30 | Refill pick areas; pick items; check & seal into totes; group by route and stop order | – |
        | 3 | **Vehicle routing** | Base plan ~20:00; final 04:00–04:30 | Build/refresh routes, assign driver/vehicle, push ETAs; adjust for traffic/emergencies | ETA updates if changed |
        | 4 | **Delivery** | Load 04:30–05:00; arrive 07:00–09:00 | Scan totes onto van; depart; handover at pharmacy; capture proof-of-delivery; collect empties/returns | Signed proof-of-delivery; invoice follows |
        """
        ),
        mo.md("**Order at 18:30 – delivery at the pharmacy between 07:00 and 09:00 the next morning.**"),
    ], gap=1.5)

    cutOffSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc, slide_table):
    moneySlide = sc.create_slide(
        'Where the money is',
        layout_type='side-by-side',
        page_number=6
    )

    moneySlide.content1 = mo.vstack([
        mo.md("**Fulfillment cost breakdown**"),
        slide_table(
        """
        | Cost block | Share |
        |:---|---:|
        | **Delivery (last mile)** | **45–65 %** |
        | Warehousing / picking / packing | 25–35 % |
        | Overheads | the rest |
        """
        ),
    ], gap=1)

    moneySlide.content2 = mo.vstack([
        mo.md(
            """
            **And where the lever is**

            The biggest optimization potential lies in **vehicle routing**: it strongly drives delivery
            cost – and it is a genuinely hard planning problem.
            """
        ),
        mo.Html(
            '<div style="background: #1e3a8a; color: #ffffff; padding: 16px 20px; border-radius: 6px; font-size: 19px; line-height: 1.4;">'
            'In the following we look at vehicle routing <i>with time windows</i> – because Phoenix does not '
            'just promise delivery, it promises delivery <b>between 07:00 and 09:00</b>.'
            '</div>'
        ),
    ], gap=1)

    moneySlide.render()
    return


@app.cell(hide_code=True)
def _(DataURLs, mo, sc):
    motivationPart1Slide = sc.create_slide(
        'How to deliver the order to the customer?',
        layout_type='side-by-side',
        page_number=7
    )

    motivationPart1Slide.content1 = mo.md(
        """
        **Order delivery**
        - After an order has been confirmed it has to be delivered to the customer (pharmacy)
        - However, it is not financially viable to deliver each order for every single product individually
        - Instead, Phoenix operates multiple **warehouses**, each operating a fleet of delivery trucks, to serve customers across **Germany**

        This is the **distribution network** – in the first part of this chapter we designed one for Spain. Now we look at how Phoenix runs its network in Germany **every day**
        """
    )

    motivationPart1Slide.content2 = mo.image(f'{DataURLs.IMG_BASE}/planner_distribution_network.png')

    motivationPart1Slide.render()
    return


@app.cell(hide_code=True)
def _(DataURLs, mo, sc):
    motivationPart2Slide = sc.create_slide(
        'How to deliver the order to the customer?',
        layout_type='side-by-side',
        page_number=8
    )

    motivationPart2Slide.content1 = mo.md(
        """
        **Last mile**
        - In this example, focus on the distribution for customers in the **Fürth** region
        - Here, Phoenix operates a warehouse and a fleet of delivery trucks serving pharmacies in the region
        - Instead of delivering each order of Amoxicillin directly, planners have to decide which delivery tour is used to deliver an order to the customer in time at minimal cost
        - We call this final step of the delivery process where goods are moved from a transportation hub to their final destination **last-mile delivery**

        **Key Question:** How can we design stable and efficient tours for **last-mile delivery**?

        """
    )

    motivationPart2Slide.content2 = mo.image(f'{DataURLs.IMG_BASE}/planner_last_mile.png')

    motivationPart2Slide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    problemDescriptionSlide = sc.create_slide(
        "The underlying decision problem",
        layout_type="2-column",
        page_number=9
    )
    problemDescriptionSlide.content1 = mo.md(
        """
        **Intuition**:
        - Designing the daily truck tours is a well-**studied** but **notoriously** hard problem known as **V**ehicle **R**outing **P**roblem with **T**ime **W**indows (VRPTW)
        - We must plan daily truck tours so that all pharmacies receive their orders **within promised time windows**, using **limited vehicle capacity**, while keeping **total cost low**.

        **What goes in (parameters)**:
        - **Customers**: locations, delivery time windows
        - **Network**: warehouse (depot), road travel times/distances.
        - **Fleet**: number of trucks, capacities, shift limits (max route duration), fixed/variable costs

        **What we decide (decisions)**:
        - **Sequencing (routing)**: visit order per truck
        - **Timing**: arrival times to hit each customer’s time window
        """
    )

    problemDescriptionSlide.content2 = mo.md(
        """
        **What must be respected (constraints)**:
        - **Capacity**: load on any truck ≤ capacity
        - **Time windows**: arrival within each customer’s window
        - **Service & travel times**: cumulative time including service at each stop
        - **Route rules**: each customer served exactly once; vehicle starts/ends at depot; max route duration/driver hours/breaks

        **What we optimize (objective)**:
        - Minimize **total cost** (distance)

        **How this maps to our example**
        - Depot: Phoenix warehouse (**Fürth** region)
        - Customers: pharmacies with daily orders and contracted delivery windows
        - Fleet: delivery vans with known capacity and shift length
        - Goal: cover all pharmacies on time with as few km as possible
        """
    )

    problemDescriptionSlide.render()
    return


@app.cell
def _(pl, requests):
    def get_customers_overpass(
        customer_type: str, center_lat: float, center_lon: float, radius_km: float, timeout: int = 30
    ) -> pl.DataFrame:
        """Fetch POIs within a radius using Overpass (browser-safe: HTTPS + GET with params)."""
        # Public Overpass servers - if one is busy, we try the next one
        OVERPASS_URLS = [
            "https://overpass-api.de/api/interpreter",
            "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
        ]
        # Overpass rejects the default python-requests user agent; browsers send their own
        import sys
        headers = {} if sys.platform == "emscripten" else {"User-Agent": "GLSCM-lecture (JMU Wuerzburg)"}
        radius_m = int(radius_km * 1000)

        query = f"""
        [out:json][timeout:{timeout}];
        (
          node["amenity"="{customer_type}"](around:{radius_m},{center_lat},{center_lon});
        );
        out center;
        """

        last_err = None
        for url in OVERPASS_URLS:
            try:
                # In browsers, use GET with ?data=... to satisfy CORS rules
                r = requests.get(url, params={"data": query}, headers=headers, timeout=timeout)
                r.raise_for_status()
                data = r.json()
                if "elements" not in data:
                    raise ValueError("Invalid response format from Overpass API")

                rows = []
                for el in data["elements"]:
                    if el["type"] == "node":
                        lat, lon = el["lat"], el["lon"]
                    elif el["type"] in ("way", "relation") and "center" in el:
                        lat, lon = el["center"]["lat"], el["center"]["lon"]
                    else:
                        continue
                    tags = el.get("tags", {})
                    name = tags.get("name", tags.get("brand", str(el["id"])))
                    rows.append({"name": name, "lat": lat, "lon": lon})

                return pl.DataFrame(rows)

            except Exception as e:
                last_err = e
                continue

        # If all endpoints failed, surface the last error with context
        raise requests.RequestException(f"Overpass request failed (HTTPS/GET). Last error: {last_err}")
    return (get_customers_overpass,)


@app.cell(hide_code=True)
def _(mo):
    category_selector = mo.ui.dropdown(options= {'Pharmacies': 'pharmacy', 'Doctors': 'doctors', 'Parcel lockers': 'parcel_locker', 'Bars': 'bar'}, value='Pharmacies', label='Category')
    return (category_selector,)


@app.cell(hide_code=True)
def _(category_selector, df_pois, mo, pl, sc):
    findingCustomersSlide = sc.create_slide(
        "Estimating the model parameters (Customers)",
        layout_type='side-by-side',
        page_number=10
    )

    findingCustomersSlide.content1 = mo.md(
        """
        **Idea**:
        - In order to plan the tours we need to know all locations that have to be visited regularly
        - In the case of Phoenix, we have to identify all relevant customers (pharmacies) in each delivery region
        - In our example we use the Phoenix warehouse (depot) in **Fürth** (lat: 49.504896, lon: 11.015822)

        **Solution**:
        - To identify relevant locations we can use geocoding APIs
        - We can choose commercial options such as Google Places or open-source options such as Nominatim or Overpass
        - The function ```get_customers_overpass``` shows how to query such APIs (see the [documentation](https://wiki.openstreetmap.org/wiki/Key:amenity) for a full list of available categories)
        - Public Overpass servers are often slow or busy, so we ran this query for the **Fürth** depot (radius 10 km) in advance
        """
    )

    # Preloaded results of get_customers_overpass(category, 49.504896, 11.015822, radius_km=10)
    data = df_pois.filter(pl.col("category") == category_selector.value).select("name", "lat", "lon")

    findingCustomersSlide.content2 = mo.vstack([
        mo.hstack([
            category_selector,
            mo.md(f"**{data.height}** locations within 10 km of the depot"),
        ], justify='start', align='center', gap=2),
        mo.ui.table(data, show_column_summaries=False, show_data_types=False, selection=None)
    ])

    findingCustomersSlide.render()
    return (data,)


@app.cell(hide_code=True)
def _(DataURLs, pd, pl):
    # Load main datasets
    df_scenarios = pl.read_csv(DataURLs.SCENARIOS)
    df_pois = pl.read_csv(DataURLs.POIS)

    # Try parquet with polars, fallback to pandas if it fails (WASM compatibility)
    try:
        df_pharmacies = pl.read_parquet(DataURLs.PHARMACIES)
    except (AttributeError, Exception) as e:
        # WASM polars doesn't support parquet properly
        # Use pandas to read parquet, then convert to polars
        print(f"Polars parquet failed: {e}, using pandas fallback...")
        df_pharmacies_pd = pd.read_parquet(DataURLs.PHARMACIES)
        df_pharmacies = pl.from_pandas(df_pharmacies_pd)
    return df_pharmacies, df_pois, df_scenarios


@app.cell(hide_code=True)
def _(DEPOT_LAT, DEPOT_LON, Iterable, Optional, df_scenarios, folium, mo, pl):
    def create_params_map(
        radius_km: float,
        pharmacies_df: pl.DataFrame,
        *,
        highlighted_ids: Optional[Iterable] = None,
        id_col: str = "id",
        highlight_color: str = "orange",
        highlight_radius: int = 7,
        normal_color: str = "green",
        normal_radius: int = 3,
        zoom_start = 8
    ):
        """
        Build a folium map around the depot with a radius overlay and pharmacy markers.
        Optionally highlight a subset of pharmacies by id (bigger marker + different color).
        Returns (map, count_of_displayed_pharmacies).
        """
        highlighted_ids = set(highlighted_ids or [])

        _params_map = folium.Map(
            location=[DEPOT_LAT, DEPOT_LON],
            zoom_start=zoom_start,
            tiles="OpenStreetMap",
            width=500,
            height=300,
        )

        folium.Marker(
            [DEPOT_LAT, DEPOT_LON],
            popup="Distribution Depot",
            tooltip="Phoenix Warehouse Sportplatzstraße 30, 90765 Fuerth",
            icon=folium.Icon(color="red", icon="home", prefix="fa"),
        ).add_to(_params_map)

        folium.Circle(
            location=[DEPOT_LAT, DEPOT_LON],
            radius=radius_km * 1000,
            color="blue",
            fillColor="lightblue",
            fillOpacity=0.2,
            weight=2,
        ).add_to(_params_map)

        # Decide which rows to display (respect radius if available)
        filtered_df = pharmacies_df
        if {"lat", "lon"}.issubset(set(pharmacies_df.columns)):
            if "distance_from_center_km" in pharmacies_df.columns:
                filtered_df = pharmacies_df.filter(
                    pl.col("distance_from_center_km") <= radius_km
                )
            # else: keep all rows (no radius filter available)

            # Add markers
            for row in filtered_df.iter_rows(named=True):
                is_highlight = row.get(id_col) in highlighted_ids if id_col in pharmacies_df.columns else False
                color = highlight_color if is_highlight else normal_color
                radius = highlight_radius if is_highlight else normal_radius

                folium.CircleMarker(
                    [row["lat"], row["lon"]],
                    radius=radius,
                    popup=f"{row.get('name', 'Unknown')}",
                    tooltip=f"{row.get('name', 'Unknown')}",
                    color="darkgreen" if not is_highlight else color,
                    fillColor=color,
                    fillOpacity=0.85 if is_highlight else 0.7,
                    weight=2 if is_highlight else 1,
                ).add_to(_params_map)

            count = filtered_df.height
        else:
            # No coordinates → nothing to plot
            count = 0

        return _params_map, count


    radius_vals_params = sorted(df_scenarios.select(pl.col("radius_km")).unique().to_series().to_list())
    map_radius_slider_params = mo.ui.slider(
        start=min(radius_vals_params),
        stop=max(radius_vals_params),
        step=5,
        value=25,
        label="Service Radius (km)"
    )
    return create_params_map, map_radius_slider_params


@app.cell(hide_code=True)
def _(create_params_map, df_pharmacies, map_radius_slider_params, mo, sc):
    customerViewSlide = sc.create_slide(
        "Finding the customers for the Fürth warehouse",
        layout_type='side-by-side',
        page_number=11
    )

    customerViewSlide.content1 = mo.md(
        """
        We can **formalize** the customer related parameters as follows:
        - Set of pharmacies: $\mathcal{C} = \{1, 2, \ldots, n\}$
        - Each pharmacy $i \in \mathcal{C}$ is located at coordinates $(x_i, y_i)$
        - Each pharmacy $i$ has a time window $[e_i, l_i]$ where it expects deliveries
        - $e_i$: earliest time delivery can start
        - $l_i$: latest time delivery must be completed
        - Vehicle must start service within this window

        The map shows the same **real pharmacies** for larger radii around the **Fürth** depot – the customers our model has to serve
        """
    )

    _params_map, _n_rows = create_params_map(
        radius_km=map_radius_slider_params.value, 
        pharmacies_df=df_pharmacies
    )

    customerViewSlide.content2 = mo.vstack([
        mo.hstack([
            map_radius_slider_params,
            mo.md("$|\\mathcal{C}|$ = " + str(_n_rows))
        ], justify="start", gap=3),
        _params_map
    ])

    customerViewSlide.render()
    return


@app.cell(hide_code=True)
def _(math):
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine great-circle distance between two WGS84 points in kilometers."""
        R_km = 6371.0088
        lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(math.radians, (lat1, lon1, lat2, lon2))
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R_km * c


    def calculate_travel_time(distance_km: float, speed_kmh: float=40) -> float:
        """Return travel time for a given distance and constant speed in minutes."""
        if speed_kmh <= 0:
            raise ValueError("speed_kmh must be > 0")

        time_h = distance_km / speed_kmh
        return time_h * 60
    return calculate_distance, calculate_travel_time


@app.cell(hide_code=True)
def _(DEPOT_LAT, DEPOT_LON, calculate_distance, calculate_travel_time, pl):
    def _first_coords_by_name(df: pl.DataFrame, name: str) -> tuple[float, float] | None:
        rows = df.filter(pl.col("name") == name).select("lat", "lon").to_numpy()
        if rows.size == 0:
            return None
        return float(rows[0, 0]), float(rows[0, 1])

    def build_distance_matrix(df_pharmacies: pl.DataFrame, selected_names: list[str]) -> pl.DataFrame:
        """
        Distance matrix (km) for Depot + selected pharmacy names.
        - Uses the first occurrence of each name in df_pharmacies.
        - Skips None/empty or not-found names.
        - Calls the provided calculate_distance(lat1, lon1, lat2, lon2).
        """
        # Clean list: drop None/empty, preserve order, dedupe
        seen, clean = set(), []
        for n in selected_names:
            if n and n not in seen:
                clean.append(n); seen.add(n)

        nodes = ["Depot"] + clean
        coords: dict[str, tuple[float, float]] = {"Depot": (DEPOT_LAT, DEPOT_LON)}

        # Resolve coords for names; drop those not found
        missing = []
        for n in clean:
            c = _first_coords_by_name(df_pharmacies, n)
            if c is None:
                missing.append(n)
            else:
                coords[n] = c
        for n in missing:
            nodes.remove(n)

        # Build pairwise distances
        data = {"from": nodes}
        for j in nodes:
            latj, lonj = coords[j]
            col_vals = []
            for i in nodes:
                if i == j:
                    col_vals.append(0.0)
                else:
                    lati, loni = coords[i]
                    col_vals.append(calculate_distance(lati, loni, latj, lonj))
            data[j] = col_vals

        df = pl.DataFrame(data)
        # Round numeric columns (all except 'from') for display
        df = df.with_columns(pl.col([c for c in nodes]).round(2))
        return df


    def build_travel_time_matrix(
        df_pharmacies: pl.DataFrame,
        selected_names: list[str],
        *,
        speed_kmh: float = 40.0
    ) -> pl.DataFrame:
        """
        Travel-time matrix (minutes) for Depot + selected pharmacy names.
        Uses:
          - calculate_distance(lat1, lon1, lat2, lon2) -> km
          - calculate_travel_time(distance_km, speed_kmh) -> minutes
        Skips None/empty/not-found names; uses first occurrence per name.
        """
        # Clean list: drop None/empty, preserve order, dedupe
        seen, clean = set(), []
        for n in selected_names:
            if n and n not in seen:
                clean.append(n); seen.add(n)

        nodes = ["Depot"] + clean
        coords: dict[str, tuple[float, float]] = {"Depot": (DEPOT_LAT, DEPOT_LON)}

        # Resolve coords and drop missing
        missing = []
        for n in clean:
            c = _first_coords_by_name(df_pharmacies, n)
            if c is None:
                missing.append(n)
            else:
                coords[n] = c
        for n in missing:
            nodes.remove(n)

        # Build pairwise travel times
        data = {"from": nodes}
        for j in nodes:
            latj, lonj = coords[j]
            col_vals = []
            for i in nodes:
                if i == j:
                    col_vals.append(0.0)
                else:
                    lati, loni = coords[i]
                    d_km = calculate_distance(lati, loni, latj, lonj)
                    t_min = calculate_travel_time(d_km, speed_kmh=speed_kmh)
                    col_vals.append(t_min)
            data[j] = col_vals

        df = pl.DataFrame(data)
        # Round numeric columns (all except 'from') for display
        df = df.with_columns(pl.col([c for c in nodes]).round(1))
        return df
    return build_distance_matrix, build_travel_time_matrix


@app.cell(hide_code=True)
def _(data, mo):
    location1Selector = mo.ui.dropdown(
        options=data['name'], 
        searchable=True, 
    )

    location2Selector = mo.ui.dropdown(
        options=data['name'], 
        searchable=True, 
    )

    location3Selector = mo.ui.dropdown(
        options=data['name'], 
        searchable=True, 
    )

    choice = mo.ui.radio(
        options=["Distance (km)", "Time (min)"],
        value="Distance (km)",
        inline=True,        # puts options on one line
    )
    return choice, location1Selector, location2Selector, location3Selector


@app.cell(hide_code=True)
def _(
    build_distance_matrix,
    build_travel_time_matrix,
    choice,
    create_params_map,
    data,
    location1Selector,
    location2Selector,
    location3Selector,
    mo,
    sc,
):
    networkViewSlides = sc.create_slide(
        "Estimating the model parameters (Network)",
        layout_type='side-by-side',
        page_number=12
    )

    networkViewSlides.content1 = mo.md(
                """
                **Idea**:
                - To compare the length (and costs) of different tours we need to know the pairwise **distances** between all nodes (depot + customers) in the network
                - To ensure that every customer is served inside the time window we also need to know the pairwise **travel times**
                - We want to use clear units (km, minutes)

                **Simple solution**:
                - Compute the Haversine distance
                - Convert to time with a constant speed
                - See implementations in ```calculate_distance``` and ```calculate_travel_time```

                **More realistic option**
                - To identify realisitc times and distances we can use routing APIs
                - We can choose commercial options such as Google Maps or open source options such as OSRM
                """
            )

    selected_names = [
        location1Selector.value,
        location2Selector.value,
        location3Selector.value
    ]

    _params_map, _ = create_params_map(
        radius_km=10, 
        pharmacies_df=data,
        zoom_start=10,
        highlighted_ids=selected_names,
        id_col='name'
    )

    _distance_df = build_distance_matrix(data, selected_names)
    _traveltime_df = build_travel_time_matrix(data, selected_names, speed_kmh=40)  

    _table = (
        mo.ui.table(_distance_df, pagination=False, selection=None,
                    show_column_summaries=False, show_data_types=False, show_download=False)
        if choice.value == "Distance (km)"
        else
        mo.ui.table(_traveltime_df, pagination=False, selection=None,
                    show_column_summaries=False, show_data_types=False, show_download=False)
    )

    networkViewSlides.content2 = mo.vstack([
        mo.hstack([
            location1Selector,
            location2Selector,
            location3Selector
        ], justify="start", gap=2),
        _params_map,
        choice,
        _table
    ])

    networkViewSlides.render()
    return


@app.cell(hide_code=True)
def _(DataURLs, mo, sc):
    distanceMatrixSlide = sc.create_slide(
        "Estimating the model parameters (Network)",
        layout_type='side-by-side',
        page_number=13
    )

    distanceMatrixSlide.content1 = mo.md(
        """
        We can **formalize** the network related parameters as follows:
        - Distance matrix $\mathcal{D}$:
            - $d_{ij}$ = distance (in km) from location $i$ to location $j$
            - $i, j \in N$ where $N = \{0\} \cup \mathcal{C}$ ($0$ is the depot)
        - Travel time matrix $\mathcal{T}$:
            - $t_{ij}$ = travel time (in minutes) from location $i$ to location $j$
            - Depends on distance, road types, traffic conditions
            - Used to ensure time window constraints are satisfied

        To keep things realistic and fast, we **precomputed** the real distance and travel time matrix using the **Open Source Routing Machine (OSRM)**
        """
    )

    distanceMatrixSlide.content2 = mo.image(f'{DataURLs.IMG_BASE}/osrm-backend.png')

    distanceMatrixSlide.render()
    return


@app.cell(hide_code=True)
def _(math):
    # Toy example for the model slides: depot 0 and five pharmacies on a 10 x 10 km grid, two vans
    TOY_NODES = {"0": (5, 5), "A": (2, 8), "B": (6, 9), "C": (9, 7), "D": (8, 2), "E": (2, 3)}
    TOY_DEMAND = {"A": 3, "B": 4, "C": 2, "D": 5, "E": 3}  # q_i in crates
    TOY_WINDOWS = {"0": (0, 180), "A": (0, 30), "B": (15, 60), "C": (30, 90), "D": (0, 45), "E": (30, 120)}  # [e_i, l_i], minutes after 07:00
    TOY_SERVICE = 5  # h_i in minutes
    TOY_CAPACITY = 10  # Q_k in crates
    TOY_MIN_PER_KM = 2  # t_ij at 30 km/h
    TOY_VANS = ["1", "2"]

    def toy_distance(i, j):
        return round(math.dist(TOY_NODES[i], TOY_NODES[j]), 1)

    def toy_clock(minutes):
        _m = int(round(minutes))
        return f"{7 + _m // 60:02d}:{_m % 60:02d}"

    def evaluate_toy(route_texts: dict) -> dict:
        """Turn typed routes ('0 A B 0') into arcs with x_ijk = 1 and evaluate every constraint."""
        arcs, schedule, unknown = [], [], []
        for k in TOY_VANS:
            tokens = route_texts.get(k, "").replace(",", " ").replace("-", " ").replace(">", " ").upper().split()
            unknown += [t for t in tokens if t not in TOY_NODES]
            seq = [t for t in tokens if t in TOY_NODES]
            steps = [(i, j) for i, j in zip(seq, seq[1:]) if i != j]
            arcs += [(i, j, k, toy_distance(i, j)) for i, j in steps]
            # service start times along the route; the vans leave the depot at 07:00
            s = 0 if not seq or seq[0] == "0" else TOY_WINDOWS[seq[0]][0]
            for i, j in steps:
                arrival = s + (TOY_SERVICE if i != "0" else 0) + TOY_MIN_PER_KM * toy_distance(i, j)
                s = max(TOY_WINDOWS[j][0], arrival)
                schedule.append({"van": k, "stop": j, "arrival": arrival, "start": s, "ok": s <= TOY_WINDOWS[j][1]})
        customers = [c for c in TOY_NODES if c != "0"]
        return {
            "arcs": arcs,
            "schedule": schedule,
            "unknown": unknown,
            "km": round(sum(a[3] for a in arcs), 1),
            "visits": {j: sum(a[1] == j for a in arcs) for j in customers},
            "depot": {k: (sum(a[0] == "0" and a[2] == k for a in arcs), sum(a[1] == "0" and a[2] == k for a in arcs)) for k in TOY_VANS},
            "flow": {(j, k): (sum(a[1] == j and a[2] == k for a in arcs), sum(a[0] == j and a[2] == k for a in arcs))
                     for k in TOY_VANS for j in customers},
            # capacity as in the model: customer i counts for van k if van k leaves i
            "load": {k: sum(TOY_DEMAND[a[0]] for a in arcs if a[2] == k and a[0] != "0") for k in TOY_VANS},
        }
    return (
        TOY_CAPACITY,
        TOY_DEMAND,
        TOY_NODES,
        TOY_VANS,
        TOY_WINDOWS,
        evaluate_toy,
        toy_clock,
    )


@app.cell(hide_code=True)
def _(mo):
    toy_reset_button = mo.ui.button(label="↺ Reset", value=0, on_click=lambda v: v + 1)
    return (toy_reset_button,)


@app.cell(hide_code=True)
def _(mo, toy_reset_button):
    toy_reset_button.value  # clicking "reset" restores the example routes
    toy_routes = mo.ui.dictionary({
        "1": mo.ui.text(value="0 A", full_width=True),
        "2": mo.ui.text(value="0 B", full_width=True),
    })
    return (toy_routes,)


@app.cell(hide_code=True)
def _(
    TOY_CAPACITY,
    TOY_DEMAND,
    TOY_NODES,
    TOY_VANS,
    TOY_WINDOWS,
    alt,
    evaluate_toy,
    math,
    mo,
    pd,
    slide_table,
    toy_clock,
    toy_routes,
):
    toy = evaluate_toy(dict(toy_routes.value))

    def _check(ok):
        return "✓" if ok else '<b style="color: #dc2626;">✗</b>'

    def toy_map(size: int, node_info: str | None = None):
        """Grid map of the toy example with the arcs of the typed routes (one colour per van)."""
        _scale = alt.Scale(domain=[0, 10], nice=False)
        _axis = alt.Axis(tickCount=10, grid=True, title=None, labels=False, ticks=False, domain=False)
        _x, _y = alt.X("x:Q", scale=_scale, axis=_axis), alt.Y("y:Q", scale=_scale, axis=_axis)
        _color = alt.Color("van:N", scale=alt.Scale(domain=["Van 1", "Van 2"], range=["#1e3a8a", "#f59e0b"]),
                           legend=alt.Legend(orient="bottom", title=None))
        _nodes = pd.DataFrame([
            {"node": n, "x": x, "y": y,
             "info": ("" if n == "0" else
                      f"{TOY_DEMAND[n]} crates" if node_info == "demand" else
                      f"{toy_clock(TOY_WINDOWS[n][0])}–{toy_clock(TOY_WINDOWS[n][1])}" if node_info == "window" else "")}
            for n, (x, y) in TOY_NODES.items()
        ])
        _layers = [alt.Chart(_nodes).mark_point(opacity=0).encode(x=_x, y=_y)]  # keeps the grid when no arc is set
        if toy["arcs"]:
            _lines, _arrows = [], []
            for _idx, (i, j, k, d) in enumerate(toy["arcs"]):
                (_x1, _y1), (_x2, _y2) = TOY_NODES[i], TOY_NODES[j]
                _lines += [{"arc": _idx, "van": f"Van {k}", "x": _x1, "y": _y1, "o": 0},
                           {"arc": _idx, "van": f"Van {k}", "x": _x2, "y": _y2, "o": 1}]
                _arrows.append({"van": f"Van {k}", "x": _x1 + 0.6 * (_x2 - _x1), "y": _y1 + 0.6 * (_y2 - _y1),
                                "angle": math.degrees(math.atan2(_x2 - _x1, _y2 - _y1)) % 360, "arc": f"{i} → {j}: {d} km"})
            _layers.append(alt.Chart(pd.DataFrame(_lines)).mark_line(strokeWidth=3).encode(
                x=_x, y=_y, detail="arc:N", order="o:Q", color=_color))
            _layers.append(alt.Chart(pd.DataFrame(_arrows)).mark_point(shape="triangle", filled=True, size=140, opacity=1).encode(
                x=_x, y=_y, color=_color, tooltip=["arc:N"],
                angle=alt.Angle("angle:Q", scale=alt.Scale(domain=[0, 360], range=[0, 360]))))
        _layers += [
            alt.Chart(_nodes).mark_point(filled=True, size=260, opacity=1).encode(
                x=_x, y=_y, shape=alt.condition("datum.node == '0'", alt.value("square"), alt.value("circle")),
                color=alt.condition("datum.node == '0'", alt.value("#111827"), alt.value("#16a34a"))),
            alt.Chart(_nodes).mark_text(dy=-17, fontSize=15, fontWeight="bold").encode(x=_x, y=_y, text="node:N"),
            alt.Chart(_nodes).mark_text(dy=19, fontSize=11, color="#374151").encode(x=_x, y=_y, text="info:N"),
        ]
        return alt.layer(*_layers).properties(width=size, height=size)

    # Page 14: which x_ijk are 1
    _arc_rows = "\n".join(f"| {k} | {i} → {j} | $x_{{{i}{j}{k}}} = 1$ |" for (i, j, k, _d) in dict.fromkeys(
        (a[0], a[1], a[2], a[3]) for a in toy["arcs"]))
    _ones = len({(i, j, k) for (i, j, k, _d) in toy["arcs"]})
    _note = f"All other **{60 - _ones}** of the 60 variables $x_{{ijk}}$ are 0 (6 × 5 arcs × 2 vans)."
    if toy["unknown"]:
        _note += f" Ignored input: {', '.join(toy['unknown'])} (use 0 and A–E)."
    toy_vars_info = mo.vstack([
        slide_table("| Van | Arc | Variable |\n|:---|:---|:---|\n" + _arc_rows),
        mo.md(_note),
    ], gap=0.5)

    # Page 15: objective
    _rows = "\n".join(f"| {i} → {j} | {k} | {d:.1f} km |" for (i, j, k, d) in toy["arcs"])
    toy_cost_info = slide_table(
        "| Arc | Van | $d_{ij}$ |\n|:---|:---|---:|\n" + _rows + f"\n| **Total** | | **{toy['km']:.1f} km** |"
    )

    # Page 16: flow conservation
    _visits = "\n".join(f"| {j} | {n} | {_check(n == 1)} |" for j, n in toy["visits"].items())
    _depot = "\n".join(f"| {k} | {o} | {r} | {_check(o <= 1 and r <= 1)} |" for k, (o, r) in toy["depot"].items())
    toy_flow_info = mo.vstack([
        slide_table("| Customer | Arrivals | = 1? |\n|:---|---:|:---:|\n" + _visits),
        slide_table("| Van | Leaves depot | Returns | OK? |\n|:---|---:|---:|:---:|\n" + _depot),
        mo.md("$\\le 1$ also allows 0: a van may stay at the depot. A van that leaves but does not return is caught by **flow continuity** (next page)."),
    ], gap=0.5)

    # Page 17: flow continuity (only customers a van actually touches)
    _cont = "\n".join(f"| {j} | {k} | {i_n} | {o_n} | {_check(i_n == o_n)} |"
                      for (j, k), (i_n, o_n) in toy["flow"].items() if i_n or o_n)
    toy_continuity_info = slide_table("| Customer | Van | In | Out | In = Out? |\n|:---|:---|---:|---:|:---:|\n" + _cont)

    # Page 18: capacity
    _served = {k: [i for (i, j, kk, _d) in toy["arcs"] if kk == k and i != "0"] for k in TOY_VANS}
    _cap = "\n".join(f"| Van {k} | {' '.join(_served[k]) or '–'} | {toy['load'][k]} / {TOY_CAPACITY} | {_check(toy['load'][k] <= TOY_CAPACITY)} |"
                     for k in TOY_VANS)
    toy_capacity_info = mo.vstack([
        slide_table("| Van | Serves | Crates | ≤ Q? |\n|:---|:---|---:|:---:|\n" + _cap),
        mo.md(f"Demand $q_i$ in crates (see map), capacity $Q_k = {TOY_CAPACITY}$ crates per van"),
    ], gap=0.5)

    # Page 19: time windows
    _time = "\n".join(
        f"| {r['van']} | {r['stop']} | {toy_clock(r['arrival'])} | {toy_clock(r['start'])} | "
        f"{toy_clock(TOY_WINDOWS[r['stop']][0])}–{toy_clock(TOY_WINDOWS[r['stop']][1])} | {_check(r['ok'])} |"
        for r in toy["schedule"])
    toy_time_info = slide_table(
        "| Van | Stop | Arrival | Start $s_{ik}$ | Window $[e_i, l_i]$ | OK? |\n|:---|:---|---:|---:|:---|:---:|\n" + _time
    )
    return (
        toy_capacity_info,
        toy_continuity_info,
        toy_cost_info,
        toy_flow_info,
        toy_map,
        toy_time_info,
        toy_vars_info,
    )


@app.cell(hide_code=True)
def _(mo, toy_map, toy_reset_button, toy_routes):
    def toy_panel(info, node_info=None, size=270, below=False):
        """Right column of the model slides: route inputs, toy map and the slide's evaluation."""
        def _label(text):
            return mo.Html(f'<span style="font-size: 15px; white-space: nowrap;">{text}</span>')
        _inputs = mo.hstack(
            [_label("Van 1"), toy_routes["1"], _label("Van 2"), toy_routes["2"], toy_reset_button],
            widths=[0.09, 0.31, 0.09, 0.31, 0.2], justify="start", align="center", gap=0.5,
        )
        _map = toy_map(size, node_info)
        _body = mo.vstack([_map, info], gap=0.5) if below else mo.hstack([_map, info], justify="start", align="start", gap=1)
        return mo.vstack([_inputs, _body], gap=0.5)
    return (toy_panel,)


@app.cell(hide_code=True)
def _(mo, sc, toy_panel, toy_vars_info):
    decisionVariablesSlide = sc.create_slide(
        'Modelling the decisions',
        layout_type='side-by-side',
        page_number=14
    )

    decisionVariablesSlide.content1 = mo.md(
        r'''
        Two types of decisions:
        - the order in which the vehicles visit the customers (**sequencing**)
        - the time when service at a customer starts (**timing**)

        **Routing variables** – for each arc $(i,j)$ and each vehicle $k$:

        $$
        x_{ijk} =
        \begin{cases}
        1, & \text{if vehicle } k \text{ drives directly from } i \text{ to } j\\
        0, & \text{otherwise}
        \end{cases}
        $$

        **Timing variables** – $s_{ik}$: time at which vehicle $k$ starts service at customer $i$
        (irrelevant if $k$ does not visit $i$)

        **Toy example (right):** depot 0, five pharmacies A–E, two vans. Type a route for each
        van – every arc you use sets one $x_{ijk}$ to 1.
        '''
    )

    decisionVariablesSlide.content2 = toy_panel(toy_vars_info)

    decisionVariablesSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc, toy_cost_info, toy_panel):
    objectiveFunctionSlide = sc.create_slide(
        'Modelling the objective function',
        layout_type='side-by-side',
        page_number=15
    )

    objectiveFunctionSlide.content1 = mo.md(
        r'''
        To find optimal tours, we need to specify the goal of the routing problem. In the VRPTW, this goal is typically to **minimize total operational cost**.

        - **Objective**: find a set of vehicle routes that
            - serve all customers within their time windows,
            - respect vehicle capacity and time constraints,
            - **minimize** the total cost of operation
        - **Typical cost measures**: total travel distance (**our example**), number of vehicles used, driver or fuel cost
        - **Mathematically:**

            $$
            \min \sum_{k\in K} \sum_{i\in N} \sum_{j\in N}d_{ij}x_{ijk}
            $$

        **Toy example:** Complete the routes so that every pharmacy is served. How short can you make the plan? The next pages check whether it is feasible.
        '''
    )

    objectiveFunctionSlide.content2 = toy_panel(toy_cost_info)

    objectiveFunctionSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc, toy_flow_info, toy_panel):
    flowConservationSlide = sc.create_slide(
        'Modelling the constraints (Flow conservation)',
        layout_type='side-by-side',
        page_number=16
    )

    flowConservationSlide.content1 = mo.md(
        r'''
        These constraints guarantee that every customer is visited exactly once and that **vehicle flows are consistent**.

        - **Each customer is visited exactly once:**

            $$
            \sum_{k\in K}\sum_{\substack{i\in\mathcal{N}\\ i\ne j}} x_{ijk} = 1 \quad \forall j\in \mathcal{C}
            $$

        - **Each vehicle leaves the depot at most once and returns at most once:**

            $$
            \sum_{j\in \mathcal{C}}x_{0jk} \le 1, \qquad \sum_{i\in \mathcal{C}}x_{i0k} \le 1 \quad \forall k\in K
            $$

        Vehicles start at the depot, visit a subset of customers, and return.

        **Try it:** visit a pharmacy twice, leave one out, or let a van return to the depot in between (`0 A 0 B 0`).
        '''
    )

    flowConservationSlide.content2 = toy_panel(toy_flow_info)

    flowConservationSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc, toy_continuity_info, toy_panel):
    flowContinuitySlide = sc.create_slide(
        'Modelling the constraints (Flow continuity)',
        layout_type='side-by-side',
        page_number=17
    )

    flowContinuitySlide.content1 = mo.md(
        r'''
        If a vehicle arrives at a customer, it must also leave again – this prevents disconnected or partial routes.

        - **Flow continuity constraint:**

            $$
            \sum_{i\in \mathcal{N}}x_{ijk} - \sum_{i\in \mathcal{N}}x_{jik} = 0 \quad \forall j\in \mathcal{C}, \forall k\in K
            $$

        - The **first term** counts the arcs **entering** customer $j$ with vehicle $k$, the **second term** the arcs **leaving** $j$
        - Prevents "dead ends" and keeps every route a connected path from the depot back to the depot

        **Try it:** what happens if a route ends at a pharmacy (e.g. `0 A B`)?
        '''
    )

    flowContinuitySlide.content2 = toy_panel(toy_continuity_info)

    flowContinuitySlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc, toy_capacity_info, toy_panel):
    vehicleCapacitySlide = sc.create_slide(
        'Modelling the constraints (Vehicle capacity)',
        layout_type='side-by-side',
        page_number=18
    )

    vehicleCapacitySlide.content1 = mo.md(
        r'''
        Each customer $i$ needs $q_i$ crates; each vehicle $k$ carries at most $Q_k$ crates.

        - **Capacity constraint:**

            $$
            \sum_{i\in \mathcal{C}}q_i \sum_{j\in \mathcal{N}}x_{ijk} \leq Q_{k} \quad \forall k\in K
            $$

        - $\sum_{j} x_{ijk} = 1$ if vehicle $k$ leaves customer $i$, i.e. if $k$ serves $i$
        - The total demand on a route must fit into the vehicle

        **Try it:** serve all five pharmacies with one van. Is it feasible?
        '''
    )

    vehicleCapacitySlide.content2 = toy_panel(toy_capacity_info, node_info="demand")

    vehicleCapacitySlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc, toy_panel, toy_time_info):
    timeWindowServiceStartSlide = sc.create_slide(
        'Modelling the constraints (Time windows & service start)',
        layout_type='side-by-side',
        page_number=19
    )

    timeWindowServiceStartSlide.content1 = mo.md(
        r'''
        Service at customer $i$ must **start within its time window** $[e_i,l_i]$; vehicles may **wait** if they arrive early. Service takes $h_i$ minutes.

        - **Time propagation (big-M):**

            $$
            s_{jk} \ge s_{ik} + h_i + t_{ij} - M(1-x_{ijk}) \quad \forall i\ne j,\; \forall k
            $$

        - **Time windows:**

            $$
            e_i \le s_{ik} \le l_i \quad \forall i\in \mathcal{N},\; \forall k\in K
            $$

        - If $x_{ijk}=1$, service at $j$ starts only after finishing $i$ and driving $t_{ij}$; if $x_{ijk}=0$, the large $M$ switches the constraint off

        **Toy example:** vans leave at 07:00, 30 km/h, 5 min per pharmacy. **Try it:** enter `0 D C E 0` for van 2, then the reverse `0 E C D 0`. Why is only one of them feasible?
        '''
    )

    timeWindowServiceStartSlide.content2 = toy_panel(toy_time_info, node_info="window", size=230, below=True)

    timeWindowServiceStartSlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    completeMIPSlide = sc.create_slide(
        "VRPTW — Complete optimization problem",
        layout_type="side-by-side",
        page_number=20
    )

    completeMIPSlide.content1 = mo.md(
        r'''
        - **Sets & nodes**:  $\mathcal{C}=\{1,\dots,n\}$ (customers), depot $0$, $\mathcal{N}=\{0\}\cup\mathcal{C}$; vehicles $K$  
        - **Data**:  demand $q_i$, service time $h_i$, distance $d_{ij}$ (km), travel time $t_{ij}$ (min), capacity $Q_k$, time windows $[e_i,l_i]$  
        - **Decision variables**:  $x_{ijk}\in\{0,1\}$ (arc $i\!\to\!j$ by vehicle $k$), $s_{ik}\ge 0$ (service start time of $i$ by $k$)

        - **Objective:**

            $$
            \min \sum_{k\in K}\sum_{i\in\mathcal{N}}\sum_{j\in\mathcal{N}} d_{ij}\,x_{ijk}
            $$


        - **Time windows & service start (big-M)**

            $$
            s_{jk} \;\ge\; s_{ik} + h_i + t_{ij} \;-\; M_{ij}\,(1 - x_{ijk})
            \quad \forall\, i\ne j,\; i,j\in\mathcal{N},\; \forall\,k\in K
            $$

            $$
            e_i \le s_{ik} \le l_i \quad \forall\, i\in\mathcal{N},\; \forall\,k\in K
            $$
        '''
    )

    completeMIPSlide.content2 = mo.md(
        r'''
        - **Flow & visit constraints**
            - Each customer visited exactly once:

                $$
                \sum_{k\in K}\sum_{\substack{i\in\mathcal{N}\\ i\ne j}} x_{ijk} = 1 \quad \forall\, j\in\mathcal{C}
                $$

            - Vehicle departures/returns:

                $$
                \sum_{j\in \mathcal{C}} x_{0jk} \le 1,\qquad
                \sum_{i\in \mathcal{C}} x_{i0k} \le 1 \quad \forall\,k\in K
                $$

            - Vehicle flow continuity:

                $$
                \sum_{i\in\mathcal{N}} x_{ijk} - \sum_{i\in\mathcal{N}} x_{jik} = 0
                \quad \forall\, j\in\mathcal{C},\; \forall\, k\in K
                $$

        - **Capacity constraint**

            $$
            \sum_{i\in\mathcal{C}} q_i \sum_{j\in\mathcal{N}} x_{ijk} \;\le\; Q_k
            \quad \forall\, k\in K
            $$
        '''
    )

    completeMIPSlide.render()
    return


@app.cell(hide_code=True)
def _(math, mo):
    def route_plans_log10(n_customers: int, n_vehicles: int):
        """
        log10 of the number of possible route plans: n customers on k vehicles that are told apart
        (as in the model, index k in x_ijk), the order on each route matters, a vehicle may stay at the depot.
        n! orders of the customers times C(n+k-1, k-1) ways to split them among the vehicles = (n+k-1)! / (k-1)!
        """
        n, k = n_customers, n_vehicles
        if n <= 0:
            return None
        return (math.lgamma(n + k) - math.lgamma(k)) / math.log(10)

    def vrptw_problem_complexity(n_customers: int, n_vehicles: int) -> dict:
        """
        Count variables and constraints for the VRPTW MIP used in class.
        Assumes a complete directed graph on N = {0} ∪ C (depot + customers),
        variables x_{ijk} (binary) for all i!=j and k, and s_{ik} (continuous).

        Returns a dict with a small breakdown and totals.
        """
        N = n_customers + 1           # |N| (customers + depot)
        arcs = N * (N - 1)            # all ordered pairs i!=j

        # Variables
        x_vars = n_vehicles * arcs
        s_vars = n_vehicles * N
        total_vars = x_vars + s_vars

        return {
            "total_vars": total_vars,
            'x_vars': x_vars,
            's_vars': s_vars
        }


    nCustomersSlider = mo.ui.slider(
        start=0, 
        stop=1000, 
        step=10,
        value=10,
        show_value=True,
        label='Customers'
    )

    nVehiclesDropdown = mo.ui.dropdown(
        options={"1": 1, "10": 10, "25": 25, "50": 50, "100": 100},
        value='1',
        label="Vehicles"
    )

    try:
        vrp_points  # list of dicts: {"customers": n, "total_vars": v, "k": k}
    except NameError:
        vrp_points = []
    return (
        nCustomersSlider,
        nVehiclesDropdown,
        route_plans_log10,
        vrp_points,
        vrptw_problem_complexity,
    )


@app.cell(hide_code=True)
def _(alt, pd, vrp_points, vrptw_problem_complexity):
    def plot_complexity(n,k):
        # Add point if new
        seen = {(p["customers"], p["k"]) for p in vrp_points}
        if (n, k) not in seen:
            size = vrptw_problem_complexity(n_customers=n, n_vehicles=k)
            vrp_points.append({"customers": n, "total_vars": size["total_vars"], "k": str(k)})

        # Plot accumulated points
        df = pd.DataFrame(vrp_points, columns=["customers", "total_vars", "k"])

        chart = (
            alt.Chart(df)
            .mark_point(filled=True, size=50)
            .encode(
                x=alt.X("customers:Q", title="Number of customers (n)"),
                y=alt.Y("total_vars:Q", title="Total number of variables"),
                color=alt.Color("k:N", title="Vehicles (k)"),
                tooltip=[
                    alt.Tooltip("customers:Q", title="Customers (n)"),
                    alt.Tooltip("total_vars:Q", title="Total variables", format=","),
                    alt.Tooltip("k:N", title="Vehicles (k)"),
                ],
            )
            .properties(width=400, height=270, title="Problem size: variables vs. customers")
        )
        return chart
    return (plot_complexity,)


@app.cell(hide_code=True)
def _(
    mo,
    nCustomersSlider,
    nVehiclesDropdown,
    plot_complexity,
    route_plans_log10,
    sc,
    vrptw_problem_complexity,
):
    solvingOverviewSlide = sc.create_slide(
        "Solving VRPTW in practice",
        layout_type="side-by-side",
        page_number=21
    )

    solvingOverviewSlide.content1 = mo.md(
        r"""
    **Why it’s hard (but doable in practice)**  
    - The VRPTW is a **NP-hard** problem: the number of possible tours **explodes** with customers and vehicles.  
    - Time windows & capacities add **tight coupling** between routing and timing.  
    - Exact optimality may be expensive for large, real datasets — but **good solutions** are achievable.
    - Use ```vrptw_problem_complexity``` to calculate the number of decision variables
    - Our toy example (5 pharmacies, 2 vans) already allows **720** route plans – only **40** of them are feasible

    **What we can use (toolbox)**  
    - **Exact MIP solvers:** open-source **HiGHS**, CBC; commercial **Gurobi**, CPLEX.  
    - **Heuristic / metaheuristic solvers:** **OR-Tools** (Routing/CP-SAT), savings, local search, Tabu, ALNS.  
    """
    )

    _n = nCustomersSlider.value
    _k = nVehiclesDropdown.value

    complexityChart = plot_complexity(_n,_k)

    # Number of decision variables vs. number of possible route plans for the current selection
    _vars = vrptw_problem_complexity(n_customers=_n, n_vehicles=_k)["total_vars"]
    _log = route_plans_log10(_n, _k)
    if _log is None:
        _plans, _compare = "–", "Move the slider to add customers."
    else:
        _plans = f"{round(10 ** _log):,}" if _log < 15 else f"≈ 10<sup>{int(_log):,}</sup>"
        _seconds_log = _log - 9  # checking one billion plans per second
        if _seconds_log < 0:
            _time = "less than a second"
        elif _seconds_log < 4.94:  # one day
            _time = f"about {10 ** _seconds_log / 3600:,.1f} hours" if _seconds_log > 3.56 else f"about {10 ** _seconds_log:,.0f} seconds"
        elif _seconds_log < 7.5:  # one year
            _time = f"about {10 ** _seconds_log / 86400:,.0f} days"
        else:
            _years_log = _seconds_log - 7.5
            _time = f"about {10 ** _years_log:,.0f} years" if _years_log < 6 else f"≈ 10<sup>{int(_years_log):,}</sup> years"
        _compare = f"Checking a billion plans per second takes {_time}."
        if _log > 80:
            _compare += " There are only ≈ 10<sup>80</sup> atoms in the universe."

    def _tile(label, value):
        return mo.Html(
            '<div style="border: 1px solid #E5E7EB; border-radius: 6px; padding: 6px 14px; min-width: 200px;">'
            f'<div style="font-size: 14px; color: #6B7280;">{label}</div>'
            f'<div style="font-size: 26px; font-weight: 700; color: #111827;">{value}</div></div>'
        )

    _content2 = mo.vstack([
        mo.hstack([nCustomersSlider, nVehiclesDropdown], gap=3, justify='center'),
        mo.hstack([_tile("Decision variables", f"{_vars:,}"), _tile("Possible route plans", _plans)], justify="center", gap=1),
        mo.Html(f'<div style="font-size: 15px; color: #374151; text-align: center;">{_compare}</div>'),
        complexityChart
    ], gap=0.6)


    solvingOverviewSlide.content2 = _content2

    solvingOverviewSlide.render()
    return


@app.cell(hide_code=True)
def _(DataURLs, mo, sc):
    solutionApproachSlide = sc.create_slide(
        "Solution approach (what we actually ran)",
        layout_type="side-by-side",
        page_number=22
    )

    solutionApproachSlide.content1 = mo.md(
        r"""
        **What we solved (overnight main run)**
        - Region: **Fürth depot**, catchment area **50 km**  
        - Data: real pharmacy snapshot + **precomputed** **distance/time** matrices  
        - Model: **VRPTW** (distance-minimizing), constraints as in the MIP slide

        **How we solved it**
        - Solver: **OR-Tools** (routing with time-window feasibility)  
        - Reason: scalable, fast, near-optimal in practice

        **Try it yourself**
        - We provide the full code to solve this problem on GitHub (code + instructions) 
        - Please follow the instructions in our repo (**[Repo link](https://github.com/NikoStein/om_lecture_fulfilment)**) to try it yourself
        """
    )

    solutionApproachSlide.content2 = mo.image(f'{DataURLs.IMG_BASE}/deliveryruns.png')

    solutionApproachSlide.render()
    return


@app.cell(hide_code=True)
def _(colorsys, folium, json, plugins, requests):
    def load_scenario(path: str) -> dict:
        """Load a precomputed VRPTW scenario JSON."""
        if path.startswith("http://") or path.startswith("https://"):
            # Load from URL
            response = requests.get(path)
            return json.loads(response.text)
        else:
            # Load from local file
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)

    def _generate_colors(n: int) -> list[str]:
        """Generate n visually distinct colors (HSV → hex)."""
        if n <= 1:
            return ["#1f77b4"]
        return [
            "#%02x%02x%02x" % tuple(int(c*255) for c in colorsys.hsv_to_rgb(i/n, 0.9, 0.95))
            for i in range(n)
        ]

    def build_folium_map_from_precomputed(
        scenario: dict,
        depot_lat: float,
        depot_lon: float
    ):
        solution = scenario.get("solution", {})
        routes = solution.get("routes", [])
        vehicles_used = solution.get("vehicles_used", len(routes))
        total_distance_km = solution.get("total_distance_km", 0.0)
        total_time_sec = solution.get("total_time_sec", 0)
        status = solution.get("status", "UNKNOWN")

        if not routes:
            raise ValueError("No routes found in scenario.")

        m = folium.Map(
            location=[depot_lat, depot_lon], 
            zoom_start=11, 
            tiles='OpenStreetMap',
            width=1100,
            height=600
        )


        # folium.TileLayer(
        #     tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        #     attr=('&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> '
        #           'contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'),
        #     name="CartoDB Light",
        #     overlay=False,
        #     control=True,
        # ).add_to(m)

        folium.Marker(
            [depot_lat, depot_lon],
            popup=folium.Popup("<b>🏭 DEPOT</b><br/>Distribution Center", max_width=200),
            tooltip="Distribution Center",
            icon=folium.Icon(color="red", icon="warehouse", prefix="fa"),
        ).add_to(m)

        colors = _generate_colors(max(vehicles_used, len(routes)))
        plotted = set()

        for r_idx, route in enumerate(routes):
            color = colors[r_idx % len(colors)]
            fg = folium.FeatureGroup(
                name=f"Vehicle {route.get('vehicle', r_idx)} ({max(len(route.get('stops', [])) - 2, 0)} stops)",
                show=False  # <-- start unchecked
            )

            for j, stop in enumerate(route.get("stops", [])):
                if stop.get("is_depot"):
                    continue
                lat, lon = stop["lat"], stop["lon"]
                key = (lat, lon)
                if key in plotted:
                    continue
                arr = int(stop.get("arrival_time", 0))
                hh, mm = arr // 3600, (arr % 3600) // 60
                tstr = f"{hh:02d}:{mm:02d}"
                folium.Marker(
                    [lat, lon],
                    popup=folium.Popup(
                        f"<b>💊 {stop.get('name','')}</b><br/>"
                        f"Vehicle: {route.get('vehicle', r_idx)}<br/>"
                        f"Stop: {j}<br/>"
                        f"Arrival: {tstr}",
                        max_width=260,
                    ),
                    tooltip=f"{stop.get('name','')} ({tstr})",
                    icon=folium.Icon(color="blue", icon="plus-square", prefix="fa"),
                ).add_to(fg)
                plotted.add(key)

            for seg in route.get("segments", []):
                geom = seg.get("geometry", [])
                if not geom:
                    continue
                pl = folium.PolyLine(
                    locations=geom, color=color, weight=3, opacity=0.7,
                    popup=f"Vehicle {route.get('vehicle', r_idx)}: "
                          f"{seg.get('start',{}).get('name','?')} → {seg.get('end',{}).get('name','?')}"
                ).add_to(fg)
                if len(geom) >= 2:
                    plugins.PolyLineTextPath(
                        pl, "  ►  ", repeat=True, offset=7,
                        attributes={"fill": color, "font-weight": "bold", "font-size": "10"},
                    ).add_to(fg)

            fg.add_to(m)

        folium.LayerControl(collapsed=True).add_to(m)
        return m
    return build_folium_map_from_precomputed, load_scenario


@app.cell(hide_code=True)
def _(
    DEPOT_LAT,
    DEPOT_LON,
    DataURLs,
    build_folium_map_from_precomputed,
    folium,
    load_scenario,
    mo,
    sc,
):
    resultsBaseSlide = sc.create_slide(
        "What do the optimal routes look like",
        layout_type="1-column",
        page_number=23
    )

    file_path = f"{DataURLs.BASE}/routes/scenario_50_02_10.json"
    scenario_base_case = load_scenario(file_path)
    _m = build_folium_map_from_precomputed(scenario_base_case, DEPOT_LAT, DEPOT_LON)
    _m.add_to(folium.Figure(width="100%", height=520))  # fixed height so the map fits on the slide

    # --- LEFT COLUMN: bullets (edit text if needed) ---
    resultsBaseSlide.content1 = mo.vstack(
        [
            mo.hstack(
                [
                    mo.md('Catchment radius: **50 km**'),
                    mo.md('Delivery time window per customer: **2 hours**'),
                    mo.md('Service time per stop: **10 minutes**')
                ]
            ),
            _m
        ]
    )

    resultsBaseSlide.render()
    return


@app.cell(hide_code=True)
def _(df_scenarios, pl):
    base_case_data = df_scenarios.filter(
        (pl.col('radius_km') == 50) & (pl.col('client_tw_hours') == 2) & (pl.col('service_time_sec') == 600)
    )

    base_vehicles = base_case_data['vehicles_used'].item()
    base_total_distance_km = base_case_data['total_distance_km'].item()
    base_total_time_min = base_case_data['total_time_sec'].item()/60
    base_total_stops = base_case_data['pharmacies_count'].item()

    avg_dist_per_vehicle = base_total_distance_km/base_vehicles
    avg_time_per_vehicle = base_total_time_min/base_vehicles
    avg_stops_per_vehicle = base_total_stops/base_vehicles

    def _fmt(x, unit=None, nd=1):
        if x is None:
            return "—"
        if isinstance(x, float):
            x = round(x, nd)
        return f"{x}{(' ' + unit) if unit else ''}"

    kpi_rows = [
        {"KPI": "Number of vehicles used", "Base case": _fmt(base_vehicles)},
        {"KPI": "Total distance",          "Base case": _fmt(base_total_distance_km, "km", nd=1)},
        {"KPI": "Total time",              "Base case": _fmt(base_total_time_min, "min", nd=0)},
        {"KPI": "Avg distance / vehicle",  "Base case": _fmt(avg_dist_per_vehicle, "km", nd=1)},
        {"KPI": "Avg tour time / vehicle", "Base case": _fmt(avg_time_per_vehicle, "min", nd=0)},
        {"KPI": "Avg stops / vehicle",     "Base case": _fmt(avg_stops_per_vehicle, nd=1)},
    ]
    return (kpi_rows,)


@app.cell(hide_code=True)
def _(kpi_rows, mo, sc):
    relevantKPISlide = sc.create_slide(
        "Relevant performance indicators",
        layout_type="side-by-side",
        page_number=24
    )

    relevantKPISlide.content1 = mo.md(
        r"""
        To compate different parameter configurations we need a quick way to compare solutions. We can use **K**ey **P**erformance **I**ndicators (KPIs) to get a good summary of our results.

        **KPIs we’ll use**
        - **Vehicles used**: fleet size required to serve all stops
        - **Total distance (km)**: sum of driven kilometers across all routes
        - **Total time (min)**: total driving + service time across all routes
        - **Avg distance per vehicle**: average distance a vehicle has to drive
        - **Avg tour time per vehicle**: average time a vehicle has to drive
        - **Avg stops per vehicle**: average number of pharmacies served per vehicle
        """
    )

    # You can replace the table with KPI tiles later if you prefer
    relevantKPISlide.content2 = mo.vstack(
        [
            mo.md("**Base Case — KPIs**"),
            mo.ui.table(kpi_rows, show_column_summaries=False, show_data_types=False, selection=None)
        ],
        gap=2,
    )

    relevantKPISlide.render()
    return


@app.cell(hide_code=True)
def _(alt, df_scenarios, pd, pl):
    # Cost scenarios: price the precomputed OR-Tools solutions with three cost rates.
    # Base case: 50 km radius, 07:00-09:00 window, 10 min per stop; illustrative cost rates.
    BASE_SCENARIO = {"radius": 50, "window": 2, "service": 10, "van": 100, "hour": 30, "km": 0.30}
    DELIVERY_DAYS = 250  # delivery days per year

    def run_scenario(p: dict) -> dict:
        """Look up the OR-Tools solution for (radius, window, service) and compute its daily cost."""
        _row = df_scenarios.filter(
            (pl.col("radius_km") == p["radius"])
            & (pl.col("client_tw_hours") == p["window"])
            & (pl.col("service_time_sec") == p["service"] * 60)
        ).row(0, named=True)
        vans = _row["vehicles_used"]
        km = _row["total_distance_km"]
        hours = _row["total_time_sec"] / 3600
        pharmacies = _row["pharmacies_count"]
        cost_vans, cost_hours, cost_km = vans * p["van"], hours * p["hour"], km * p["km"]
        total = cost_vans + cost_hours + cost_km
        return {
            "pharmacies": pharmacies, "vans": vans, "km": km, "hours": hours,
            "cost_vans": cost_vans, "cost_hours": cost_hours, "cost_km": cost_km,
            "total": total, "per_delivery": total / pharmacies, "per_year": total * DELIVERY_DAYS,
        }

    def cost_breakdown_chart(cases: dict, height: int, width: int = 430):
        """Stacked bars: daily cost split into vans, driver hours and kilometres for each case."""
        _components = [("Vans", "cost_vans"), ("Driver hours", "cost_hours"), ("Kilometres", "cost_km")]
        _rows = [
            {"case": _case, "component": _label, "order": _i, "cost": round(_res[_key])}
            for _case, _res in cases.items()
            for _i, (_label, _key) in enumerate(_components)
        ]
        return (
            alt.Chart(pd.DataFrame(_rows))
            .mark_bar()
            .encode(
                y=alt.Y("case:N", title=None, sort=list(cases)),
                x=alt.X("sum(cost):Q", title="Cost per day (€)"),
                color=alt.Color(
                    "component:N", title=None, sort=[c[0] for c in _components],
                    scale=alt.Scale(range=["#1e3a8a", "#60a5fa", "#f59e0b"]),
                    legend=alt.Legend(orient="bottom"),
                ),
                order=alt.Order("order:Q"),
                tooltip=[alt.Tooltip("case:N", title="Case"), alt.Tooltip("component:N", title="Cost block"),
                         alt.Tooltip("cost:Q", title="€ per day", format=",")],
            )
            .properties(width=width, height=height)
        )

    base_scenario = run_scenario(BASE_SCENARIO)
    return (
        BASE_SCENARIO,
        DELIVERY_DAYS,
        base_scenario,
        cost_breakdown_chart,
        run_scenario,
    )


@app.cell(hide_code=True)
def _(mo):
    cost_reset_button = mo.ui.button(label="↺ Reset", value=0, on_click=lambda v: v + 1)
    return (cost_reset_button,)


@app.cell(hide_code=True)
def _(BASE_SCENARIO, cost_reset_button, mo):
    cost_reset_button.value  # clicking "reset" re-creates the sliders with their base values

    _settings = {  # key: (label, start, stop, step)
        "radius": ("Catchment radius (km)", 5, 75, 5),
        "window": ("Time window from 07:00 (h)", 2, 10, 1),
        "service": ("Service time per stop (min)", 1, 10, 1),
        "van": ("Cost per van and day (€)", 0, 300, 5),
        "hour": ("Cost per driver hour (€)", 0, 80, 5),
        "km": ("Cost per km (€)", 0.0, 1.0, 0.05),
    }
    cost_sliders = mo.ui.dictionary({
        _key: mo.ui.slider(start=_start, stop=_stop, step=_step, value=BASE_SCENARIO[_key],
                           show_value=True, debounce=True)
        for _key, (_label, _start, _stop, _step) in _settings.items()
    })
    _labels = {_key: _setting[0] for _key, _setting in _settings.items()}

    def cost_slider_row(key, labels=_labels):
        """One compact row: label on the left, slider on the right."""
        return mo.hstack(
            [mo.Html(f'<span style="font-size: 15px; color: #374151;">{labels[key]}</span>'),
             cost_sliders[key]],
            widths=[0.48, 0.52], align="center", gap=0.5,
        )
    return cost_slider_row, cost_sliders


@app.cell(hide_code=True)
def _(base_scenario, cost_breakdown_chart, cost_sliders, run_scenario, slide_table):
    cost_scenario = run_scenario(dict(cost_sliders.value))
    _b, _s = base_scenario, cost_scenario

    def _change(key):
        return f"{(_s[key] / _b[key] - 1) * 100:+.0f} %" if _b[key] else "–"

    cost_kpi_table = slide_table(
        f"""
    | | Base case | Scenario | Change |
    |:---|---:|---:|---:|
    | Pharmacies | {_b['pharmacies']} | **{_s['pharmacies']}** | {_change('pharmacies')} |
    | Vans | {_b['vans']} | **{_s['vans']}** | {_change('vans')} |
    | Stops per van | {_b['pharmacies'] / _b['vans']:.1f} | **{_s['pharmacies'] / _s['vans']:.1f}** | |
    | Kilometres | {_b['km']:,.0f} | **{_s['km']:,.0f}** | {_change('km')} |
    | km per pharmacy | {_b['km'] / _b['pharmacies']:.1f} | **{_s['km'] / _s['pharmacies']:.1f}** | |
    | Driver hours | {_b['hours']:.1f} | **{_s['hours']:.1f}** | {_change('hours')} |
    | Cost per day | {_b['total']:,.0f} € | **{_s['total']:,.0f} €** | {_change('total')} |
    | Cost per delivery | {_b['per_delivery']:.2f} € | **{_s['per_delivery']:.2f} €** | {_change('per_delivery')} |
    """
    )
    _cases = {"Base case": base_scenario, "Scenario": cost_scenario}
    lab_cost_chart = cost_breakdown_chart(_cases, height=80)
    panel_cost_chart = cost_breakdown_chart(_cases, height=50)
    return cost_kpi_table, lab_cost_chart, panel_cost_chart


@app.cell(hide_code=True)
def _(cost_kpi_table, cost_reset_button, cost_slider_row, mo, panel_cost_chart):
    def cost_scenario_panel(*keys):
        """Right column of a scenario slide: the relevant sliders, KPI table and cost chart."""
        return mo.vstack(
            [
                mo.vstack([cost_slider_row(k) for k in keys], gap=0.2),
                mo.hstack([mo.md("**Scenario vs. base case**"), cost_reset_button],
                          justify="space-between", align="center"),
                cost_kpi_table,
                panel_cost_chart,
            ],
            gap=0.3,
        )
    return (cost_scenario_panel,)


@app.cell(hide_code=True)
def _(DELIVERY_DAYS, base_scenario, cost_breakdown_chart, mo, sc, slide_table):
    costModelSlide = sc.create_slide(
        'What does a delivery day cost?',
        layout_type='side-by-side',
        page_number=25
    )

    costModelSlide.content1 = mo.vstack([
        mo.md(
            r"""
        So far we compared solutions by vans, kilometres and hours. To decide,
        Phoenix needs **one number: cost**.

        We price each OR-Tools solution with three cost rates
        (illustrative assumptions):
        """
        ),
        slide_table(
            """
        | Cost rate | Base case | Examples |
        |:---|---:|:---|
        | per van and day | 100 € | leasing, insurance, tax, cooling box, driver's fixed pay |
        | per driver hour | 30 € | driver wage incl. social security (driving + service time) |
        | per km | 0.30 € | fuel, tyres, maintenance, repairs |
        """
        ),
        mo.md(
            r"""

        $$
        \text{cost per day} = \text{vans} \cdot c_{\text{van}} + \text{hours} \cdot c_{\text{hour}} + \text{km} \cdot c_{\text{km}}
        $$

        **Think about it:** Which cost block is the largest – and which
        KPI drives it?
        """
        ),
    ], gap=1)

    _b = base_scenario
    costModelSlide.content2 = mo.vstack(
        [
            mo.md("**Base case** – 50 km radius, window 07:00–09:00, 10 min per stop"),
            slide_table(
                f"""
            | KPI | Base case |
            |:---|---:|
            | Vans | {_b['vans']} |
            | Kilometres | {_b['km']:,.0f} km |
            | Driver hours | {_b['hours']:.1f} h |
            | **Cost per day** | **{_b['total']:,.0f} €** |
            | **Cost per delivery** | **{_b['per_delivery']:.2f} €** |
            | Cost per year ({DELIVERY_DAYS} delivery days) | {_b['per_year'] / 1e6:.1f} M€ |
            """
            ),
            cost_breakdown_chart({"Base case": base_scenario}, height=40),
        ],
        gap=1,
    )

    costModelSlide.render()
    return


@app.cell(hide_code=True)
def _(cost_kpi_table, cost_reset_button, cost_slider_row, lab_cost_chart, mo, sc):
    costLabSlide = sc.create_slide(
        'Scenario lab: change the delivery policy and the costs',
        layout_type='side-by-side',
        page_number=26
    )

    costLabSlide.content1 = mo.vstack(
        [
            mo.md("**Delivery policy**"),
            cost_slider_row("radius"), cost_slider_row("window"), cost_slider_row("service"),
            mo.md("**Cost rates**"),
            cost_slider_row("van"), cost_slider_row("hour"), cost_slider_row("km"),
            cost_reset_button,
            mo.md(
                """
                Every combination of radius, time window and service time is one of the
                **1,350 OR-Tools runs** we precomputed. The lab looks up the optimal tours
                and prices them with your cost rates.
                """
            ),
        ],
        gap=0.3,
    )

    costLabSlide.content2 = mo.vstack([cost_kpi_table, lab_cost_chart], gap=0.5)

    costLabSlide.render()
    return


@app.cell(hide_code=True)
def _(cost_scenario_panel, mo, sc):
    laterWindowSlide = sc.create_slide(
        'Scenario 1: A later delivery window',
        layout_type='side-by-side',
        page_number=27
    )

    laterWindowSlide.content1 = mo.md(
        r"""
    **Situation:** Phoenix asks its pharmacies whether they would accept
    deliveries between **07:00 and 10:00** instead of 07:00–09:00.

    **1 · Predict** – How many vans can Phoenix save? Do the driver hours
    fall as much as the number of vans?

    **2 · Test** – set the time window on the right.

    **3 · Explain** – Why does the number of vans drop so much while the
    driver hours hardly move?

    **4 · Business case** – Which discount per delivery could Phoenix offer
    the pharmacies and still save money?

    **Discuss:** Why do pharmacies insist on delivery before 09:00? Which
    pharmacies would accept a later window – and what if only some of them do?
    """
    )

    laterWindowSlide.content2 = cost_scenario_panel("window")

    laterWindowSlide.render()
    return


@app.cell(hide_code=True)
def _(cost_scenario_panel, mo, sc):
    handoverSlide = sc.create_slide(
        'Scenario 2: Faster handover at the pharmacy',
        layout_type='side-by-side',
        page_number=28
    )

    handoverSlide.content1 = mo.md(
        r"""
    **Situation:** Today a driver needs about **10 minutes** per pharmacy:
    park, carry the totes inside, get a signature, collect empties. With
    pre-sorted totes and a scan instead of a signature, Phoenix could cut
    this to **5 minutes**.

    **1 · Predict** – Which saves more: this or the later window from Scenario 1?

    **2 · Test** – reset, then set the service time on the right.

    **3 · Explain** – Compare vans, driver hours and kilometres with Scenario 1.

    **4 · Dig deeper** – With night drop boxes, the driver puts the totes into a
    secure box at the pharmacy (≈ 2 min) and the time window no longer matters.
    Approximate this with the longest window (10 h). How many vans are left?

    **Discuss:** Who should pay for the drop boxes – and who carries the risk
    if medicines are stolen or get too warm?
    """
    )

    handoverSlide.content2 = cost_scenario_panel("service", "window")

    handoverSlide.render()
    return


@app.cell(hide_code=True)
def _(cost_scenario_panel, mo, sc):
    contractSlide = sc.create_slide(
        'Scenario 3: Who pays for the time window?',
        layout_type='side-by-side',
        page_number=29
    )

    contractSlide.content1 = mo.md(
        r"""
    **Situation:** Phoenix buys its tours from courier companies. Two
    contracts are on the table – both cost about the same today
    (plus 0.30 € per km in both):

    - **Contract A:** 125 € per van and day, 0 € per driver hour
    - **Contract B:** 0 € per van, 55 € per driver hour

    **1 · Predict** – Under which contract does the later window from
    Scenario 1 (07:00–10:00) save more?

    **2 · Test** – set contract A and compare 2 h with 3 h; then contract B.

    **3 · Explain** – Which KPI drives the cost under each contract?

    **Discuss:** All tours are back at the depot by 10:00. Phoenix also runs a
    mid-day top-up (departure 11:00–11:30, page 4). What does this mean for the
    courier's vans and drivers – and which contract would the courier prefer?
    """
    )

    contractSlide.content2 = cost_scenario_panel("van", "hour", "window")

    contractSlide.render()
    return


@app.cell(hide_code=True)
def _(cost_scenario_panel, mo, sc):
    closingSlide = sc.create_slide(
        'Scenario 4: Closing a neighbouring warehouse',
        layout_type='side-by-side',
        page_number=30
    )

    closingSlide.content1 = mo.md(
        r"""
    **Situation:** Phoenix considers closing a neighbouring warehouse. Fürth
    would then serve all pharmacies within **75 km** instead of 50 km –
    592 instead of 397 pharmacies (+49 %).

    **1 · Predict** – Does the delivery cost grow by more or less than 49 %?

    **2 · Test** – reset, then set the radius on the right.

    **3 · Explain** – Compare stops per van and km per pharmacy with the base case.

    **4 · Dig deeper** – What do the additional pharmacies cost per year
    (250 delivery days)? Compare this with the fixed cost of a warehouse in
    our Spain model (≈ 0.9 M€ per year).

    **Discuss:** In the warehouse location problem we assumed: the further a
    region is from the warehouse, the fewer pharmacies fit into one tour. Do the
    VRPTW results confirm this? What is different in Spain?
    """
    )

    closingSlide.content2 = cost_scenario_panel("radius")

    closingSlide.render()
    return


@app.cell(hide_code=True)
def _(cost_scenario_panel, mo, sc):
    technologyVanSlide = sc.create_slide(
        'Scenario 5: New technologies',
        layout_type='side-by-side',
        page_number=31
    )

    technologyVanSlide.content1 = mo.md(
        r"""
    **Situation:** Two technologies could change Phoenix's last mile:
    **electric vans** today and **autonomous vans** in a few years.

    **1 · Translate** – Which cost rates and which delivery parameters does
    each technology change – and in which direction?

    **2 · Build your scenario** – set the sliders for one of them.

    **3 · Defend it** – Compare with your neighbours. Why do you end up with
    different costs?

    **Discuss:** An autonomous van has no driver. Who carries the totes into
    the pharmacy – and what does this mean for the service time and the
    time window?
    """
    )

    technologyVanSlide.content2 = cost_scenario_panel("van", "hour", "km", "service")

    technologyVanSlide.render()
    return


@app.cell(hide_code=True)
def _(df_scenarios, mo, pl):
    x_param_choice = mo.ui.dropdown(
        options=["Time window (h)", "Service time (min)", "Radius (km)"],
        value="Time window (h)",
        label="x-axis"
    )

    y_kpi_choice = mo.ui.dropdown(
        options=["Vehicles", "Distance", "Time"],
        value="Distance",
        label="KPI"
    )

    # Integer domains for clean ticks
    tw_vals_all = sorted(int(v) for v in df_scenarios.select(pl.col("client_tw_hours").cast(pl.Int64)).unique().to_series().to_list())
    st_vals_all = sorted(int(v) for v in df_scenarios.select((pl.col("service_time_sec") // 60).alias("service_time_min")).unique().to_series().to_list())
    ra_vals_all = sorted(int(v) for v in df_scenarios.select(pl.col("radius_km").cast(pl.Int64)).unique().to_series().to_list())

    # Sliders to FIX the two non-x parameters (base-case defaults)
    tw_fix_slider = mo.ui.slider(start=min(tw_vals_all), stop=max(tw_vals_all), step=1, value=2,  label="Time window")
    st_fix_slider = mo.ui.slider(start=min(st_vals_all), stop=max(st_vals_all), step=1, value=10, label="Service time")
    ra_fix_slider = mo.ui.slider(start=min(ra_vals_all), stop=max(ra_vals_all), step=5, value=50, label="Radius")
    return (
        ra_fix_slider,
        st_fix_slider,
        tw_fix_slider,
        x_param_choice,
        y_kpi_choice,
    )


@app.cell(hide_code=True)
def _(
    alt,
    df_scenarios,
    pl,
    ra_fix_slider,
    st_fix_slider,
    tw_fix_slider,
    x_param_choice,
    y_kpi_choice,
):
    df_all = (
        df_scenarios
        .with_columns(
            (pl.col("service_time_sec") // 60).alias("service_time_min"),
            (pl.col("total_time_sec") / 60).alias("total_time_min"),
        )
        .select(
            "client_tw_hours", "service_time_min", "radius_km",
            "vehicles_used", "total_distance_km", "total_time_min", "pharmacies_count"
        )
    )

    axis_key_map = {
        "Time window (h)": "client_tw_hours",
        "Service time (min)": "service_time_min",
        "Radius (km)": "radius_km",
    }
    kpi_field_map = {
        "Vehicles": ("vehicles_used", "Vehicles (count)"),
        "Distance": ("total_distance_km", "Total distance (km)"),
        "Time": ("total_time_min", "Total time (min)"),
    }
    x_title_map = {
        "client_tw_hours": "Time window (hours)",
        "service_time_min": "Service time (min)",
        "radius_km": "Radius (km)",
    }

    x_key = axis_key_map[x_param_choice.value]
    y_field, y_title = kpi_field_map[y_kpi_choice.value]
    x_title = x_title_map[x_key]

    y_max_global = float(df_all.select(pl.max(y_field)).to_series().item())
    y_domain = [0, y_max_global if y_max_global > 0 else 1.0]

    fixed_values = {
        "client_tw_hours": tw_fix_slider.value,
        "service_time_min": st_fix_slider.value,
        "radius_km": ra_fix_slider.value,
    }
    other_keys = [k for k in ["client_tw_hours", "service_time_min", "radius_km"] if k != x_key]
    expr = (pl.col(other_keys[0]) == fixed_values[other_keys[0]]) & (pl.col(other_keys[1]) == fixed_values[other_keys[1]])

    df_line = (
        df_all
        .filter(expr)
        .group_by(x_key)
        .agg(pl.mean(y_field).alias(y_field))
        .sort(x_key)
    )

    x_vals = df_line.select(pl.col(x_key)).to_series().to_list()
    if len(x_vals) == 0:
        x_ticks, x_domain = [], [0, 1]
    else:
        x_min, x_max = int(min(x_vals)), int(max(x_vals))
        x_ticks = list(range(x_min, x_max + 1))
        x_domain = [x_min, x_max]

    line_chart = (
        alt.Chart(df_line)
        .mark_line(point=True)
        .encode(
            x=alt.X(
                f"{x_key}:Q",
                title=x_title,
                scale=alt.Scale(domain=x_domain, nice=False),
                axis=alt.Axis(values=x_ticks, tickMinStep=1),
            ),
            y=alt.Y(
                f"{y_field}:Q",
                title=y_title,
                scale=alt.Scale(domain=y_domain, nice=False),
            ),
            tooltip=[
                alt.Tooltip(f"{x_key}:Q", title=x_title),
                alt.Tooltip(
                    f"{y_field}:Q",
                    title=y_title,
                    format=".1f" if y_field != "vehicles_used" else ""
                ),
            ],
        )
        .properties(width=500, height=300, title=f"{y_title} vs. {x_title}")
    )
    return line_chart, x_key


@app.cell(hide_code=True)
def _(
    line_chart,
    mo,
    ra_fix_slider,
    sc,
    st_fix_slider,
    tw_fix_slider,
    x_key,
    x_param_choice,
    y_kpi_choice,
):
    oneParamSensitivitySlide = sc.create_slide(
        "Sensitivity analysis: the whole range of each lever",
        layout_type="side-by-side",
        page_number=32
    )

    oneParamSensitivitySlide.content1 = mo.md(
        r"""
        The scenarios tested **single changes**. A **sensitivity analysis** varies one lever over its
        **whole range** while holding the others fixed – e.g. the time window from 2 h to 10 h. This shows
        where extra flexibility stops paying off (**diminishing returns**).

        **What this helps us decide**
        - **Service promise vs. cost:** quantify how stricter delivery windows shift vehicles and time.
        - **Process improvements:** estimate the payoff from shaving minutes off on-site handling.
        - **Coverage policy:** see when expanding the radius stops paying off (diminishing returns).

        **Takeaway**  
        Use these simulations to pick **cost-effective policies** and to set **guardrails**
        (e.g., minimum window length, maximum service time, or radius limits) that keep operations stable.
        """
    )

    if x_key == "client_tw_hours":
        fix_controls = mo.hstack([st_fix_slider, ra_fix_slider], gap=2)
    elif x_key == "service_time_min":
        fix_controls = mo.hstack([tw_fix_slider, ra_fix_slider], gap=2)
    else:  # radius_km on x
        fix_controls = mo.hstack([tw_fix_slider, st_fix_slider], gap=2)

    oneParamSensitivitySlide.content2 = mo.vstack(
        [
            mo.hstack([x_param_choice, y_kpi_choice], gap=2),
            fix_controls,
            line_chart,
        ],
        gap=2,
    )

    oneParamSensitivitySlide.render()
    return


@app.cell(hide_code=True)
def _(mo, sc):
    sessionWrapSlide = sc.create_slide(
        "Session Wrap-Up — VRPTW with Phoenix (Fulfilment)",
        layout_type="side-by-side",
        page_number=33
    )

    sessionWrapSlide.content1 = mo.md(
        r"""
        **What we set out to do**
        - Figure out how Phoenix can **fulfil** customer orders in a **cost-efficient** way
        - Learn how to find **efficient last-mile routes** within a given distribution network

        **What you learned**
        - Translate business rules into a **VRPTW** formulation  
          (objective, flow, capacity, time-window timing)
        - Build a **parameterized dataset** (customers, depot, matrices, fleet) **from realistic data**
        - Read and communicate **KPIs**: vehicles, km, minutes, and per-vehicle averages
        - Price solutions and compare **service policies** in scenarios
        """
    )

    sessionWrapSlide.content2 = mo.vstack(
        [
            mo.md(
                r"""
                **Skills you practiced**
                - Turning an operations narrative into a **formal model**
                - Running **sensitivity analyses** and interpreting KPIs
                """
            ),
            mo.md(
                r"""
                **Takeaways for practice**
                - Start with a **base case**, vary one lever, **hold others fixed**
                - Tie findings to **operational policies** customers **experience** (windows, handling)
                """
            ),
            mo.md(
                r"""
                **What’s next**
                - Connect routing back to **network design**: how many warehouses does Phoenix need if every tour is planned like this?
                - Reproduce the analysis with the repo (class notebook + data + plots)
                """
            ),
        ],
        gap=2,
    )


    sessionWrapSlide.render()
    return


if __name__ == "__main__":
    app.run()
