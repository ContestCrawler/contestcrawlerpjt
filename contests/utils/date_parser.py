from datetime import datetime


def parse_period(period_text):
    # "YYYY-MM-DD ~ YYYY-MM-DD" 문자열을 date 2개로 변환한다.
    # 형식이 다르면 (None, None) 반환.
    if "~" not in period_text:
        return None, None

    start_text, end_text = period_text.split("~")
    start_text = start_text.strip()
    end_text = end_text.strip()

    try:
        start_date = datetime.strptime(start_text, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_text, "%Y-%m-%d").date()
        return start_date, end_date
    except ValueError:
        return None, None
