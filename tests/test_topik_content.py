"""topik_daily.content — 날짜 기반 순환 테스트."""

from datetime import date, timedelta

from topik_daily.content import (
    EPOCH_DATE,
    EXAM_ROUNDS,
    GRAMMAR,
    PASSAGE_TYPES,
    QUESTION_TYPES,
    SECTORS,
    TOPICS,
    TOTAL_SECTORS,
    build_plan,
)


def test_seed_counts():
    assert len(GRAMMAR) == 40
    assert len(TOPICS) == 10
    assert len(PASSAGE_TYPES) == 4
    assert len(QUESTION_TYPES) == 4
    assert len(EXAM_ROUNDS) == 9


def test_sectors_structure():
    # 회차당 42섹터 — 세트(19~20 등)를 존중해 묶는다(§4.3)
    assert len(SECTORS) == 42
    assert TOTAL_SECTORS == 378
    # 전 문항 1~50 이 빠짐없이 정확히 한 번씩 덮인다
    covered = [q for start, end in SECTORS for q in range(start, end + 1)]
    assert covered == list(range(1, 51))
    # 세트 경계
    assert (19, 20) in SECTORS
    assert (48, 50) in SECTORS
    assert (19, 19) not in [s for s in SECTORS]


def test_day_one_is_epoch():
    plan = build_plan(EPOCH_DATE)
    assert plan.day == 1
    assert plan.grammar == GRAMMAR[0]
    assert plan.topic == TOPICS[0]
    assert plan.exam_round == EXAM_ROUNDS[0]
    assert (plan.exam_start, plan.exam_end) == (1, 1)


def test_sector_cycle_boundaries():
    # 1일차 / 378일차 / 379일차 (§12 단계 4 경계값)
    d1 = build_plan(EPOCH_DATE)
    d378 = build_plan(EPOCH_DATE + timedelta(days=377))
    d379 = build_plan(EPOCH_DATE + timedelta(days=378))
    assert (d1.exam_round, d1.exam_start) == (EXAM_ROUNDS[0], 1)
    assert d378.exam_round == EXAM_ROUNDS[-1]
    assert (d378.exam_start, d378.exam_end) == (48, 50)  # 마지막 섹터
    # 379일차는 처음으로 되돌아온다
    assert (d379.exam_round, d379.exam_start, d379.exam_end) == (EXAM_ROUNDS[0], 1, 1)
    assert d379.day == 379  # Day 번호는 계속 증가


def test_exam_label_format():
    single = build_plan(EPOCH_DATE)
    assert single.exam_label == f"제{EXAM_ROUNDS[0]}회 TOPIK II 읽기 1번"
    # 19번째 섹터 = 19~20번 세트 (idx 18)
    set_plan = build_plan(EPOCH_DATE + timedelta(days=18))
    assert set_plan.exam_label == f"제{EXAM_ROUNDS[0]}회 TOPIK II 읽기 19~20번"


def test_question_type_offset_from_passage_type():
    # 지문 유형(4주기)과 문제 유형(4일마다 전진)이 16일 안에 16개 조합을 모두 낸다
    combos = set()
    for i in range(16):
        p = build_plan(EPOCH_DATE + timedelta(days=i))
        combos.add((p.passage_type, p.question_type))
    assert len(combos) == 16


def test_determinism():
    d = date(2027, 3, 1)
    assert build_plan(d) == build_plan(d)


def test_epoch_env_override(monkeypatch):
    monkeypatch.setenv("TOPIK_EPOCH", "2026-09-01")
    plan = build_plan(date(2026, 9, 1))
    assert plan.day == 1
