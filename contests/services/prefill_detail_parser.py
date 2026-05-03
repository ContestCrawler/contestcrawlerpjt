from bs4 import BeautifulSoup

from contests.utils.extractor.file_extractor import extract_files
from contests.utils.extractor.image_extractor import extract_images
from contests.utils.extractor.text_extractor import extract_text_content


def clean_text(value):
    # 문자열 공통 정리 함수.
    # split()/join() 조합은 연속 공백/줄바꿈/탭을 1칸 공백으로 통일하는 가장 간단한 방법.
    return " ".join((value or "").split())


def guess_title_from_html(html):
    # BeautifulSoup(html, "html.parser"):
    # - HTML 문자열을 DOM처럼 탐색 가능한 객체로 변환.
    # - selector 기반 탐색(select_one)이나 텍스트 추출(get_text)을 위해 필요.
    soup = BeautifulSoup(html, "html.parser")

    # soup.select_one(css_selector):
    # - CSS 셀렉터에 맞는 첫 번째 노드 1개를 반환.
    # - 제목 후보는 보통 1개면 충분하므로 select()보다 select_one()이 적합.
    for selector in ["h1", ".title", ".subject", ".board_tit"]:
        node = soup.select_one(selector)
        if node:
            # node.get_text(" ", strip=True):
            # - 노드 내부 텍스트를 모두 합침.
            # - 구분자 " "를 주면 태그 경계가 붙지 않아 가독성 유지.
            # - strip=True로 앞뒤 공백 제거.
            title = clean_text(node.get_text(" ", strip=True))
            if title:
                return title

    # soup.title / soup.title.string:
    # - 문서 <title> 태그 접근.
    # - 본문 제목 셀렉터를 못 찾는 경우의 fallback.
    if soup.title and soup.title.string:
        return clean_text(soup.title.string)
    return ""


def extract_label_map(soup):
    # 다양한 마크업 패턴에서 "라벨 -> 값" 사전을 만든다.
    # 사이트마다 구조가 달라도 이후 매핑 로직을 공통화하기 위한 중간 표현.
    data = {}

    # soup.select("tr"):
    # - 모든 table row를 가져와 th/td 패턴을 순회한다.
    for row in soup.select("tr"):
        # row.find("th") / row.find("td"):
        # - 해당 row 하위에서 첫 번째 th/td를 찾는다.
        # - find()는 존재하지 않으면 None을 반환하므로 조건문으로 안전 처리.
        th = row.find("th")
        td = row.find("td")
        if th and td:
            key = clean_text(th.get_text(" ", strip=True)).lower()
            val = clean_text(td.get_text(" ", strip=True))
            # key not in data:
            # - 먼저 찾은 값을 우선 채택해 뒤의 중복 라벨 덮어쓰기를 방지.
            if key and val and key not in data:
                data[key] = val

    # soup.select("dt") + dt.find_next_sibling("dd"):
    # - 정의목록(dl) 구조에서 라벨/값 쌍을 복구하는 전형적인 방식.
    for dt in soup.select("dt"):
        dd = dt.find_next_sibling("dd")
        if dd:
            key = clean_text(dt.get_text(" ", strip=True)).lower()
            val = clean_text(dd.get_text(" ", strip=True))
            if key and val and key not in data:
                data[key] = val

    # 문장형 "라벨: 값" 패턴 처리.
    # select("li, p, div, span")로 텍스트 컨테이너를 넓게 수집한 뒤 heuristic 필터 적용.
    for node in soup.select("li, p, div, span"):
        text = clean_text(node.get_text(" ", strip=True))
        if ":" not in text or len(text) > 200:
            continue
        # split(":", 1):
        # - 첫 번째 콜론에서만 분리해 값 내부 콜론을 보존.
        key, val = text.split(":", 1)
        key = clean_text(key).lower()
        val = clean_text(val)
        if 1 <= len(key) <= 20 and val and key not in data:
            data[key] = val

    return data


def find_value_by_keys(data_map, keys):
    # 라벨 사전에서 키워드 기반으로 값을 찾는다.
    # "in" 비교를 쓰는 이유:
    # - 라벨이 정확히 같지 않아도(예: "참가대상", "응모 대상") 부분 매칭 가능.
    for key in keys:
        key = key.lower()
        for existing_key, value in data_map.items():
            if key in existing_key:
                return value
    return ""


def classify_content_from_extracted(extracted_text, extracted_images, extracted_files):
    # len():
    # - 텍스트 길이/이미지 개수/파일 개수를 수치화해 간단 규칙 분류.
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


def parse_detail_fields(html, source_url, list_meta):
    # 상세 페이지 1건에서 form 초기값 후보를 만드는 함수.
    soup = BeautifulSoup(html, "html.parser")
    label_map = extract_label_map(soup)

    # extractor 함수들은 이미 본문 필터링/정규화를 수행하므로 여기서는 조합만 담당.
    extracted_text = extract_text_content(html).get("raw_text", "")
    extracted_images = extract_images(html, source_url)
    extracted_files = extract_files(html, source_url)

    # dict.get("key"):
    # - key가 없을 때 KeyError 대신 None/기본값 반환.
    # - 리스트 메타 누락에도 안전하게 fallback 로직 구성 가능.
    title = list_meta.get("title") or guess_title_from_html(html)
    region = list_meta.get("region") or find_value_by_keys(label_map, ["지역", "장소", "시행지역", "region"])
    category = find_value_by_keys(label_map, ["분야", "카테고리", "category", "분류"])
    eligibility = find_value_by_keys(label_map, ["자격", "대상", "응모대상", "참가대상", "eligibility"])

    content_type = classify_content_from_extracted(
        extracted_text=extracted_text,
        extracted_images=extracted_images,
        extracted_files=extracted_files,
    )

    # "\n".join(list):
    # - textarea 멀티라인 입력 형식으로 직렬화.
    # - form에서 사용자 수정이 쉽다.
    return {
        "title": title,
        "region": region,
        "category": category,
        "eligibility": eligibility,
        "description": extracted_text,
        "content_type": content_type,
        "image_urls": "\n".join(extracted_images),
        "attachment_lines": "\n".join(
            f"{item['file_name']} | {item['file_url']}" for item in extracted_files
        ),
    }
