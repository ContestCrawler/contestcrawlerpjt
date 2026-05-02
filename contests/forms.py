from django import forms

from .models import Contest


class ContestCreateForm(forms.ModelForm):
    # 프리필 대상 상세 URL 입력 필드
    source_url = forms.URLField(
        required=False,
        label="Prefill URL",
        widget=forms.URLInput(attrs={"placeholder": "https://.../contest-detail"}),
        help_text="상세 페이지 URL을 넣고 Load Prefill을 누르면 자동 채움됩니다.",
    )

    # 이미지 URL 다건 입력(줄바꿈 구분)
    image_urls = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 4, "placeholder": "https://example.com/image1.jpg"}),
        help_text="이미지 URL을 한 줄에 하나씩 입력하세요.",
    )

    # 첨부파일 다건 입력(파일명|URL 또는 URL 단독)
    attachment_lines = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={"rows": 6, "placeholder": "guide.pdf | https://example.com/files/guide.pdf"}
        ),
        help_text='한 줄에 하나씩 입력: "파일명 | 파일URL" 또는 "파일URL"',
    )

    class Meta:
        model = Contest
        # 실제 DB에 저장되는 Contest 필드
        fields = [
            "title",
            "eligibility",
            "description",
            "category",
            "region",
            "start_date",
            "end_date",
            "is_active",
            "detail_url",
            "content_type",
        ]
        # 날짜/장문 필드 입력 편의 위젯
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "eligibility": forms.Textarea(attrs={"rows": 3}),
            "description": forms.Textarea(attrs={"rows": 5}),
        }
