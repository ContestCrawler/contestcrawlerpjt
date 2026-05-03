from urllib.parse import urljoin

from contests.utils.extractor.common import get_main_content


EXCLUDED_IMAGE_KEYWORDS = [
    "logo",
    "ico_",
    "icon",
    "banner",
    "btn_",
    "bullet",
    "sprite",
    "loading",
    "spacer",
    "blank",
]


def _is_contest_related_image(img, image_url):
    # lower():
    # - 대소문자 영향 없이 키워드 필터링하기 위해 소문자화
    lower_url = image_url.lower()

    # startswith("data:"):
    # - base64 inline 이미지(data URI) 제외
    if lower_url.startswith("data:"):
        return False

    # any(...):
    # - URL에 제외 키워드가 하나라도 있으면 False
    if any(keyword in lower_url for keyword in EXCLUDED_IMAGE_KEYWORDS):
        return False

    # img.get("class", []):
    # - class 속성이 없을 수 있어 기본값 []를 사용
    cls = " ".join(img.get("class", [])).lower()
    alt = (img.get("alt") or "").lower()

    # img.parent:
    # - 상위 컨텍스트 텍스트까지 참고해 아이콘/공유 이미지 판별
    parent_text = img.parent.get_text(" ", strip=True).lower() if img.parent else ""
    context = f"{cls} {alt} {parent_text}"
    if any(keyword in context for keyword in ["logo", "icon", "sns", "share"]):
        return False

    width = img.get("width")
    height = img.get("height")
    try:
        # int():
        # - 문자열 속성값을 수치로 변환해 작은 UI 아이콘 제거
        if width and height and int(width) <= 40 and int(height) <= 40:
            return False
    except (TypeError, ValueError):
        # 속성값이 비정상일 때는 필터를 건너뛰고 이미지 유지
        pass

    return True


def extract_images(html, base_url):
    content = get_main_content(html)

    images = []
    seen = set()

    # select("img[src]"):
    # - src가 있는 이미지 태그만 선택
    for img in content.select("img[src]"):
        src = img.get("src")
        if not src:
            continue

        # urljoin():
        # - 상대경로 src를 절대 URL로 변환
        image_url = urljoin(base_url, src)
        if not _is_contest_related_image(img, image_url):
            continue

        # set으로 중복 URL 제거
        if image_url in seen:
            continue
        seen.add(image_url)
        images.append(image_url)

    return images
