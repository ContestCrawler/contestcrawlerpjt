import re
from datetime import datetime
from urllib.parse import urlparse

from bs4 import BeautifulSoup

DATE_PATTERN = re.compile(
    r"(\d{4})[.\-/년]\s*(\d{1,2})[.\-/월]\s*(\d{1,2})(?:일)?"
)

# 위비티 상세 페이지에서는 실제 공모전 제목 아래에 요약 메타 영역이 붙어 있다.
# 이 라벨들이 보이는 위치를 기준으로 바로 앞 heading을 제목 후보로 잡는다.
SUMMARY_TITLE_LABELS = ["분야", "응모대상", "주최/주관", "접수기간"]

# 사이트 공통 섹션 제목은 실제 공모전명이 아니므로 제목 후보에서 제외한다.
NOISE_TITLES = {
    "공모전 대외활동 정보",
    "상세내용",
    "공모전 공모요강",
}


def clean_text(value):
    # 여러 줄/탭/연속 공백을 한 칸 공백으로 통일한다.
    # HTML에서 get_text()로 가져온 값은 줄바꿈이 섞이는 경우가 많다.
    return " ".join((value or "").split())


def is_valid_title_candidate(value):
    # 제목 후보가 비어 있거나 사이트 공통 문구라면 버린다.
    # 위비티 하단 안내문처럼 "※"로 시작하는 문장도 제목으로 오인하지 않게 제외한다.
    title = clean_text(value)
    if not title:
        return False
    if title in NOISE_TITLES:
        return False
    if title.startswith("※"):
        return False
    return True


def normalize_label(value):
    # 라벨 비교를 쉽게 하기 위해 공백/콜론/구분자 등을 제거한다.
    # 예: "주최/주관", "주최 주관", "주최:주관"을 비슷하게 비교할 수 있다.
    label_chars = r"[\s:：ㆍ·/\-_\[\]()]"
    return re.sub(f"{label_chars}+", "", clean_text(value).lower())


def label_matches(text, labels):
    # HTML의 실제 라벨 문구가 사이트마다 조금씩 다르기 때문에 부분 포함 방식으로 비교한다.
    normalized_text = normalize_label(text)
    return any(normalize_label(label) in normalized_text for label in labels)


def find_title_near_summary(soup):
    # 위비티 제목 전용 보정 로직.
    # 전역 h1/h2를 먼저 잡으면 "공모전 대외활동 정보" 같은 공통 제목이 들어갈 수 있다.
    # 그래서 요약 라벨을 먼저 찾고, 그 라벨 블록 바로 앞 heading을 제목으로 쓴다.
    for node in soup.select("li, tr, dt, p"):
        text = clean_text(node.get_text(" ", strip=True))
        if not label_matches(text[:80], SUMMARY_TITLE_LABELS):
            continue

        heading = node.find_previous(["h1", "h2", "h3", "h4", "h5", "h6"])
        if heading:
            title = clean_text(heading.get_text(" ", strip=True))
            if is_valid_title_candidate(title):
                return title

    return ""


def guess_title_from_html(html, soup=None):
    # 상세 페이지에서 제목을 추정한다.
    # 1순위: 위비티 요약 블록 근처 heading
    # 2순위: 일반 상세 페이지에서 자주 쓰는 제목 selector
    # 3순위: 문서 <title> 태그
    soup = soup or BeautifulSoup(html, "html.parser")

    summary_title = find_title_near_summary(soup)
    if summary_title:
        return summary_title

    for selector in [
        ".view_tit",
        ".board_tit",
        ".subject",
        ".contest-title",
        ".tit",
        ".title",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
    ]:
        node = soup.select_one(selector)
        if node:
            title = clean_text(node.get_text(" ", strip=True))
            if is_valid_title_candidate(title):
                return title

    if soup.title and soup.title.string:
        title = clean_text(soup.title.string)
        title = title.split("|", 1)[0].strip()
        title = title.rsplit("-", 1)[0].strip()
        if is_valid_title_candidate(title):
            return title
    return ""


def strip_label_prefix(text, labels):
    # "분야 기획/아이디어" 또는 "분야: 기획/아이디어" 같은 문장에서
    # 앞의 라벨 부분만 제거하고 값만 남긴다.
    text = clean_text(text)
    for label in sorted(labels, key=len, reverse=True):
        pattern = rf"^\s*{re.escape(label)}\s*[:：ㆍ·\-/]?\s*"
        value = re.sub(pattern, "", text, flags=re.IGNORECASE)
        if value != text:
            return clean_text(value)
    return text


def meaningful_value(value, labels):
    # 너무 긴 문단이나 라벨만 있는 값은 필드 값으로 쓰기 어렵다.
    value = clean_text(value)
    if not value or len(value) > 300:
        return ""
    if normalize_label(value) in {normalize_label(label) for label in labels}:
        return ""
    return strip_label_prefix(value, labels)


