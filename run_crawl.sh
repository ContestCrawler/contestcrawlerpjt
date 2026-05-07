#!/usr/bin/env bash

# 에러가 발생하면 즉시 스크립트 중단
set -e

# 이 쉘스크립트가 위치한 폴더로 이동
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# 로그 폴더 생성
mkdir -p logs

# 로그 파일 경로
LOG_FILE="$PROJECT_DIR/logs/crawl.log"

echo "===================================" >> "$LOG_FILE"
echo "크롤링 시작: $(date)" >> "$LOG_FILE"

# 가상환경 실행
source "$PROJECT_DIR/venv/Script/activate"

# Django Management Command 실행
python manage.py crawl_contests >> "$LOG_FILE" 2>&1

echo "크롤링 완료: $(date)" >> "$LOG_FILE"
echo "===================================" >> "$LOG_FILE"