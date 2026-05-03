from bs4 import BeautifulSoup

from contests.services.classifier import classify_content
from contests.services.crawler import fetch_list_page
from contests.services.detail_crawler import fetch_detail_page
from contests.services.parser import parse_contest_list
from contests.utils.extractor.file_extractor import extract_files
from contests.utils.extractor.image_extractor import extract_images
from contests.utils.extractor.text_extractor import extract_text_content


def clean_text(value):
    # 전처리 공통 함수:
    # 줄바꿈/탭/중복 공백을 1칸 공백으로 정규화해 텍스트 비교 정확도를 높인다.
    return " ".join((value or "").split())


def guess_title_from_html(html):
    # 상세 페이지에서 제목을 추정한다.
    # 1) h1, .title 등 자주 쓰는 제목 셀렉터를 우선 시도
    # 2) 실패하면 <title> 태그를 fallback으로 사용
    soup = BeautifulSoup(html, "html.parser")
    for selector in ["h1", ".title", ".subject", ".board_tit"]:
        node = soup.select_one(selector)
        if node:
            title = clean_text(node.get_text(" ", strip=True))
            if title:
                return title

    if soup.title and soup.title.string:
        return clean_text(soup.title.string)
    return ""


def extract_label_map(soup):
    # 목적:
    # 사이트마다 마크업 구조가 달라도 "라벨:값" 형태를 최대한 공통 추출하기 위해
    # 다양한 패턴을 하나의 dict(label -> value)로 수집한다.
    data = {}

    # 패턴 1) table 구조 (th / td)
    for row in soup.select("tr"):
        th = row.find("th")
        td = row.find("td")
        if th and td:
            key = clean_text(th.get_text(" ", strip=True)).lower()
            val = clean_text(td.get_text(" ", strip=True))
            if key and val and key not in data:
                data[key] = val

    # 패턴 2) dl 구조 (dt / dd)
    for dt in soup.select("dt"):
        dd = dt.find_next_sibling("dd")
        if dd:
            key = clean_text(dt.get_text(" ", strip=True)).lower()
            val = clean_text(dd.get_text(" ", strip=True))
            if key and val and key not in data:
                data[key] = val

    # 패턴 3) 일반 텍스트 "라벨: 값"
    for node in soup.select("li, p, div, span"):
        text = clean_text(node.get_text(" ", strip=True))
        if ":" not in text or len(text) > 200:
            continue
        key, val = text.split(":", 1)
        key = clean_text(key).lower()
        val = clean_text(val)
        if 1 <= len(key) <= 20 and val and key not in data:
            data[key] = val

    return data


def find_value_by_keys(data_map, keys):
    # 라벨 맵에서 key 후보가 포함된 첫 값을 반환한다.
    # 예) keys=["자격","대상"]이면 "참가대상" 같은 라벨에도 매칭된다.
    for key in keys:
        key = key.lower()
        for existing_key, value in data_map.items():
            if key in existing_key:
                return value
    return ""


def normalize_url(url):
    # 리스트 URL과 입력 URL 비교를 위해 trailing slash 차이를 제거한다.
    return (url or "").strip().rstrip("/")


def find_list_metadata(source_url):
    # 리스트 페이지에서 이미 확보 가능한 메타데이터를 우선 재사용한다.
    # 현재 정책:
    # - title / region / start_date / end_date 는 리스트 기준값을 신뢰
    # - 상세 페이지는 보완 정보(eligibility/category/description/asset) 중심
    try:
        list_html = fetch_list_page()
        items = parse_contest_list(list_html)
    except Exception:
        # 리스트 로딩 실패 시 프리필 전체를 중단하지 않기 위해 빈 dict 반환
        return {}

    target = normalize_url(source_url)
    for item in items:
        if normalize_url(item.get("detail_url", "")) == target:
            return {
                "title": item.get("title", ""),
                "region": item.get("region", ""),
                "start_date": item.get("start_date"),
                "end_date": item.get("end_date"),
            }
    return {}


def build_prefill_data(source_url):
    # create 화면 프리필 메인 파이프라인
    # 1) 리스트 메타 조회
    # 2) 상세 HTML 수집
    # 3) 텍스트/이미지/첨부 추출
    # 4) 폼 초기값 dict 생성
    list_meta = find_list_metadata(source_url)

    html = fetch_detail_page(source_url)
    if not html or not html.strip():
        raise ValueError("Fetched page is empty.")

    soup = BeautifulSoup(html, "html.parser")
    label_map = extract_label_map(soup)

    # 본문/이미지/첨부 추출
    extracted_text = extract_text_content(html).get("raw_text", "")
    extracted_images = extract_images(html, source_url)
    extracted_files = extract_files(html, source_url)

    # title/region/date는 리스트 메타 우선
    # 리스트에 없을 때만 상세에서 보완
    title = list_meta.get("title") or guess_title_from_html(html)
    region = list_meta.get("region") or find_value_by_keys(label_map, ["지역", "장소", "시행지역", "region"])
    start_date = list_meta.get("start_date")
    end_date = list_meta.get("end_date")

    # 상세 페이지 라벨 기반 보완 필드
    category = find_value_by_keys(label_map, ["분야", "카테고리", "category", "분류"])
    eligibility = find_value_by_keys(label_map, ["자격", "대상", "응모대상", "참가대상", "eligibility"])

    # ContestCreateForm(initial=...)에 바로 넣을 데이터 구조
    return {
        "source_url": source_url,
        "detail_url": source_url,
        "title": title,
        "eligibility": eligibility,
        "description": extracted_text,
        "category": category,
        "region": region,
        "start_date": start_date,
        "end_date": end_date,
        "content_type": classify_content(html),
        "image_urls": "\n".join(extracted_images),
        "attachment_lines": "\n".join(
            f"{item['file_name']} | {item['file_url']}" for item in extracted_files
        ),
        "is_active": True,
    }
