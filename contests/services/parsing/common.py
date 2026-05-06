import re
from datetime import datetime

from bs4 import BeautifulSoup


DATE_PATTERN = re.compile(r"(\d{4})\D{0,5}(\d{1,2})\D{0,5}(\d{1,2})")
SUMMARY_TITLE_LABELS = [
    "분야",
    "응모대상",
    "주최",
    "주관",
    "접수기간",
    "field",
    "category",
    "eligibility",
    "organizer",
    "period",
]
NOISE_TITLES = {
    "공모전 상세내용 정보",
    "상세내용",
    "공모전 요강",
    "contest information",
    "detail",
    "contest details",
}


def clean_text(value):
    """
    HTML에서 추출한 텍스트의 공백과 줄바꿈을 정리한다.

    의미:
        label 비교, 제목 후보 비교, 저장 값 생성 전에 문자열 형태를 안정화한다.

    반환값:
        연속 공백이 하나로 줄어든 문자열을 반환한다. None은 빈 문자열처럼 처리된다.
    """
    return " ".join((value or "").split())


def is_valid_title_candidate(value):
    """
    텍스트가 공모전 제목 후보로 사용할 수 있는지 판단한다.

    의미:
        빈 값, 공통 섹션 제목, 안내 문구처럼 실제 공모전명이 아닌 값을 제외한다.

    반환값:
        제목 후보로 적절하면 True, 아니면 False를 반환한다.
    """
    title = clean_text(value)
    if not title:
        return False
    if title.lower() in NOISE_TITLES:
        return False
    if title.startswith(("※", "*")):
        return False
    return True


def normalize_label(value):
    """
    label 비교를 위해 공백, 구분자, 괄호 등을 제거한 문자열을 만든다.

    의미:
        사이트마다 다른 "주최/주관", "주최 주관", "주최:주관" 같은 표기를
        최대한 같은 label로 비교하기 위한 정규화 단계다.

    반환값:
        비교용으로 정규화된 소문자 문자열을 반환한다.
    """
    label_chars = r"[\s:|/\\\-_\[\]()]"
    return re.sub(f"{label_chars}+", "", clean_text(value).lower())


def label_matches(text, labels):
    """
    텍스트가 주어진 label 후보 중 하나와 의미상 맞는지 확인한다.

    의미:
        상세 페이지에서 "분야", "대상", "홈페이지" 같은 label 영역을 찾을 때 사용한다.

    반환값:
        정규화된 label 후보가 정규화된 text 안에 포함되면 True, 아니면 False를 반환한다.
    """
    normalized_text = normalize_label(text)
    return any(normalize_label(label) in normalized_text for label in labels)


def find_title_near_summary(soup):
    """
    요약 정보 영역 근처의 heading을 공모전 제목 후보로 찾는다.

    의미:
        상세 페이지의 h1/h2가 공통 섹션 제목일 수 있어, 분야/대상/기간 같은
        요약 label 근처에 있는 이전 heading을 우선 제목으로 본다.

    반환값:
        유효한 제목 후보 문자열을 반환한다. 찾지 못하면 빈 문자열을 반환한다.
    """
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
    """
    상세 HTML에서 공모전 제목을 추정한다.

    의미:
        요약 영역 근처 heading, 자주 쓰이는 title selector, 문서 title 순서로 후보를 찾는다.

    반환값:
        제목 문자열을 반환한다. 적절한 후보가 없으면 빈 문자열을 반환한다.
    """
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
    """
    "분야: 기획/아이디어" 같은 문자열에서 label prefix를 제거한다.

    의미:
        label과 값이 같은 노드 안에 붙어 있을 때 실제 값만 저장하기 위해 사용한다.

    반환값:
        label prefix가 제거된 문자열을 반환한다. 매칭되는 prefix가 없으면 원문 정리값을 반환한다.
    """
    text = clean_text(text)
    for label in sorted(labels, key=len, reverse=True):
        pattern = rf"^\s*{re.escape(label)}\s*[:|/\-]?\s*"
        value = re.sub(pattern, "", text, flags=re.IGNORECASE)
        if value != text:
            return clean_text(value)
    return text


