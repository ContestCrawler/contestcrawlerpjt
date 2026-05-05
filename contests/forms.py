from django import forms

from .models import Contest


class ContestCreateForm(forms.ModelForm):
    source_url = forms.URLField(
        required=False,
        label="Wevity List URL",
        widget=forms.URLInput(attrs={"placeholder": "https://www.wevity.com/?c=find&s=1&gub=1&cidx=20"}),
        help_text="위비티 분야별 리스트 URL을 입력하면 상세 공모전들을 자동 수집합니다.",
    )

    image_urls = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 4, "placeholder": "https://example.com/image1.jpg"}),
        help_text="이미지 URL은 한 줄에 하나씩 입력하세요.",
    )

    attachment_lines = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={"rows": 6, "placeholder": "guide.pdf | https://example.com/files/guide.pdf"}
        ),
        help_text='한 줄에 하나씩 입력: "파일명 | 파일URL" 또는 "파일URL"',
    )

    class Meta:
        model = Contest
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
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "eligibility": forms.Textarea(attrs={"rows": 3}),
            "description": forms.Textarea(attrs={"rows": 5}),
        }
