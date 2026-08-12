import re
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "docs" / "index.html"
JAVASCRIPT_PATH = ROOT / "docs" / "assets" / "dashboard.js"


class IdParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []

    def handle_starttag(self, _tag, attrs):
        attributes = dict(attrs)
        if "id" in attributes:
            self.ids.append(attributes["id"])


def test_static_dashboard_ids_are_unique_and_cover_javascript_targets():
    parser = IdParser()
    parser.feed(HTML_PATH.read_text(encoding="utf-8"))
    html_ids = set(parser.ids)
    javascript = JAVASCRIPT_PATH.read_text(encoding="utf-8")
    referenced_ids = set(re.findall(r'byId\("([^"]+)"\)', javascript))

    assert len(parser.ids) == len(html_ids)
    assert referenced_ids <= html_ids


def test_static_dashboard_uses_relative_data_paths_for_github_pages():
    javascript = JAVASCRIPT_PATH.read_text(encoding="utf-8")

    assert 'const DATA_URL = "assets/regional_data.json"' in javascript
    assert 'const GEOGRAPHY_URL = "assets/globe_geography.json"' in javascript
