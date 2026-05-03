from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import ContestCreateForm
from .services.contest_writer import save_assets
from .services.prefill import build_prefill_data


def create_contest(request):
    # 단일 화면에서
    # 1) 프리필 불러오기
    # 2) 사용자 검수 후 저장
    # 두 동작을 모두 처리한다.
    if request.method == "POST":
        action = request.POST.get("action", "save")

        if action == "prefill":
            messages.info(request, "Prefill request received.")
            source_url = (request.POST.get("source_url") or "").strip()
            form = ContestCreateForm(request.POST)

            if not source_url:
                form.add_error("source_url", "Please enter a prefill URL.")
                return render(request, "contests/create.html", {"form": form})

            try:
                # 상세 URL에서 프리필 데이터 생성
                initial_data = build_prefill_data(source_url)
            except Exception as exc:
                form.add_error("source_url", f"Could not load prefill data: {exc}")
                return render(request, "contests/create.html", {"form": form})

            messages.success(request, "Prefill loaded. Please review and save.")
            return render(request, "contests/create.html", {"form": ContestCreateForm(initial=initial_data)})

        # 저장 요청: Contest 저장 후 이미지/첨부는 별도 서비스에서 저장
        form = ContestCreateForm(request.POST)
        if form.is_valid():
            contest = form.save()
            save_assets(
                contest=contest,
                image_urls_text=form.cleaned_data["image_urls"],
                attachment_lines_text=form.cleaned_data["attachment_lines"],
            )
            messages.success(request, "Contest has been saved.")
            return redirect("contests:create")
    else:
        form = ContestCreateForm()

    return render(request, "contests/create.html", {"form": form})
