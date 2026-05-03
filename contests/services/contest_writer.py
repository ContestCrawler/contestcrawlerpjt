from urllib.parse import unquote, urlparse

from contests.models import ContestAttachment, ContestImage


def guess_file_name_from_url(url):
    # URL path 마지막 세그먼트를 파일명으로 사용
    parsed = urlparse(url)
    name = unquote(parsed.path.split("/")[-1]).strip()
    return name or "attachment"


def guess_file_type(file_name):
    # 모델의 file_type choices에 맞춰 확장자 분류
    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    allowed = {"pdf", "hwp", "hwpx", "doc", "docx", "zip"}
    return ext if ext in allowed else "etc"


def save_assets(contest, image_urls_text, attachment_lines_text):
    # 1) 이미지 URL 저장
    image_urls = [line.strip() for line in image_urls_text.splitlines() if line.strip()]
    for image_url in image_urls:
        ContestImage.objects.create(contest=contest, image_url=image_url)

    # 2) 첨부파일 저장
    # 형식: "파일명 | 파일URL" 또는 "파일URL"
    attachment_lines = [line.strip() for line in attachment_lines_text.splitlines() if line.strip()]
    for line in attachment_lines:
        if "|" in line:
            file_name, file_url = [part.strip() for part in line.split("|", 1)]
        else:
            file_url = line
            file_name = guess_file_name_from_url(file_url)

        if not file_url:
            continue
        if not file_name:
            file_name = guess_file_name_from_url(file_url)

        ContestAttachment.objects.create(
            contest=contest,
            file_name=file_name,
            file_url=file_url,
            file_type=guess_file_type(file_name),
        )
