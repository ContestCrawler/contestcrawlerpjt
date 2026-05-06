from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import ContestCreateForm
from .services.crawling.wevity import crawl_wevity_list
from .services.prefilling.url_rules import is_wevity_list_url


def create_contest(request):
    # 현재 create 화면은 수동 입력 화면이라기보다
    # "위비티 리스트 URL을 넣고 크롤링을 시작하는 진입점" 역할만 맡는다.
    # 실제 Contest 데이터 생성은 크롤러가 상세 페이지를 순회하면서 자동으로 처리한다.
    form = ContestCreateForm()
    return render(request, "contests/create.html", {"form": form})


def prefill_contest(request):
    if request.method != "POST":
        return redirect("contests:create")

    form = ContestCreateForm(request.POST)
    source_url = (request.POST.get("source_url") or "").strip()

    if not is_wevity_list_url(source_url):
        # 위비티 URL이 아닌 경우 에러 처리
        form.add_error("source_url", "Please enter a Wevity list URL.")
        return render(request, "contests/create.html", {"form": form})

    try:
        
        # 수동 실행이든 나중의 스케줄러 실행이든
        # 실제 수집 로직은 동일한 크롤러 진입점을 사용하도록 맞춘다.
        crawl_wevity_list(source_url) # 여기서 리스트 페이지 전달
        
    # 에러 처리
    except ValueError as exc:
        form.add_error("source_url", str(exc))
        return render(request, "contests/create.html", {"form": form})
    except Exception as exc:
        form.add_error("source_url", f"Could not crawl Wevity list page: {exc}")
        return render(request, "contests/create.html", {"form": form})

    return redirect("contests:create")
