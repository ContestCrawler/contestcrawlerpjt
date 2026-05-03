from urllib.parse import unquote, urlparse

from contests.models import ContestAttachment, ContestImage


def guess_file_name_from_url(url):
    # urlparse(url):
    # - URL을 path/query 등으로 분해
    # parsed.path.split("/")[-1]:
    # - 마지막 경로 세그먼트를 파일명 후보로 사용
    parsed = urlparse(url)
    name = unquote(parsed.path.split("/")[-1]).strip()
    return name or "attachment"


def guess_file_type(file_name):
    # rsplit(".", 1):
    # - 마지막 점 기준으로 확장자 분리 (파일명에 점이 여러 개여도 안전)
    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    allowed = {"pdf", "hwp", "hwpx", "doc", "docx", "zip"}
    return ext if ext in allowed else "etc"


def save_assets(contest, image_urls_text, attachment_lines_text):
    # splitlines():
    # - textarea 멀티라인 문자열을 줄 단위 리스트로 변환
    # strip():
    # - 빈 줄/공백 줄 제거
    image_urls = [line.strip() for line in image_urls_text.splitlines() if line.strip()]
    for image_url in image_urls:
        # Model.objects.create():
        # - 인스턴스 생성 + DB 저장을 한 번에 수행
        ContestImage.objects.create(contest=contest, image_url=image_url)

    attachment_lines = [line.strip() for line in attachment_lines_text.splitlines() if line.strip()]
    for line in attachment_lines:
        # split("|", 1):
        # - 첫 구분자만 사용해 파일명/URL 분리
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
