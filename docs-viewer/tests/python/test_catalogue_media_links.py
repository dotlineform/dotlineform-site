"""Generated Catalogue identity, media safety and inline token Build boundaries."""

import json
from pathlib import Path
import sys

from bs4 import BeautifulSoup
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "build"))

from docs_builder.pipeline import DocsDataBuilder
from docs_builder.semantic_tokens import parse_catalogue_token
from docs_builder.semantic_token_registry import load_semantic_token_registry
from docs_catalogue_media import catalogue_media_record, read_catalogue_media_targets, read_catalogue_work
from docs_management_read_service import docs_management_get_payload
import docs_management_routes as routes
from docs_scope_config import load_docs_scope_configs
from repo_factory import docs_scope_record, write_docs_scope_config, write_json, write_site_tools_config, write_text

REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_ID = "d-20260909-120000-000001"
MEDIA_URL = "https://media.example.test/explicit/image.webp?v=2"


@pytest.fixture
def catalogue(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    base = tmp_path / "projects"
    generated = base / "catalogue/generated"
    work = {
        "work_id": "00523", "title": 'A *Work* </script><img src=x onerror="bad">',
        "year_display": "2023", "width_px": 2400, "height_px": 1800, "documents": [],
        "media": {"primary": [{"url": MEDIA_URL, "width": 1600}]},
    }
    write_json(generated / "works/works_index.json", {"works": {"00523": work}})
    write_json(generated / "works/index/00523.json", {"work": work})
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(base))
    write_site_tools_config(root)
    write_docs_scope_config(root, [docs_scope_record("studio")])
    registry_path = "docs-viewer/config/semantic-tokens/registry.json"
    write_text(root / registry_path, (REPO_ROOT / registry_path).read_text())
    routes_path = "docs-viewer/config/routes/docs-viewer-routes.json"
    write_text(root / routes_path, (REPO_ROOT / routes_path).read_text())
    return root, generated, work


def test_local_routes_read_generated_data_without_documents_or_archive(catalogue):
    root, _, work = catalogue
    result = docs_management_get_payload(root, routes.CATALOGUE_MEDIA_TARGETS_PATH, {})
    assert result["targets"] == [{"family": "catalogue", "target_type": "work", "target_id": "00523",
                                  "title": work["title"], "meta": ["2023"]}]
    result = docs_management_get_payload(root, routes.CATALOGUE_WORK_PATH, {"work_id": ["00523"]})
    assert result["work"] == work
    assert result["work"]["media"]["primary"][0]["url"] == MEDIA_URL
    work["title"] = "Changed since the document was built"
    write_json(catalogue[1] / "works/index/00523.json", {"work": work})
    assert docs_management_get_payload(root, routes.CATALOGUE_WORK_PATH, {"work_id": ["00523"]})["work"]["title"] == work["title"]


@pytest.mark.parametrize("work_id", ["523", "../00523", "00524", "00523 "])
def test_invalid_or_unavailable_work_is_not_substituted(catalogue, work_id):
    root, _, _ = catalogue
    with pytest.raises(ValueError):
        read_catalogue_work(root, work_id)


@pytest.mark.parametrize("url", ["//evil.test/x", "javascript:alert(1)", "https://user:pass@example.test/x", "https://safe.test\\@evil.test/x", "http://example.test/x"])
def test_unsafe_generated_media_is_rejected(catalogue, url):
    root, generated, work = catalogue
    work["media"]["primary"][0]["url"] = url
    write_json(generated / "works/index/00523.json", {"work": work})
    with pytest.raises(ValueError, match="unsafe"):
        catalogue_media_record(read_catalogue_work(root, "00523"), "00523")


def test_mismatched_record_and_escaped_workspace_are_rejected(catalogue, tmp_path):
    root, generated, work = catalogue
    work["work_id"] = "00524"
    record = generated / "works/index/00523.json"
    write_json(record, {"work": work})
    with pytest.raises(ValueError, match="does not match"):
        read_catalogue_work(root, "00523")
    outside = tmp_path / "outside.json"
    record.rename(outside)
    record.symlink_to(outside)
    with pytest.raises(ValueError, match="unavailable"):
        read_catalogue_work(root, "00523")
    write_json(generated / "works/works_index.json", {"works": {"00523": work}})
    with pytest.raises(ValueError, match="identity"):
        read_catalogue_media_targets(root)


