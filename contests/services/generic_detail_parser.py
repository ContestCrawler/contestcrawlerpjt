from bs4 import BeautifulSoup

from contests.services.prefill_detail_parser import (
    classify_content_from_extracted,
    find_dates,
    find_url_by_labels,
    find_value_by_labels,
    guess_title_from_html,
)
from contests.utils.extractor.file_extractor import extract_files
from contests.utils.extractor.image_extractor import extract_images
from contests.utils.extractor.text_extractor import extract_text_content


def parse_generic_detail_fields(html, source_url, list_meta):
    # 공공데이터포털 상세 URL은 실제로는 여러 기관/회사 사이트로 연결될 수 있다.
    # 사이트별 HTML 구조가 제각각이므로 특정 영역을 확정하지 않고,
    # 기존 공통 extractor와 라벨 추정 로직을 넓게 사용한다.
    soup = BeautifulSoup(html, "html.parser")

    # 범용 사이트에서는 "어디가 본문인지"를 추정해야 한다.
    # extract_text_content/extract_images/extract_files는 common.get_main_content()를 통해
    # 가장 본문에 가까운 컨테이너를 고른 뒤 값을 수집한다.
    extracted_text = extract_text_content(html).get("raw_text", "")
    extracted_images = extract_images(html, source_url)
    extracted_files = extract_files(html, source_url)
    detail_start_date, detail_end_date = find_dates(soup, extracted_text)

    # 공공데이터포털 목록에서 가져온 값은 상세 사이트 추정보다 안정적이므로 우선한다.
    title = list_meta.get("title") or guess_title_from_html(html, soup)
    host_region = list_meta.get("host_region") or list_meta.get("region") or find_value_by_labels(
        soup,
        ["지역", "장소", "개최지역", "시행지역", "활동지역", "소재지", "region"],
    )

    # 아래 값들은 목록 페이지에 없거나 사이트마다 표현이 달라 상세 HTML에서 라벨 기반으로 찾는다.
    category = find_value_by_labels(
        soup,
        ["분야", "공모분야", "사업분야", "카테고리", "category", "분류"],
    )
    eligibility = find_value_by_labels(
        soup,
        ["자격", "대상", "응모대상", "참가대상", "지원자격", "eligibility"],
    )
    organizer = find_value_by_labels(
        soup,
        [
            "주최/주관",
            "주최주관",
            "주최사",
            "주최기관",
            "주관기관",
            "주최",
            "주관",
            "기관명",
            "소관기관",
            "organizer",
        ],
    )
    total_prize = find_value_by_labels(
        soup,
        ["총 상금", "총상금", "시상내역"],
    )
    first_prize = find_value_by_labels(
        soup,
        ["1등 상금", "1등상금", "대상 상금", "대상상금"],
    )
    detail_url = find_url_by_labels(
        soup,
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
        "start_date": list_meta.get("start_date") or detail_start_date,
        "end_date": list_meta.get("end_date") or detail_end_date,
        "description": extracted_text,
        "content_type": content_type,
        "image_urls": "\n".join(extracted_images),
        "attachment_lines": "\n".join(
            f"{item['file_name']} | {item['file_url']}" for item in extracted_files
        ),
    }
