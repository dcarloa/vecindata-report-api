from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

_TEMPLATE_DIR = Path(__file__).parent / "templates"


def render_html(report: dict) -> str:
    env = Environment(loader=FileSystemLoader(_TEMPLATE_DIR), autoescape=True)
    template = env.get_template("report.html.jinja")
    return template.render(**report)


def render_pdf(report: dict) -> bytes:
    html = render_html(report)
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
