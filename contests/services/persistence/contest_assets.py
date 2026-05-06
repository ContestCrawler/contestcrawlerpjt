from urllib.parse import unquote, urlparse

from django.db import transaction

from contests.models import Contest, ContestAttachment, ContestImage


def get_file_name_from_url(url):
    """
    URL path에서 파일명을 추정한다.

    의미:
        첨부파일 입력이 URL만 있을 때 ContestAttachment.file_name을 채우기 위해 사용한다.

    반환값:
        URL 마지막 path segment를 URL decode한 문자열을 반환한다.
        파일명을 추정할 수 없으면 "attachment"를 반환한다.
    """
    parsed = urlparse(url)
    name = unquote(parsed.path.split("/")[-1]).strip()
    return name or "attachment"


def get_attachment_type(file_name):
    """
    파일명 확장자를 ContestAttachment.file_type 값으로 변환한다.

    의미:
        모델에서 허용하는 첨부파일 타입만 저장하고, 모르는 확장자는 etc로 묶는다.

    반환값:
        pdf, hwp, hwpx, doc, docx, zip 중 하나이거나 "etc"를 반환한다.
    """
    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    allowed = {"pdf", "hwp", "hwpx", "doc", "docx", "zip"}
    return ext if ext in allowed else "etc"


def split_contest_prefill(prefill_data):
    """
    prefill dict를 Contest 본문 필드와 자산 입력 필드로 분리한다.

    의미:
        Contest 모델에 직접 저장되는 값과 이미지/첨부파일처럼 별도 테이블에 저장되는 값을 나눈다.

    반환값:
        (contest_fields, asset_fields) tuple을 반환한다.
        - contest_fields: Contest.objects.create(**contest_fields)에 쓰는 dict
        - asset_fields: save_contest_assets()에 넘길 image_urls_text, attachment_lines_text dict
    """
    contest_fields = {
        "title": prefill_data.get("title", ""),
        "eligibility": prefill_data.get("eligibility", ""),
        "description": prefill_data.get("description", ""),
        "category": prefill_data.get("category", ""),
        "host_region": prefill_data.get("host_region", ""),
        "organizer": prefill_data.get("organizer", ""),
        "total_prize": prefill_data.get("total_prize", ""),
        "first_prize": prefill_data.get("first_prize", ""),
        "start_date": prefill_data.get("start_date"),
        "end_date": prefill_data.get("end_date"),
        "is_active": prefill_data.get("is_active", True),
        "detail_url": prefill_data.get("detail_url", ""),
        "content_type": prefill_data.get("content_type", "unknown"),
    }
    asset_fields = {
        "image_urls_text": prefill_data.get("image_urls", ""),
        "attachment_lines_text": prefill_data.get("attachment_lines", ""),
    }
    return contest_fields, asset_fields


@transaction.atomic
def create_contest_with_assets(prefill_data):
    """
    Contest와 연결 자산을 하나의 트랜잭션으로 저장한다.

    의미:
        공모전 본문, 이미지, 첨부파일 저장을 하나로 묶어 중간 실패 시 부분 저장을 막는다.

    반환값:
        생성된 Contest 모델 인스턴스를 반환한다.

    예외:
        Contest 생성 또는 자산 저장 중 예외가 발생하면 transaction.atomic이 전체 저장을 rollback한다.
    """
    contest_fields, asset_fields = split_contest_prefill(prefill_data)
    contest = Contest.objects.create(**contest_fields)
    save_contest_assets(contest=contest, **asset_fields)
    return contest


def save_contest_assets(contest, image_urls_text, attachment_lines_text):
    """
    줄바꿈 문자열로 받은 이미지 URL과 첨부파일 정보를 연결 모델로 저장한다.

    의미:
        prefill textarea 형태의 자산 데이터를 ContestImage, ContestAttachment 레코드로 변환한다.

    반환값:
        명시적인 반환값은 없다. DB에 연결 자산 레코드를 생성한다.
    """
    image_urls = [line.strip() for line in image_urls_text.splitlines() if line.strip()]
    for image_url in image_urls:
        ContestImage.objects.create(contest=contest, image_url=image_url)

    attachment_lines = [line.strip() for line in attachment_lines_text.splitlines() if line.strip()]
    for line in attachment_lines:
        if "|" in line:
            file_name, file_url = [part.strip() for part in line.split("|", 1)]
        else:
            file_url = line
            file_name = get_file_name_from_url(file_url)

        # Error handling:
        # 비어 있는 URL 줄은 저장할 수 있는 첨부파일이 아니므로 조용히 건너뛴다.
        if not file_url:
            continue
        if not file_name:
            file_name = get_file_name_from_url(file_url)

        ContestAttachment.objects.create(
            contest=contest,
            file_name=file_name,
            file_url=file_url,
            file_type=get_attachment_type(file_name),
        )
