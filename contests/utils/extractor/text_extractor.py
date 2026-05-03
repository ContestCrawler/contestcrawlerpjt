from contests.utils.extractor.common import get_main_content


def extract_text_content(html):
    # 본문 영역에서 텍스트를 추출하고,
    # 네비/공유/댓글 등 노이즈 영역을 제거한다.
    content = get_main_content(html)
    cleanup_selectors = [
        "script",
        "style",
        "noscript",
        "header",
        "footer",
        "nav",
        ".breadcrumb",
        ".location",
        ".gnb",
        ".lnb",
        ".quick",
        ".share",
        ".sns",
        ".comment",
        ".reply",
    ]

    for selector in cleanup_selectors:
        for node in content.select(selector):
            node.decompose()

    # 저장/검색 시 일관성을 위해 공백을 정규화한다.
    raw_text = content.get_text(" ", strip=True)
    raw_text = " ".join(raw_text.split())

    return {"raw_text": raw_text}
