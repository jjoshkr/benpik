"""진입점: python -m topik_daily [--dry-run]

--dry-run  콘텐츠 준비·렌더링까지만 하고 발송 없이 평문 본문을 출력한다.

콘텐츠는 뱅크(topik_daily/bank/YYYY-MM-DD.json) 우선이다 — 이 경로면 API 비용 0.
뱅크에 없는 날짜만 ANTHROPIC_API_KEY 가 있을 때 API 생성으로 폴백한다.

환경변수:
  SMTP_USER / SMTP_PASS  (발송 시 필수) SMTP 자격증명
  ANTHROPIC_API_KEY  (선택) 뱅크에 없는 날짜의 API 폴백
  TOPIK_TO    수신자 (기본 benrico@handong.ac.kr)
  TOPIK_FROM  발신자 (기본 SMTP_USER)
  TOPIK_DATE  YYYY-MM-DD 로 대상 날짜 고정 (기본: 오늘, KST)
  TOPIK_MODEL / TOPIK_EPOCH  모델·Day 1 기준일 재조정
"""

from __future__ import annotations

import os
import sys
from datetime import date, datetime, timedelta, timezone

from topik_daily.bank import REFILL_WARNING_DAYS, days_remaining, load_entry
from topik_daily.content import build_plan
from topik_daily.generate import GenerationError, generate_daily
from topik_daily.mailer import DEFAULT_TO, build_message, send
from topik_daily.render import render_html, render_text, subject

KST = timezone(timedelta(hours=9))


def _target_date() -> date:
    raw = os.environ.get("TOPIK_DATE", "")
    return date.fromisoformat(raw) if raw else datetime.now(KST).date()


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    dry_run = "--dry-run" in args

    plan = build_plan(_target_date())
    print(f"[topik-daily] Day {plan.day} · {plan.target_date} · {plan.passage_type} · "
          f"{plan.question_type} · {plan.grammar} · {plan.topic} · {plan.exam_label}")

    payload = load_entry(plan.target_date)
    if payload is not None:
        remaining = days_remaining(plan.target_date)
        print(f"[topik-daily] 뱅크 사용 · 잔여 {remaining}일")
        if remaining <= REFILL_WARNING_DAYS:
            # GitHub Actions 로그에 노란 경고 배지로 표시된다
            print(f"::warning::topik 콘텐츠 뱅크 잔여 {remaining}일 — "
                  f"Cowork 에서 다음 구간을 리필해 커밋하세요 (docs/topik-daily.md)")
    elif os.environ.get("ANTHROPIC_API_KEY"):
        print("[topik-daily] 뱅크에 없는 날짜 — API 생성 폴백")
        payload = generate_daily(plan)
    else:
        raise GenerationError(
            f"뱅크에 {plan.target_date} 파일이 없고 ANTHROPIC_API_KEY 도 없다. "
            "Cowork 에서 뱅크를 리필해 커밋하거나 API 키를 설정하라."
        )
    text = render_text(plan, payload)
    html = render_html(plan, payload)
    subj = subject(plan)

    if dry_run:
        print(f"\n제목: {subj}\n")
        print(text)
        return 0

    to = os.environ.get("TOPIK_TO", DEFAULT_TO)
    sender = os.environ.get("TOPIK_FROM") or os.environ.get("SMTP_USER", "")
    msg = build_message(subj, text, html, sender, to)
    send(msg)
    print(f"[topik-daily] 발송 완료 → {to} ({subj})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
