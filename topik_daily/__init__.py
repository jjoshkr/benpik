"""topik-daily — TOPIK II 읽기 일일 학습 메일 (PRD v0.3).

매일 1회, 창작 지문(4급) + 문제 1문항 + 영어 번역 + 어휘 풀이를 담은
학습 메일을 생성·발송한다. 외부 패키지 없이 표준 라이브러리만 사용한다(NFR-1).
모든 순환(문법·주제·유형·기출 섹터)은 날짜 기반 계산이며 영속 저장소가 없다(NFR-3).
"""

from topik_daily.content import DailyPlan, build_plan

__all__ = ["DailyPlan", "build_plan"]
