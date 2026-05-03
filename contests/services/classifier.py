from bs4 import BeautifulSoup


def classify_content(html):
    # 상세 페이지를 대략 text/image/file/mixed로 분류한다.
    # 현재는 보조 메타정보 용도이며, 실제 추출은 별도 로직에서 항상 수행한다.
    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text(" ", strip=True)
    text_length = len(text)

    images = soup.find_all("img")
    files = soup.select(
        "a[href$='.pdf'], "
        "a[href$='.hwp'], "
        "a[href$='.hwpx'], "
        "a[href$='.docx']"
    )

    image_count = len(images)
    file_count = len(files)

    if file_count > 0 and text_length < 300:
        return "file"
    if image_count > 0 and text_length < 300:
        return "image"
    if text_length > 300 and (image_count > 0 or file_count > 0):
        return "mixed"
    if text_length > 300:
        return "text"
    return "unknown"
