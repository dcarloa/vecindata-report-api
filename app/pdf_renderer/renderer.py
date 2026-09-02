import threading
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

_TEMPLATE_DIR = Path(__file__).parent / "templates"

# Each render_pdf() call launches a full Chromium process. Cloud Run can route
# several concurrent requests to the same container instance, and unbounded
# simultaneous Chromium launches compete for that instance's fixed CPU/memory
# until render time blows up (observed in production: a normal 12-50s render
# stretched to 272s/281s under 3 concurrent requests, with a later request
# hitting a hard 504 at Cloud Run's 300s timeout). Capping concurrent renders
# at 2 (matching the service's 2 vCPU) keeps each render fast regardless of
# how many requests land on the instance at once.
_MAX_CONCURRENT_RENDERS = 2
_render_semaphore = threading.Semaphore(_MAX_CONCURRENT_RENDERS)


def render_html(report: dict) -> str:
    env = Environment(loader=FileSystemLoader(_TEMPLATE_DIR), autoescape=True)
    template = env.get_template("report.html.jinja")
    return template.render(**report)


def render_pdf(report: dict) -> bytes:
    html = render_html(report)
    with _render_semaphore:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page()
                page.set_content(html)
                pdf_bytes = page.pdf(
                    format="A4",
                    print_background=True,
                    margin={"top": "18mm", "bottom": "16mm", "left": "16mm", "right": "16mm"},
                )
            finally:
                browser.close()
    return pdf_bytes
