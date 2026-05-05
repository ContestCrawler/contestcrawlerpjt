from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import ContestCreateForm
from .services.contest_writer import save_assets
from .services.prefill import build_prefill_data


def create_contest(request):
    if request.method == "POST":
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


def prefill_contest(request):
    if request.method != "POST":
        return redirect("contests:create")

    source_url = (request.POST.get("source_url") or "").strip()
    form = ContestCreateForm(request.POST)

    if not source_url:
        form.add_error("source_url", "Please enter a prefill URL.")
        return render(request, "contests/create.html", {"form": form})

    try:
        initial_data = build_prefill_data(source_url)
    except Exception as exc:
        form.add_error("source_url", f"Could not load prefill data: {exc}")
        return render(request, "contests/create.html", {"form": form})

    messages.success(request, "Prefill loaded. Please review and save.")
    return render(request, "contests/create.html", {"form": ContestCreateForm(initial=initial_data)})
