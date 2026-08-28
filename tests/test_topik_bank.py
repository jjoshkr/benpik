"""topik_daily.bank — 뱅크 로더 + 커밋된 뱅크 파일 전량 검증(CI 가드)."""

import json
import re
from datetime import date, timedelta

import pytest

from topik_daily.bank import BANK_DIR, days_remaining, load_entry
from topik_daily.content import build_plan
from topik_daily.generate import GenerationError
from tests.test_topik_generate import valid_payload

D = date(2026, 8, 28)


def _write(bank_dir, d, data):
    (bank_dir / f"{d.isoformat()}.json").write_text(
        json.dumps(data, ensure_ascii=False), encoding="utf-8"
    )


def test_load_entry_missing_returns_none(tmp_path):
    assert load_entry(D, bank_dir=tmp_path) is None


def test_load_entry_valid(tmp_path):
    _write(tmp_path, D, valid_payload())
    assert load_entry(D, bank_dir=tmp_path)["answer"] == 3


def test_load_entry_contract_violation_raises(tmp_path):
    bad = valid_payload()
    bad["answer"] = 9
    _write(tmp_path, D, bad)
    with pytest.raises(GenerationError):
        load_entry(D, bank_dir=tmp_path)


def test_days_remaining_counts_consecutive(tmp_path):
    for i in (0, 1, 2, 4):  # 3일차에 구멍
        _write(tmp_path, D + timedelta(days=i), valid_payload())
    assert days_remaining(D, bank_dir=tmp_path) == 3
    assert days_remaining(D + timedelta(days=10), bank_dir=tmp_path) == 0


# ---- 커밋된 실제 뱅크 파일 전량 검증 — 리필 커밋의 CI 가드 ----

BANK_FILES = sorted(BANK_DIR.glob("*.json")) if BANK_DIR.exists() else []


def test_bank_exists():
    assert BANK_FILES, "콘텐츠 뱅크가 비어 있다 — topik_daily/bank/ 에 최소 1일치 필요"


@pytest.mark.parametrize("path", BANK_FILES, ids=lambda p: p.name)
def test_bank_file_valid(path):
    # 파일명이 ISO 날짜여야 한다
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}\.json", path.name)
    d = date.fromisoformat(path.stem)
    payload = load_entry(d)  # 데이터 계약 검증 포함
    plan = build_plan(d)
    # 빈칸 유형인 날은 지문에 빈칸 표기가 있어야 한다
    if plan.question_type == "빈칸에 알맞은 말 넣기":
        assert "(    )" in payload["passage_ko"], f"{path.name}: 빈칸 '(    )' 누락"
