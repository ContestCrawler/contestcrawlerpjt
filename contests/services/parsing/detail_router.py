from contests.services.parsing.generic_detail import parse_generic_detail_fields
from contests.services.parsing.wevity_detail import parse_wevity_detail_fields
from contests.services.prefilling.url_rules import is_wevity_url


def parse_detail_fields(html, source_url, list_meta):
    """
    상세 페이지 HTML을 사이트에 맞는 상세 파서로 라우팅한다.

    의미:
        Wevity URL은 Wevity 전용 구조 파서를 사용하고, 그 외 URL은 범용 상세 파서를 사용한다.

    반환값:
        상세 파서가 반환하는 Contest prefill용 필드 dict를 그대로 반환한다.
    """
    if is_wevity_url(source_url):
        return parse_wevity_detail_fields(html, source_url, list_meta)

    return parse_generic_detail_fields(html, source_url, list_meta)
