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
    # 아이콘/로고/작은 UI 이미지처럼 공모전 본문과 무관한 이미지를 제외한다.
    lower_url = image_url.lower()
    if lower_url.startswith("data:"):
        return False
    if any(keyword in lower_url for keyword in EXCLUDED_IMAGE_KEYWORDS):
        return False

    cls = " ".join(img.get("class", [])).lower()
    alt = (img.get("alt") or "").lower()
    parent_text = img.parent.get_text(" ", strip=True).lower() if img.parent else ""
    context = f"{cls} {alt} {parent_text}"
    if any(keyword in context for keyword in ["logo", "icon", "sns", "share"]):
        return False

    width = img.get("width")
    height = img.get("height")
    try:
        if width and height and int(width) <= 40 and int(height) <= 40:
            return False
    except (TypeError, ValueError):
        pass

    return True


def extract_images(html, base_url):
    # 본문 이미지 URL을 추출하고 중복을 제거한다.
    content = get_main_content(html)

    images = []
    seen = set()
    for img in content.select("img[src]"):
        src = img.get("src")
        if not src:
            continue

        image_url = urljoin(base_url, src)
        if not _is_contest_related_image(img, image_url):
            continue
        if image_url in seen:
            continue

        seen.add(image_url)
        images.append(image_url)

    return images
