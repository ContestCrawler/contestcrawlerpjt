import re
from urllib.parse import parse_qs, unquote, urljoin, urlparse

from contests.utils.extractor.common import get_main_content


FILE_EXTENSIONS = [
    "pdf", "hwp", "hwpx", "doc", "docx", "zip",
    "jpg", "jpeg", "png", "xlsx", "xls", "ppt", "pptx",
]

FILE_EXT_RE = "|".join(FILE_EXTENSIONS)
FILE_NAME_PATTERN = re.compile(
    rf"([^\s/\\?&]+\.(?:{FILE_EXT_RE}))",
    re.IGNORECASE,
)


def _has_file_extension(text):
    # 파일 확장자 포함 여부 확인
    return bool(FILE_NAME_PATTERN.search(text or ""))


def _extract_file_name_from_href(href):
    # href의 query/path에서 파일명을 복구한다.
    parsed = urlparse(href)
    query = parse_qs(parsed.query)
    for key in ["filename", "fileName", "file_name", "atchFileNm", "orignlFileNm"]:
        value = query.get(key)
        if value:
            name = unquote(value[0]).strip()
            if _has_file_extension(name):
                return name

    path_name = unquote(parsed.path.split("/")[-1]).strip()
    if _has_file_extension(path_name):
        return path_name
    return ""


def _extract_file_name(a, href):
    # a 태그 속성/텍스트에서 파일명을 우선 추출하고 실패 시 href를 사용한다.
    for candidate in [a.get("download"), a.get("title"), a.get_text(" ", strip=True)]:
        if candidate and _has_file_extension(candidate):
            match = FILE_NAME_PATTERN.search(candidate)
            if match:
                return match.group(1).strip()
    return _extract_file_name_from_href(href)


def extract_files(html, base_url):
    # 본문의 첨부 링크를 찾아 파일명/파일URL 목록을 만든다.
    content = get_main_content(html)

    files = []
    seen_urls = set()
    for a in content.select("a[href]"):
        href = (a.get("href") or "").strip()
        if not href:
            continue

        lower_target = f"{href} {a.get_text(' ', strip=True)}".lower()
        is_file_hint = (
            any(ext in lower_target for ext in [f".{ext}" for ext in FILE_EXTENSIONS])
            or any(keyword in lower_target for keyword in ["download", "첨부", "파일", "붙임"])
        )
        if not is_file_hint:
            continue

        # 전체 다운로드 버튼/뷰어 링크 제외
        if "downloadall" in href.lower() or "synapviewer" in href.lower():
            continue

        file_url = urljoin(base_url, href)
        if file_url in seen_urls:
            continue
        seen_urls.add(file_url)

        file_name = _extract_file_name(a, href)
        if not file_name:
            file_name = unquote(urlparse(file_url).path.split("/")[-1]) or "attachment"

        files.append({
            "file_name": file_name,
            "file_url": file_url,
        })

    return files