def build_document(root, body, *, scope="studio"):
    source = root / f"docs-viewer/scopes/{scope}/source/documents/{DOC_ID}.md"
    write_text(source, f'---\ndoc_id: {DOC_ID}\ntitle: Invoking document\nadded_date: "2026-09-09 12:00:00"\n---\n{body}\n')
    builder = DocsDataBuilder(repo_root=root, config=load_docs_scope_configs(root)[scope], skip_media_builds=True)
    builder.run(write=True)
    payload = json.loads((root / f"docs-viewer/scopes/{scope}/generated/documents/by-id/{DOC_ID}.json").read_text())
    return payload["content_html"], builder.warnings


def test_build_preserves_only_authored_text_and_independent_references(catalogue):
    root, generated, work = catalogue
    source = r'Before [[catalogue:media:work:00523|A *literal* \| label]] and [[catalogue:media:work:00523|second]] after.'
    content, warnings = build_document(root, source)
    soup = BeautifulSoup(content, "html.parser")
    markers = soup.select('[data-docs-content-detail="media"]')
    assert len(markers) == 2
    assert soup.p.get_text() == "Before A *literal* | label and second after."
    assert not soup.select("img, em, script")
    for marker in markers:
        assert marker["data-docs-media-kind"] == "catalogue-work"
        assert marker["data-docs-media-id"] == "00523"
        assert marker.button["type"] == "button"
        assert "href" not in marker.button.attrs
    assert work["title"] not in content and MEDIA_URL not in content
    assert not warnings
    (generated / "works/index/00523.json").unlink()
    assert build_document(root, source)[0] == content


def test_public_scope_build_preserves_media_activation_without_management(catalogue):
    root, _, _ = catalogue
    write_docs_scope_config(root, [docs_scope_record("example", scope_type="public", viewer_base_url="/analysis/", include_scope_param=False)])
    content, warnings = build_document(root, "[[catalogue:media:work:00523|Public link]]", scope="example")
    marker = BeautifulSoup(content, "html.parser").select_one('[data-docs-content-detail="media"]')
    assert marker["data-docs-media-id"] == "00523"
    assert marker.select_one("button[data-docs-media-open]").get_text() == "Public link"
    assert not warnings


def test_missing_work_retains_a_live_reference_and_code_tokens_remain_literal(catalogue):
    root, _, _ = catalogue
    missing = "[[catalogue:media:work:00524|Missing]]"
    literal = "[[catalogue:media:work:00523|Code]]"
    content, warnings = build_document(root, f"{missing}\n\n`{literal}`\n\n```text\n{literal}\n```\n")
    soup = BeautifulSoup(content, "html.parser")
    assert soup.button.get_text() == "Missing"
    assert len(soup.select('[data-docs-media-open]')) == 1
    assert all(code.get_text().strip() == literal for code in soup.select("code"))
    assert not warnings


@pytest.mark.parametrize("prefix, container_selector", [("", "p"), ("- ", "li")])
@pytest.mark.parametrize("token", [
    "[[catalogue:media:work:00523|*literal*]]",
    "[[catalogue:image:work:00523|alt=%2Aliteral%2A]]",
])
def test_leading_inline_media_preserves_surrounding_markdown(catalogue, prefix, container_selector, token):
    root, _, _ = catalogue
    content, warnings = build_document(
        root, prefix + token + " followed by **bold** and [a link](https://example.com).",
    )
    soup = BeautifulSoup(content, "html.parser")
    container = soup.select_one(container_selector)
    assert not warnings
    assert container is not None
    assert container.get_text().strip() == "*literal* followed by bold and a link."
    assert container.strong.get_text() == "bold"
    assert container.a["href"] == "https://example.com"
    assert container.button.get_text() == "*literal*"
    assert not container.button.select("em, strong")
    assert container.select_one('[data-docs-media-id="00523"]') is not None


