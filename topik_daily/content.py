"""날짜 기반 순환 콘텐츠 시드 — 문법·주제·지문 유형·문제 유형·기출 섹터.

영속 저장소 없이(NFR-3) 날짜만으로 모든 순환을 결정한다.
Day 1 = EPOCH_DATE. 같은 날짜는 언제 실행해도 같은 시드를 낸다.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date

# 첫 발송일 = Day 1. TOPIK_EPOCH(YYYY-MM-DD) 환경변수로 재조정 가능.
EPOCH_DATE = date(2026, 8, 28)

# 4급 목표 문법 포인트 40개 (v0.2의 GRAMMAR 40개 순환 유지)
GRAMMAR: tuple[str, ...] = (
    "-는 바람에", "-느라고", "-는 대신에", "-을 뿐만 아니라",
    "-기 마련이다", "-는 셈이다", "-는 척하다", "-을 리가 없다",
    "-고자", "-도록", "-더니", "-았/었더니",
    "-다가는", "-는 한", "-을수록", "-는 반면에",
    "-음에도 불구하고", "-기는커녕", "-을 정도로", "-다시피",
    "-는 데다가", "-기 나름이다", "-는 탓에", "-는 덕분에",
    "-을 겸", "-는 김에", "-다 보니", "-다 보면",
    "-기에는", "-으로 인해", "-에 따르면", "-을 비롯해서",
    "-에 비해", "-치고", "-는 만큼", "-을 만하다",
    "-기 십상이다", "-는 법이다", "-으나 마나", "-을 지경이다",
)

# 주제 10개 (v0.2의 TOPIC 10개 순환 유지)
TOPICS: tuple[str, ...] = (
    "환경과 기후", "경제와 소비", "과학과 기술", "건강과 의학",
    "교육과 학습", "문화와 예술", "사회 문제", "일과 직장",
    "여가와 여행", "인간관계와 심리",
)

# FR-1: 지문 유형 — 기출 분포를 따라 순환
PASSAGE_TYPES: tuple[str, ...] = ("설명문", "신문 기사", "수필", "안내문")

# FR-2: 문제 유형 — 기출 대표 유형 순환
QUESTION_TYPES: tuple[str, ...] = (
    "주제 고르기", "일치하는 내용 고르기", "빈칸에 알맞은 말 넣기", "필자의 태도 고르기",
)

# §4.3: 공개 기출 9회차. 회차당 42섹터 → 총 378섹터 순환.
EXAM_ROUNDS: tuple[int, ...] = (35, 36, 37, 41, 47, 52, 60, 64, 83)

# 읽기 50문항 중 지문 공유 세트(시작 번호 → 끝 번호)
_QUESTION_SETS: dict[int, int] = {19: 20, 21: 22, 23: 24, 42: 43, 44: 45, 46: 47, 48: 50}

EXAM_ARCHIVE_URL = "https://www.topik.go.kr/TWSTDY/TWSTDY0080.do"


def build_sectors() -> tuple[tuple[int, int], ...]:
    """회차 1개의 42개 섹터를 시험 순서대로 (시작, 끝) 튜플로 만든다."""
    sectors: list[tuple[int, int]] = []
    q = 1
    while q <= 50:
        end = _QUESTION_SETS.get(q, q)
        sectors.append((q, end))
        q = end + 1
    return tuple(sectors)


SECTORS = build_sectors()
TOTAL_SECTORS = len(EXAM_ROUNDS) * len(SECTORS)  # 378


@dataclass(frozen=True)
class DailyPlan:
    """하루치 발송에 필요한 모든 시드."""

    day: int                # Day 번호 (Day 1 = EPOCH_DATE)
    target_date: date
    grammar: str
    topic: str
    passage_type: str
    question_type: str
    exam_round: int         # 참고 기출 회차
    exam_start: int         # 참고 기출 문항 시작 번호
    exam_end: int           # 참고 기출 문항 끝 번호
    exam_url: str = EXAM_ARCHIVE_URL

    @property
    def exam_label(self) -> str:
        if self.exam_start == self.exam_end:
            return f"제{self.exam_round}회 TOPIK II 읽기 {self.exam_start}번"
        return f"제{self.exam_round}회 TOPIK II 읽기 {self.exam_start}~{self.exam_end}번"


def _epoch() -> date:
    raw = os.environ.get("TOPIK_EPOCH", "")
    return date.fromisoformat(raw) if raw else EPOCH_DATE


def build_plan(target_date: date) -> DailyPlan:
    """날짜 하나로 그날의 모든 시드를 결정한다."""
    idx = (target_date - _epoch()).days  # Day 1 → idx 0
    sector_idx = idx % TOTAL_SECTORS
    start, end = SECTORS[sector_idx % len(SECTORS)]
    return DailyPlan(
        day=idx + 1,
        target_date=target_date,
        grammar=GRAMMAR[idx % len(GRAMMAR)],
        topic=TOPICS[idx % len(TOPICS)],
        passage_type=PASSAGE_TYPES[idx % len(PASSAGE_TYPES)],
        # 지문 유형과 같은 주기로 돌면 조합이 고정되므로 4일 단위로 어긋나게 돈다.
        question_type=QUESTION_TYPES[(idx // len(PASSAGE_TYPES)) % len(QUESTION_TYPES)],
        exam_round=EXAM_ROUNDS[sector_idx // len(SECTORS)],
        exam_start=start,
        exam_end=end,
    )
