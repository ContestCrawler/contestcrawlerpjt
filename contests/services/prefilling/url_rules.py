from urllib.parse import parse_qs, urlparse


def get_url_hostname(url):
    """
    URL에서 hostname만 추출해 소문자로 반환한다.

    의미:
        사이트 판별 로직이 scheme, path, query에 흔들리지 않도록 host만 비교한다.

    반환값:
        hostname 문자열을 반환한다. URL이 비어 있거나 hostname이 없으면 빈 문자열을 반환한다.
    """
    hostname = urlparse(url or "").hostname or ""
    return hostname.lower()


def get_url_query_params(url):
    """
    URL query string을 dict 형태로 파싱한다.

    의미:
        Wevity 상세 URL 여부를 판단할 때 ix 같은 query parameter를 확인하기 위해 사용한다.

    반환값:
        parse_qs() 결과 dict를 반환한다. 각 값은 문자열 리스트다.
    """
    return parse_qs(urlparse(url or "").query)


def is_wevity_url(url):
    """
    URL이 Wevity 도메인인지 판단한다.

    의미:
        Wevity 전용 파서와 크롤러를 적용해도 되는 입력인지 구분한다.

    반환값:
        hostname이 wevity.com 또는 하위 도메인이면 True, 아니면 False를 반환한다.
    """
    return get_url_hostname(url).endswith("wevity.com")


def is_wevity_detail_url(url):
    """
    URL이 Wevity 상세 페이지 URL인지 판단한다.

    의미:
        Wevity 상세 페이지는 query parameter에 ix 값이 들어간다는 규칙을 사용한다.

    반환값:
        Wevity URL이고 ix query parameter가 있으면 True, 아니면 False를 반환한다.
    """
    return is_wevity_url(url) and bool(get_url_query_params(url).get("ix"))


def is_wevity_list_url(url):
    """
    URL이 Wevity 목록 페이지 URL인지 판단한다.

    의미:
        현재 서비스에서는 Wevity 도메인이면서 상세 URL이 아닌 URL을 목록 URL로 취급한다.

    반환값:
        Wevity URL이고 상세 URL이 아니면 True, 아니면 False를 반환한다.
    """
    return is_wevity_url(url) and not is_wevity_detail_url(url)
