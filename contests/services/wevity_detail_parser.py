import re
from urllib.parse import unquote, urljoin, urlparse

from bs4 import BeautifulSoup

from contests.services.prefill_detail_parser import (
    clean_text,
    classify_content_from_extracted,
    find_dates,
    find_url_by_labels,
    find_value_by_labels,
    guess_title_from_html,
    label_matches,
)
from contests.utils.extractor.image_extractor import extract_images
from contests.utils.extractor.text_extractor import extract_text_content


ATTACHMENT_LABELS = ["첨부파일", "첨부 파일", "attachment"]
FILE_EXTENSIONS = [
    "pdf",
    "hwp",
    "hwpx",
    "doc",
    "docx",
    "zip",
    "xlsx",
    "xls",
    "ppt",
    "pptx",
]
FILE_EXT_RE = "|".join(FILE_EXTENSIONS)
FILE_NAME_PATTERN = re.compile(rf"([^/\\?&\s]+\.(?:{FILE_EXT_RE}))", re.IGNORECASE)


def get_contest_detail_node(soup):
    # 위비티 상세 페이지의 실질 데이터는 .contest-detail 내부에 모여 있다.
    # 이 범위를 먼저 좁혀두면 헤더/푸터/사이드바/SNS 버튼을 훑지 않아도 된다.
    return soup.select_one("div.contest-detail") or soup


def get_info_node(contest_detail):
    # .info에는 요약 메타가 있다.
    # 분야, 응모대상, 주최/주관, 후원/협찬, 접수기간, 상금, 홈페이지, 첨부파일을 여기서 찾는다.
    return contest_detail.select_one("div.info") or contest_detail


def get_article_node(contest_detail):
    # .article은 "상세내용" 본문이 시작되는 영역이다.
    # description과 image_urls는 이 영역에서만 추출한다.
    return contest_detail.select_one("div.article") or contest_detail


def node_to_html(node):
    return str(node) if node else ""


def find_wevity_attachment_node(info_node):
    # 첨부파일은 상세내용(.article)이 아니라 요약(.info)에 있다.
    # "파일없음"이면 빈 리스트를 반환하고, 다운로드 링크가 있으면 그 링크만 처리한다.
    for node in info_node.select("li, tr, dt, p, div"):
        text = clean_text(node.get_text(" ", strip=True))
        if label_matches(text[:80], ATTACHMENT_LABELS):
            return node
    return None


def is_empty_attachment_text(text):
    normalized = clean_text(text)
    return "파일없음" in normalized or "파일 없음" in normalized


def iter_link_candidates(link):
    # 위비티 첨부 링크는 href가 javascript:void(0)이고,
    # 실제 다운로드 경로가 onclick 또는 data-* 속성에 들어가는 경우가 있다.
    raw_values = [
        link.get("href", ""),
        link.get("onclick", ""),
        link.get("data-url", ""),
        link.get("data-href", ""),
        link.get("data-file", ""),
    ]

    for raw_value in raw_values:
        value = clean_text(raw_value)
        for quoted in re.findall(r"""['"]([^'"]+)['"]""", value):
            yield clean_text(quoted)
        if value:
            yield value


def looks_like_download_target(value):
    lower_value = (value or "").lower()
    if not lower_value or lower_value in {"#", "javascript:void(0)", "void(0)"}:
        return False
    if lower_value.startswith("javascript:void"):
        return False
    if re.match(r"^\w+\s*\(", lower_value):
        return False
    if FILE_NAME_PATTERN.search(lower_value):
        return True
    return (
        "download" in lower_value
        or "file" in lower_value
        or lower_value.startswith(("/", "http://", "https://"))
    )


def extract_file_name(file_url, link_text):
    # 링크 텍스트가 파일명인 경우 우선 사용하고, 아니면 URL path에서 파일명을 추정한다.
    text_match = FILE_NAME_PATTERN.search(link_text or "")
    if text_match:
        return text_match.group(1)

    parsed = urlparse(file_url)
    path_name = unquote(parsed.path.split("/")[-1]).strip()
    if path_name:
        return path_name
    return "attachment"


def extract_wevity_files(info_node, base_url):
    node = find_wevity_attachment_node(info_node)
    if not node:
        return []

    node_text = clean_text(node.get_text(" ", strip=True))
    if is_empty_attachment_text(node_text):
        return []

    files = []
    seen_urls = set()
    for link in node.select("a"):
        link_text = clean_text(link.get_text(" ", strip=True))
        for candidate in iter_link_candidates(link):
            if not looks_like_download_target(candidate):
                continue
            file_url = urljoin(base_url, candidate)
            if file_url in seen_urls:
                continue
            seen_urls.add(file_url)
            files.append({
                "file_name": extract_file_name(file_url, link_text),
                "file_url": file_url,
            })
            break

    return files


def parse_wevity_detail_fields(html, source_url, list_meta):
    # 위비티는 .contest-detail 내부가 정형화되어 있다.
    # .info에서는 메타/첨부를, .article에서는 상세 본문/이미지만 가져온다.
    soup = BeautifulSoup(html, "html.parser")
    contest_detail = get_contest_detail_node(soup)
    info_node = get_info_node(contest_detail)
    article_node = get_article_node(contest_detail)

    info_html = node_to_html(info_node)
    article_html = node_to_html(article_node)
    info_soup = BeautifulSoup(info_html, "html.parser")

    extracted_text = extract_text_content(article_html).get("raw_text", "")
    extracted_images = extract_images(article_html, source_url)
    extracted_files = extract_wevity_files(info_node, source_url)
    detail_start_date, detail_end_date = find_dates(info_soup, extracted_text)

    title = guess_title_from_html(node_to_html(contest_detail), contest_detail)
    host_region = find_value_by_labels(
        info_soup,
        ["지역", "장소", "개최지역", "시행지역", "활동지역", "소재지", "region"],
    )
    category = find_value_by_labels(
        info_soup,
        ["분야", "공모분야", "사업분야", "카테고리", "category", "분류"],
    )
    eligibility = find_value_by_labels(
        info_soup,
        ["자격", "대상", "응모대상", "참가대상", "지원자격", "eligibility"],
    )
    organizer = find_value_by_labels(
        info_soup,
        ["주최/주관", "주최주관", "주최사", "주최기관", "주관기관", "주최", "주관", "organizer"],
    )
    total_prize = find_value_by_labels(
        info_soup,
        ["총 상금", "총상금", "시상내역"],
    )
    first_prize = find_value_by_labels(
        info_soup,
        ["1등 상금", "1등상금", "대상 상금", "대상상금"],
    )
    detail_url = find_url_by_labels(
        info_soup,
        ["홈페이지", "공식홈페이지", "url", "website"],
    )

    content_type = classify_content_from_extracted(
        extracted_text=extracted_text,
        extracted_images=extracted_images,
        extracted_files=extracted_files,
    )

    return {
        "title": title,
        "host_region": host_region,
        "organizer": organizer,
        "total_prize": total_prize,
        "first_prize": first_prize,
        "detail_url": detail_url,
        "category": category,
        "eligibility": eligibility,
        "start_date": detail_start_date,
        "end_date": detail_end_date,
        "description": extracted_text,
        "content_type": content_type,
        "image_urls": "\n".join(extracted_images),
        "attachment_lines": "\n".join(
            f"{item['file_name']} | {item['file_url']}" for item in extracted_files
        ),
    }
