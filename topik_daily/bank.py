"""콘텐츠 뱅크 — 미리 생성해 저장소에 커밋해 둔 하루치 JSON을 읽는다.

`topik_daily/bank/YYYY-MM-DD.json` 파일이 그날의 콘텐츠다.
매일 아침 워크플로는 API 호출 없이 이 파일을 렌더링·발송만 하므로 운영 비용이 0이다.
뱅크가 없는 날짜는 API 폴백(generate)으로 넘어가거나, 키가 없으면 실패한다.

리필: Cowork/Claude Code 세션에서 다음 구간을 생성해 커밋한다(docs/topik-daily.md 참고).
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from topik_daily.generate import GenerationError, validate_payload

BANK_DIR = Path(__file__).resolve().parent / "bank"

# 잔여분이 이 이하로 내려가면 워크플로 로그에 경고를 띄운다
REFILL_WARNING_DAYS = 7


def entry_path(d: date, bank_dir: Path = BANK_DIR) -> Path:
    return bank_dir / f"{d.isoformat()}.json"


def load_entry(d: date, bank_dir: Path = BANK_DIR) -> dict | None:
    """해당 날짜의 뱅크 콘텐츠. 파일이 없으면 None, 계약 위반이면 예외."""
    path = entry_path(d, bank_dir)
    if not path.exists():
        return None
    try:
        return validate_payload(json.loads(path.read_text(encoding="utf-8")))
    except (ValueError, json.JSONDecodeError) as e:
        raise GenerationError(f"뱅크 파일이 데이터 계약을 어겼다 ({path.name}): {e}") from e


def days_remaining(d: date, bank_dir: Path = BANK_DIR) -> int:
    """오늘부터 빈 날 없이 연속으로 준비된 일수 (오늘 포함)."""
    n = 0
    while entry_path(d + timedelta(days=n), bank_dir).exists():
        n += 1
    return n
