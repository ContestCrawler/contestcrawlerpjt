from django import forms

from .models import Contest


class ContestCreateForm(forms.ModelForm):
    # source_url은 DB에 저장되는 Contest 필드가 아니다.
    # create 화면에서 "어느 상세 페이지를 크롤링할지" 입력받기 위한 임시 폼 필드다.
    source_url = forms.URLField(
        required=False,
        label="Prefill URL",
        widget=forms.URLInput(attrs={"placeholder": "https://.../contest-detail"}),
        help_text="상세 페이지 URL을 넣고 Load Prefill을 누르면 자동으로 입력값을 채웁니다.",
    )

    # image_urls 역시 Contest 모델 필드는 아니다.
    # 사용자가 확인/수정한 뒤 저장하면 contest_writer.save_assets()가 ContestImage로 저장한다.
    image_urls = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 4, "placeholder": "https://example.com/image1.jpg"}),
        help_text="이미지 URL을 한 줄에 하나씩 입력하세요.",
    )

    # 첨부파일도 ContestAttachment 별도 테이블로 저장되므로 textarea 보조 필드로 받는다.
    # 한 줄 형식은 "파일명 | URL"이고, 파일명이 없으면 URL만 넣어도 처리된다.
    attachment_lines = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={"rows": 6, "placeholder": "guide.pdf | https://example.com/files/guide.pdf"}
        ),
        help_text='한 줄에 하나씩 입력: "파일명 | 파일URL" 또는 "파일URL"',
    )

    class Meta:
        model = Contest
        # 실제 Contest 모델에 저장되는 필드들이다.
        # source_url/image_urls/attachment_lines는 위에서 정의한 보조 필드라 여기에 넣지 않는다.
        fields = [
            "title",
            "eligibility",
            "description",
            "category",
            "host_region",
            "organizer",
            "total_prize",
            "first_prize",
            "start_date",
            "end_date",
            "is_active",
            "detail_url",
            "content_type",
        ]
        # 날짜 필드는 브라우저 date picker를 쓰게 하고,
        # 긴 텍스트 필드는 textarea 높이를 조금 넉넉하게 잡는다.
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "eligibility": forms.Textarea(attrs={"rows": 3}),
            "description": forms.Textarea(attrs={"rows": 5}),
        }
