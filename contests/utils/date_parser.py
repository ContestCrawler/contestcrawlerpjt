from datetime import datetime


def parse_period(period_text):
    # period_text 예: "2026-05-01 ~ 2026-05-31"
    #
    # "~" in 문자열:
    # - 구분자가 없으면 기대 형식이 아니므로 즉시 실패 처리
    if "~" not in period_text:
        return None, None

    # split("~"):
    # - 시작일/종료일 텍스트 분리
    start_text, end_text = period_text.split("~")

    # strip():
    # - 좌우 공백 제거 (UI 문구에서 흔히 포함됨)
    start_text = start_text.strip()
    end_text = end_text.strip()

    try:
        # datetime.strptime():
        # - 지정 포맷("%Y-%m-%d")으로 문자열을 datetime으로 파싱
        # .date():
        # - 시간정보 제거 후 date 타입으로 변환
        start_date = datetime.strptime(start_text, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_text, "%Y-%m-%d").date()
        return start_date, end_date
    except ValueError:
        # 포맷 불일치/존재하지 않는 날짜(예: 2026-02-30)는 ValueError
        return None, None
