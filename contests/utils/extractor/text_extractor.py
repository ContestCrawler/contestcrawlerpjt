from contests.utils.extractor.common import get_main_content


def extract_text_content(html):
    # get_main_content():
    # - 사이트별 상이한 본문 컨테이너를 공통 기준으로 선택
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
        # content.select():
        # - 본문 하위에서 해당 selector에 맞는 모든 노드 반환
        for node in content.select(selector):
            # decompose():
            # - 노드를 트리에서 완전히 제거(텍스트/자식 포함)
            # - 노이즈 영역 제거에 적합
            node.decompose()

    # get_text():
    # - 남은 본문 텍스트를 수집
    raw_text = content.get_text(" ", strip=True)

    # split()/join():
    # - 중복 공백 정규화로 저장/검색 일관성 확보
    raw_text = " ".join(raw_text.split())

    return {"raw_text": raw_text}