def test_media_parser_requires_explicit_presentation_and_exact_work_target(catalogue):
    root, _, _ = catalogue
    registry = load_semantic_token_registry(root)
    assert parse_catalogue_token("[[catalogue:work:00523|Unqualified]]", registry=registry) is None
    assert parse_catalogue_token("[[catalogue:media:work:00523|New]]", registry=registry).presentation == "media"
    for raw in ("[[catalogue:media:series:143|Series]]", "[[catalogue:media:work:523|Short]]"):
        assert parse_catalogue_token(raw, registry=registry) is None


def test_broken_links_uses_generated_media_availability(catalogue):
    from docs_broken_links import DocMeta, semantic_token_broken_entries

    root, _, _ = catalogue
    meta = DocMeta("analysis", DOC_ID, "Example", "/docs/", "working", "works")
    result = semantic_token_broken_entries(root, [(meta,
        "[[catalogue:media:work:00523|available]] [[catalogue:media:work:00524|missing]]")])
    assert len(result) == 1
    assert result[0]["target_id"] == "00524" and result[0]["reason"] == "missing_media"
    assert result[0]["from_page_stage"] == "working" and result[0]["from_page_sub_scope"] == "works"


def test_work_and_detail_images_build_only_exact_references_and_authored_presentation(catalogue):
    root, generated, _ = catalogue
    source = (
        '[[catalogue:image:work:00523|alt=A%20Work]]\n\n'
        '[[catalogue:image:work:00523|alt=Detail%20alt&detail_id=015&caption=A%20%3Ccaption%3E&summary=Line%201%0ALine%202&placement=right&fill_width=false]]\n'
    )
    content, warnings = build_document(root, source)
    soup = BeautifulSoup(content, "html.parser")
    assert not warnings
    assert len(soup.select('[data-docs-media-image]')) == 2
    assert all('src' not in image.attrs for image in soup.select('img'))
    assert not soup.select('script, a')
    detail = soup.select('[data-docs-media-kind="catalogue-work-detail"]')[0]
    assert detail.find_parent("p") is None
    assert detail['data-docs-media-id'] == '00523-015'
    assert detail['data-docs-media-work-id'] == '00523'
    assert detail.img['alt'] == 'Detail alt'
    assert 'docsViewerFigure--image-right' in detail['class']
    assert 'docsViewerFigure--natural-width' in detail['class']
    assert detail.select_one('.docsViewerFigure__caption').get_text() == 'A <caption>'
    assert detail.select_one('.docsViewerFigure__summary').get_text() == 'Line 1\nLine 2'
    (generated / 'works/index/00523.json').unlink()
    assert build_document(root, source)[0] == content


def test_detail_availability_uses_exact_generated_record_without_work_primary(catalogue):
    from docs_broken_links import DocMeta, semantic_token_broken_entries

    root, generated, work = catalogue
    work['media'] = {}
    detail = {'work_id': '00523', 'detail_id': '015', 'detail_uid': '00523-015', 'title': 'Detail',
              'width_px': 700, 'height_px': 700, 'media': {'primary': [{'url': MEDIA_URL, 'width': 700}]}}
    payload = {'work': work, 'sections': [{'details': [detail]}]}
    write_json(generated / 'works/index/00523.json', payload)
    assert catalogue_media_record(read_catalogue_work(root, '00523'), '00523', '015') == detail
    meta = DocMeta('analysis', DOC_ID, 'Example', '/docs/', 'working', 'works')
    issues = semantic_token_broken_entries(root, [(meta,
        '[[catalogue:image:work:00523|alt=Detail&detail_id=015]] [[catalogue:image:work:00523|alt=Missing&detail_id=016]]')])
    assert len(issues) == 1 and issues[0]['reason'] == 'missing_detail_image' and issues[0]['link_url'] == ''
    payload['sections'][0]['details'].append(dict(detail))
    with pytest.raises(ValueError, match='unavailable or mismatched'):
        catalogue_media_record(payload, '00523', '015')
    payload['sections'][0]['details'] = [dict(detail, work_id='00524')]
    with pytest.raises(ValueError, match='unavailable or mismatched'):
        catalogue_media_record(payload, '00523', '015')
