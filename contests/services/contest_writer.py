from urllib.parse import unquote, urlparse

from django.db import transaction

from contests.models import Contest
from contests.models import ContestAttachment, ContestImage


def guess_file_name_from_url(url):
    # 첨부파일 라인에 파일명이 없는 경우 URL 마지막 경로 조각을 파일명 후보로 사용한다.
    # 예: https://example.com/files/guide.pdf -> guide.pdf
    parsed = urlparse(url)
    name = unquote(parsed.path.split("/")[-1]).strip()
    return name or "attachment"


def guess_file_type(file_name):
    # 확장자를 기준으로 대략적인 파일 종류를 분류한다.
    # 허용 목록에 없는 확장자는 일단 etc로 묶어서 저장한다.
    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    allowed = {"pdf", "hwp", "hwpx", "doc", "docx", "zip"}
    return ext if ext in allowed else "etc"


def split_prefill_data(prefill_data):
    # prefill 단계에서 만들어지는 dict는 Contest 본체 컬럼과
    # 이미지/첨부 같은 연관 데이터가 한 번에 섞여 있다.
    # 저장 전에 이 둘을 나눠 두면 본체 저장과 자산 저장 책임이 분명해지고,
    # 수동 저장/크롤러/스케줄러가 같은 저장 규칙을 재사용하기 쉬워진다.
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
        # 이미지/첨부는 Contest 컬럼이 아니라 별도 테이블로 저장되므로
        # 원본 텍스트를 따로 넘겨 save_assets()에서 풀어 쓰게 한다.
        "image_urls_text": prefill_data.get("image_urls", ""),
        "attachment_lines_text": prefill_data.get("attachment_lines", ""),
    }
    return contest_fields, asset_fields


@transaction.atomic
def create_contest_with_assets(prefill_data):
    # 공모전 본체와 연관 자산 저장을 하나의 트랜잭션으로 묶는다.
    # 중간에 첨부파일 저장이 실패하면 Contest만 덩그러니 남지 않도록
    # 전체 저장을 함께 롤백하기 위한 장치다.
    #
    # 이 함수는 "상세 페이지에서 파싱한 dict 하나를 받아 DB 저장까지 끝내는"
    # 공용 저장 진입점이다. 크롤러나 다른 진입점은 저장 방식 자체를 몰라도
    # 이 함수만 호출하면 같은 규칙으로 처리된다.
    contest_fields, asset_fields = split_prefill_data(prefill_data)

    # 먼저 Contest 본체를 저장하고,
    # 그 다음에 생성된 contest를 부모로 삼아 이미지/첨부를 연결한다.
    contest = Contest.objects.create(**contest_fields)
    save_assets(contest=contest, **asset_fields)
    return contest


def save_assets(contest, image_urls_text, attachment_lines_text):
    # textarea로 들어온 줄바꿈 텍스트를 정리해서 실제 연관 모델 레코드로 바꾼다.
    image_urls = [line.strip() for line in image_urls_text.splitlines() if line.strip()]
    for image_url in image_urls:
        ContestImage.objects.create(contest=contest, image_url=image_url)

    attachment_lines = [line.strip() for line in attachment_lines_text.splitlines() if line.strip()]
    for line in attachment_lines:
        # 첨부는 "파일명 | URL" 형식을 우선 지원한다.
        # 파일명이 없는 경우에는 URL에서 파일명을 추정해서 채운다.
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
