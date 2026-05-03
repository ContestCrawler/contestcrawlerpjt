import re
from urllib.parse import parse_qs, unquote, urljoin, urlparse

from contests.utils.extractor.common import get_main_content


FILE_EXTENSIONS = [
    "pdf", "hwp", "hwpx", "doc", "docx", "zip",
    "jpg", "jpeg", "png", "xlsx", "xls", "ppt", "pptx",
]

# "|".join(...):
# - 정규식 확장자 그룹을 동적으로 구성
FILE_EXT_RE = "|".join(FILE_EXTENSIONS)

# re.compile(..., re.IGNORECASE):
# - 확장자 대소문자 구분 없이 매칭하기 위해 사전 컴파일
FILE_NAME_PATTERN = re.compile(
    rf"([^\s/\\?&]+\.(?:{FILE_EXT_RE}))",
    re.IGNORECASE,
)


def _has_file_extension(text):
    # Pattern.search():
    # - 문자열 어디든 확장자 패턴이 있는지 검사
    return bool(FILE_NAME_PATTERN.search(text or ""))


def _extract_file_name_from_href(href):
    # urlparse():
    # - href를 path/query 등으로 분해
    parsed = urlparse(href)

    # parse_qs():
    # - query 문자열을 dict(key -> [values])로 변환
    query = parse_qs(parsed.query)
    for key in ["filename", "fileName", "file_name", "atchFileNm", "orignlFileNm"]:
        value = query.get(key)
        if value:
            # unquote():
            # - URL 인코딩된 파일명(%ED%95%9C...) 복원
            name = unquote(value[0]).strip()
            if _has_file_extension(name):
                return name

    # query에 파일명이 없으면 path 마지막 세그먼트로 fallback
    path_name = unquote(parsed.path.split("/")[-1]).strip()
    if _has_file_extension(path_name):
        return path_name
    return ""


def _extract_file_name(a, href):
    # a.get():
    # - download/title 속성 우선 확인
    # a.get_text():
    # - 링크 텍스트에서 파일명 패턴 확인
    for candidate in [a.get("download"), a.get("title"), a.get_text(" ", strip=True)]:
        if candidate and _has_file_extension(candidate):
            match = FILE_NAME_PATTERN.search(candidate)
            if match:
                return match.group(1).strip()

    return _extract_file_name_from_href(href)


def extract_files(html, base_url):
    content = get_main_content(html)

    files = []
    seen_urls = set()

    # select("a[href]"):
    # - href가 있는 링크만 대상으로 함
    for a in content.select("a[href]"):
        href = (a.get("href") or "").strip()
        if not href:
            continue

        lower_target = f"{href} {a.get_text(' ', strip=True)}".lower()
        # any():
        # - 확장자 힌트 또는 다운로드 키워드가 하나라도 있으면 파일 링크로 판단
        is_file_hint = (
            any(ext in lower_target for ext in [f".{ext}" for ext in FILE_EXTENSIONS])
            or any(keyword in lower_target for keyword in ["download", "첨부", "파일", "붙임"])
        )
        if not is_file_hint:
            continue

        # 전체 다운로드/뷰어 링크는 일반 첨부 링크가 아니므로 제외
        if "downloadall" in href.lower() or "synapviewer" in href.lower():
            continue

        # urljoin():
        # - 상대 href를 절대 URL로 변환
        file_url = urljoin(base_url, href)

        # set 중복 제거
        if file_url in seen_urls:
            continue
        seen_urls.add(file_url)

        file_name = _extract_file_name(a, href)
        if not file_name:
            # 마지막 fallback: 절대 URL path 끝값 사용
            file_name = unquote(urlparse(file_url).path.split("/")[-1]) or "attachment"

        files.append({
            "file_name": file_name,
            "file_url": file_url,
        })

    return files
