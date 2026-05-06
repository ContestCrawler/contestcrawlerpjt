import re
from urllib.parse import unquote, urljoin, urlparse

from bs4 import BeautifulSoup

from contests.services.parsing.common import (
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


ATTACHMENT_LABELS = ["첨부파일", "첨부 파일", "attachment", "file"]
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


def find_wevity_detail_container(soup):
    """
    Wevity 상세 HTML에서 전체 상세 컨테이너를 찾는다.

    의미:
        header/footer/sidebar 같은 주변 요소를 제외하고 상세 파싱 범위를 좁히기 위한 시작점이다.

    반환값:
        div.contest-detail node를 반환한다. 없으면 soup 전체를 fallback으로 반환한다.
    """
    return soup.select_one("div.contest-detail") or soup


def find_wevity_summary_container(contest_detail):
    """
    Wevity 상세 컨테이너 안에서 요약 정보 영역을 찾는다.

    의미:
        분야, 대상, 주최, 기간, 상금, 홈페이지, 첨부파일 같은 구조화 정보가 있는 영역이다.

    반환값:
        div.info node를 반환한다. 없으면 contest_detail 전체를 fallback으로 반환한다.
    """
    return contest_detail.select_one("div.info") or contest_detail


def find_wevity_article_container(contest_detail):
    """
    Wevity 상세 컨테이너 안에서 본문 영역을 찾는다.

    의미:
        description과 image_urls는 요약 정보가 아니라 상세 본문 영역에서 추출한다.

    반환값:
        div.article node를 반환한다. 없으면 contest_detail 전체를 fallback으로 반환한다.
    """
    return contest_detail.select_one("div.article") or contest_detail


def node_to_html(node):
    """
    BeautifulSoup node를 HTML 문자열로 변환한다.

    의미:
        extractor 함수들이 HTML 문자열을 입력으로 받기 때문에 node 단위 파싱 결과를 다시 문자열로 만든다.

    반환값:
        node가 있으면 str(node)를 반환하고, 없으면 빈 문자열을 반환한다.
    """
    return str(node) if node else ""


def find_wevity_attachment_node(info_node):
    """
    Wevity 요약 정보 영역에서 첨부파일 label이 있는 node를 찾는다.

    의미:
        첨부파일은 상세 본문이 아니라 info 영역에 들어 있으므로 별도로 탐색한다.

    반환값:
        첨부파일 label을 포함한 node를 반환한다. 찾지 못하면 None을 반환한다.
    """
    for node in info_node.select("li, tr, dt, p, div"):
        text = clean_text(node.get_text(" ", strip=True))
        if label_matches(text[:80], ATTACHMENT_LABELS):
            return node
    return None


def is_empty_attachment_text(text):
    """
    첨부파일 영역 텍스트가 '파일 없음' 상태인지 판단한다.

    의미:
        첨부파일 label은 있지만 실제 다운로드 링크가 없는 경우를 빈 첨부파일로 처리한다.

    반환값:
        파일 없음 문구로 판단되면 True, 아니면 False를 반환한다.
    """
    normalized = clean_text(text).lower()
    return "파일없음" in normalized or "파일 없음" in normalized or "no file" in normalized or "none" in normalized


def iter_link_candidates(link):
    """
    a 태그에서 다운로드 URL 후보 문자열들을 순서대로 생성한다.

    의미:
        Wevity 첨부 링크는 href뿐 아니라 onclick, data-* 속성 안에 실제 다운로드 경로가 있을 수 있다.

    반환값:
        generator로 후보 문자열을 하나씩 yield한다.
    """
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
    """
    문자열이 실제 다운로드 대상처럼 보이는지 판단한다.

    의미:
        javascript:void(0) 같은 UI 동작과 실제 파일/다운로드 URL 후보를 구분한다.

    반환값:
        파일명, download/file keyword, 절대/상대 URL 형태로 보이면 True, 아니면 False를 반환한다.
    """
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
    """
    첨부파일 URL과 링크 텍스트에서 파일명을 추정한다.

    의미:
        링크 텍스트에 파일명이 있으면 우선 사용하고, 없으면 URL path 마지막 값을 사용한다.

    반환값:
        추정한 파일명 문자열을 반환한다. 추정할 수 없으면 "attachment"를 반환한다.
    """
    text_match = FILE_NAME_PATTERN.search(link_text or "")
    if text_match:
        return text_match.group(1)

    parsed = urlparse(file_url)
    path_name = unquote(parsed.path.split("/")[-1]).strip()
    if path_name:
        return path_name
    return "attachment"


def extract_wevity_attachment_files(info_node, base_url):
    """
    Wevity 요약 정보 영역에서 첨부파일 목록을 추출한다.

    의미:
        첨부파일 node를 찾고, 그 안의 링크 후보를 실제 파일 URL과 파일명 dict로 변환한다.

    반환값:
        {"file_name": ..., "file_url": ...} dict 목록을 반환한다.
        첨부파일 영역이 없거나 파일 없음 상태이면 빈 목록을 반환한다.
    """
    node = find_wevity_attachment_node(info_node)
    # Error handling:
    # 첨부파일 label 자체가 없으면 첨부파일이 없는 상세 페이지로 처리한다.
    if not node:
        return []

    node_text = clean_text(node.get_text(" ", strip=True))
    # Error handling:
    # 파일 없음 문구가 있는 경우 링크 탐색 없이 빈 목록을 반환한다.
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
            # Error handling:
            # 같은 첨부 링크가 여러 속성에서 반복될 수 있어 URL 기준으로 중복 저장을 막는다.
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
    """
    Wevity 상세 HTML에서 Contest prefill용 필드 dict를 만든다.

    의미:
        Wevity의 고정 구조를 이용해 info 영역에서는 요약 필드/첨부파일을,
        article 영역에서는 상세 설명과 이미지를 추출한다.

    반환값:
        title, host_region, organizer, prize, detail_url, category, eligibility,
        start_date, end_date, description, content_type, image_urls,
        attachment_lines를 담은 dict를 반환한다.
    """
    soup = BeautifulSoup(html, "html.parser")
    contest_detail = find_wevity_detail_container(soup)
    info_node = find_wevity_summary_container(contest_detail)
    article_node = find_wevity_article_container(contest_detail)

    article_html = node_to_html(article_node)
    info_soup = BeautifulSoup(node_to_html(info_node), "html.parser")

    extracted_text = extract_text_content(article_html).get("raw_text", "")
    extracted_images = extract_images(article_html, source_url)
    extracted_files = extract_wevity_attachment_files(info_node, source_url)
    detail_start_date, detail_end_date = find_dates(info_soup, extracted_text)

    title = guess_title_from_html(node_to_html(contest_detail), contest_detail)
    host_region = find_value_by_labels(info_soup, ["지역", "장소", "개최지역", "활동지역", "소재지", "region", "location", "place"])
    category = find_value_by_labels(info_soup, ["분야", "공모분야", "사업분야", "카테고리", "분류", "category", "field", "type"])
    eligibility = find_value_by_labels(info_soup, ["자격", "대상", "응모대상", "참가대상", "지원자격", "eligibility", "target", "applicant"])
    organizer = find_value_by_labels(info_soup, ["주최/주관", "주최주관", "주최", "주관", "기관명", "organizer", "host", "sponsor"])
    total_prize = find_value_by_labels(info_soup, ["총상금", "총 시상금", "시상내역", "total prize", "prize"])
    first_prize = find_value_by_labels(info_soup, ["1등상금", "1등 시상금", "대상상금", "대상 시상금", "first prize", "grand prize"])
    detail_url = find_url_by_labels(info_soup, ["홈페이지", "공식홈페이지", "website", "homepage", "url"])

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
