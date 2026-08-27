"""진입점: python -m topik_daily [--dry-run]

--dry-run  생성·렌더링까지만 하고 발송 없이 평문 본문을 출력한다.
환경변수:
  ANTHROPIC_API_KEY  (필수) LLM 생성
  SMTP_USER / SMTP_PASS  (발송 시 필수) SMTP 자격증명
  TOPIK_TO    수신자 (기본 benrico@handong.ac.kr)
  TOPIK_FROM  발신자 (기본 SMTP_USER)
  TOPIK_DATE  YYYY-MM-DD 로 대상 날짜 고정 (기본: 오늘, KST)
  TOPIK_MODEL / TOPIK_EPOCH  모델·Day 1 기준일 재조정
"""

from __future__ import annotations

import os
import sys
from datetime import date, datetime, timedelta, timezone

from topik_daily.content import build_plan
from topik_daily.generate import generate_daily
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

    payload = generate_daily(plan)
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
