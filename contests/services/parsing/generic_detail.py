from bs4 import BeautifulSoup

from contests.services.parsing.common import (
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
    """
    특정 사이트 전용 규칙이 없는 상세 페이지에서 공모전 필드를 추정한다.

    의미:
        본문 텍스트, 이미지, 첨부파일을 공통 extractor로 찾고,
        label 기반 탐색으로 카테고리/대상/주최/상금/홈페이지/날짜를 추정한다.
        목록 메타데이터가 있으면 제목과 날짜 일부를 우선 사용한다.

    반환값:
        title, host_region, organizer, prize, detail_url, category, eligibility,
        start_date, end_date, description, content_type, image_urls,
        attachment_lines를 담은 dict를 반환한다.
    """
    soup = BeautifulSoup(html, "html.parser")

    extracted_text = extract_text_content(html).get("raw_text", "")
    extracted_images = extract_images(html, source_url)
    extracted_files = extract_files(html, source_url)
    detail_start_date, detail_end_date = find_dates(soup, extracted_text)

    title = list_meta.get("title") or guess_title_from_html(html, soup)
    host_region = list_meta.get("host_region") or list_meta.get("region") or find_value_by_labels(
        soup,
        ["지역", "장소", "개최지역", "활동지역", "소재지", "region", "location", "place"],
    )

    category = find_value_by_labels(soup, ["분야", "공모분야", "사업분야", "카테고리", "분류", "category", "field", "type"])
    eligibility = find_value_by_labels(soup, ["자격", "대상", "응모대상", "참가대상", "지원자격", "eligibility", "target", "applicant"])
    organizer = find_value_by_labels(soup, ["주최/주관", "주최주관", "주최", "주관", "기관명", "organizer", "host", "sponsor"])
    total_prize = find_value_by_labels(soup, ["총상금", "총 시상금", "시상내역", "total prize", "prize"])
    first_prize = find_value_by_labels(soup, ["1등상금", "1등 시상금", "대상상금", "대상 시상금", "first prize", "grand prize"])
    detail_url = find_url_by_labels(soup, ["홈페이지", "공식홈페이지", "website", "homepage", "url"])

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