def find_value_by_labels(soup, labels):
    # 라벨과 값이 붙어 있는 대표 HTML 구조를 순서대로 처리한다.
    # 1. <tr><th>라벨</th><td>값</td></tr>
    # 2. <dt>라벨</dt><dd>값</dd>
    # 3. <li>라벨 값</li> 또는 <p>라벨 값</p>
    for row in soup.select("tr"):
        cells = row.find_all(["th", "td"], recursive=False) or row.find_all(["th", "td"])
        if len(cells) < 2:
            continue
        label_text = clean_text(cells[0].get_text(" ", strip=True))
        if label_matches(label_text, labels):
            value = meaningful_value(
                " ".join(cell.get_text(" ", strip=True) for cell in cells[1:]),
                labels,
            )
            if value:
                return value

    for dt in soup.select("dt"):
        label_text = clean_text(dt.get_text(" ", strip=True))
        if not label_matches(label_text, labels):
            continue
        dd = dt.find_next_sibling("dd")
        if dd:
            value = meaningful_value(dd.get_text(" ", strip=True), labels)
            if value:
                return value

    for node in soup.select("li, p"):
        text = clean_text(node.get_text(" ", strip=True))
        if len(text) > 300 or not label_matches(text[:80], labels):
            continue

        # 라벨이 strong/span 등 별도 태그로 감싸져 있으면 그 태그를 제거한 뒤 값을 읽는다.
        for child in node.find_all(["strong", "b", "span"], recursive=False):
            child_text = clean_text(child.get_text(" ", strip=True))
            if label_matches(child_text, labels):
                child.extract()
                value = meaningful_value(node.get_text(" ", strip=True), labels)
                if value:
                    return value

        value = meaningful_value(text, labels)
        if value and not label_matches(value, labels):
            return value

    return ""


def find_url_by_labels(soup, labels):
    # "홈페이지"처럼 URL 값이 필요한 라벨을 찾는다.
    # a[href]가 있으면 href를 우선 사용하고, 없으면 텍스트가 http(s)로 시작하는지 확인한다.
    for row in soup.select("tr"):
        cells = row.find_all(["th", "td"], recursive=False) or row.find_all(["th", "td"])
        if len(cells) < 2:
            continue
        label_text = clean_text(cells[0].get_text(" ", strip=True))
        if not label_matches(label_text, labels):
            continue
        link = row.select_one("a[href]")
        if link:
            return clean_text(link.get("href", ""))
        value = meaningful_value(
            " ".join(cell.get_text(" ", strip=True) for cell in cells[1:]),
            labels,
        )
        if value.startswith(("http://", "https://")):
            return value

    for node in soup.select("li, p"):
        text = clean_text(node.get_text(" ", strip=True))
        if len(text) > 300 or not label_matches(text[:80], labels):
            continue
        link = node.select_one("a[href]")
        if link:
            return clean_text(link.get("href", ""))
        value = meaningful_value(text, labels)
        if value.startswith(("http://", "https://")):
            return value

    return ""


def parse_date_range(value):
    # "2026-04-01 ~ 2026-04-30", "2026.04.01 - 2026.04.30",
    # "2026년 04월 01일 ~ 2026년 04월 30일" 형태를 date 두 개로 바꾼다.
    matches = DATE_PATTERN.findall(value or "")
    if len(matches) < 2:
        return None, None

    dates = []
    for year, month, day in matches[:2]:
        try:
            dates.append(datetime(int(year), int(month), int(day)).date())
        except ValueError:
            return None, None
    return dates[0], dates[1]


def find_dates(soup, extracted_text):
    # 날짜는 먼저 "접수기간/공모기간/신청기간" 같은 라벨 주변에서 찾는다.
    # 라벨 구조에서 못 찾으면 전체 추출 텍스트에서 첫 번째 날짜 범위를 fallback으로 사용한다.
    period_text = find_value_by_labels(
        soup,
        ["접수기간", "공모기간", "응모기간", "모집기간", "신청기간", "사업기간", "기간"],
    )
    start_date, end_date = parse_date_range(period_text)
    if start_date or end_date:
        return start_date, end_date

    return parse_date_range(extracted_text)


def classify_content_from_extracted(extracted_text, extracted_images, extracted_files):
    # 본문이 텍스트 중심인지, 이미지 공고문 중심인지, 첨부파일 중심인지 간단히 분류한다.
    image_count = len(extracted_images)
    file_count = len(extracted_files)
    text_length = len(extracted_text)

    if file_count > 0 and text_length < 300:
        return "file"
    if image_count > 0 and text_length < 300:
        return "image"
    if text_length > 300 and (image_count > 0 or file_count > 0):
        return "mixed"
    if text_length > 300:
        return "text"
    return "unknown"


def is_wevity_url(source_url):
    # 상세 파싱 단계에서도 사이트별 전략을 나누기 위해 hostname을 직접 확인한다.
    hostname = urlparse(source_url or "").hostname or ""
    return hostname.lower().endswith("wevity.com")


def parse_detail_fields(html, source_url, list_meta):
    # 상세 URL의 HTML에서 form initial 후보를 만드는 진입점.
    #
    # 위비티:
    # - 요약 영역/상세내용 영역이 고정되어 있으므로 wevity_detail_parser가 좁은 범위만 본다.
    # - 첨부파일도 요약 영역의 "첨부파일" 항목에서만 찾는다.
    #
    # 공공데이터포털로 간주되는 나머지 URL:
    # - 실제 상세 페이지가 여러 외부 사이트일 수 있어 generic_detail_parser가 넓게 추정한다.
    if is_wevity_url(source_url):
    
        return parse_wevity_detail_fields(html, source_url, list_meta)

    return parse_generic_detail_fields(html, source_url, list_meta)


# 사이트별 파서는 이 파일의 공통 유틸(clean_text, find_value_by_labels 등)을 다시 import한다.
# 그래서 파일 상단에서 import하면 순환 import가 발생한다. 공통 유틸과 parse_detail_fields가
# 모두 정의된 뒤 마지막에 import해야 Django 시작 시 안전하게 로딩된다.
from contests.services.generic_detail_parser import parse_generic_detail_fields
from contests.services.wevity_detail_parser import parse_wevity_detail_fields