def meaningful_value(value, labels):
    """
    label 탐색 결과가 실제 필드 값으로 쓸 만한지 검증하고 정리한다.

    의미:
        너무 긴 본문, 빈 값, label만 있는 값이 필드 값으로 저장되는 것을 막는다.

    반환값:
        의미 있는 값이면 정리된 문자열을 반환한다. 부적절하면 빈 문자열을 반환한다.
    """
    value = clean_text(value)
    if not value or len(value) > 300:
        return ""
    if normalize_label(value) in {normalize_label(label) for label in labels}:
        return ""
    return strip_label_prefix(value, labels)


def find_value_by_labels(soup, labels):
    """
    HTML에서 주어진 label 후보에 대응하는 텍스트 값을 찾는다.

    의미:
        tr/th/td, dt/dd, li/p 구조를 순서대로 훑어 label 옆의 값을 추출한다.

    반환값:
        처음 찾은 의미 있는 값 문자열을 반환한다. 찾지 못하면 빈 문자열을 반환한다.
    """
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
    """
    HTML에서 주어진 label 후보에 대응하는 URL 값을 찾는다.

    의미:
        홈페이지/URL 같은 필드는 텍스트보다 a[href]가 더 신뢰할 수 있으므로 링크를 우선 사용한다.

    반환값:
        URL 문자열을 반환한다. label 영역을 찾지 못하거나 URL 값이 없으면 빈 문자열을 반환한다.
    """
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
    """
    문자열에서 시작일과 종료일로 보이는 날짜 2개를 추출한다.

    의미:
        "2026.05.01 ~ 2026.05.31"처럼 separator가 다양한 날짜 범위를 date 객체로 변환한다.

    반환값:
        (start_date, end_date) tuple을 반환한다.
        날짜 2개를 찾지 못하거나 유효하지 않으면 (None, None)을 반환한다.
    """
    matches = DATE_PATTERN.findall(value or "")
    # Error handling:
    # 날짜가 2개 미만이면 기간으로 볼 수 없으므로 빈 날짜 tuple을 반환한다.
    if len(matches) < 2:
        return None, None

    dates = []
    for year, month, day in matches[:2]:
        try:
            dates.append(datetime(int(year), int(month), int(day)).date())
        except ValueError:
            # Error handling:
            # 2026-99-99 같은 잘못된 날짜는 파싱 실패로 보고 전체 기간을 비운다.
            return None, None
    return dates[0], dates[1]


def find_dates(soup, extracted_text):
    """
    상세 HTML에서 접수/공모 기간 날짜를 찾는다.

    의미:
        먼저 기간 label 주변 값을 찾고, 없으면 전체 추출 텍스트에서 첫 날짜 범위를 fallback으로 찾는다.

    반환값:
        (start_date, end_date) tuple을 반환한다. 찾지 못하면 (None, None)을 반환한다.
    """
    period_text = find_value_by_labels(
        soup,
        [
            "접수기간",
            "공모기간",
            "응모기간",
            "모집기간",
            "신청기간",
            "사업기간",
            "기간",
            "period",
            "application period",
            "contest period",
            "recruitment period",
            "submission period",
        ],
    )
    start_date, end_date = parse_date_range(period_text)
    if start_date or end_date:
        return start_date, end_date

    return parse_date_range(extracted_text)


def classify_content_from_extracted(extracted_text, extracted_images, extracted_files):
    """
    추출된 본문/이미지/첨부파일 비중으로 상세 콘텐츠 유형을 분류한다.

    의미:
        관리자나 화면에서 공모전 상세가 텍스트 중심인지, 이미지/파일 중심인지 구분할 수 있게 한다.

    반환값:
        "file", "image", "mixed", "text", "unknown" 중 하나를 반환한다.
    """
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
