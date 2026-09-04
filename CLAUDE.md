# benpik — TOPIK II 읽기 일일 학습 메일

이 저장소는 단일 시스템이다: `topik_daily/` (표준 라이브러리만, GitHub Actions cron 발송).
**정본 문서는 [`docs/topik-daily.md`](docs/topik-daily.md)** — PRD 매핑·데이터 계약(§8)·
뱅크 리필 절차가 거기 있다. 이 파일의 규칙을 항상 따른다.

> 원래 `jjoshkr/josharchv`(finmodel)의 `topik_daily/` 폴더였다. 2026-09 에 topik 커밋
> 히스토리를 재생해 단독 저장소로 분리했다.

## 원칙

- 커밋 접두사는 `topik:` 을 쓴다.
- **외부 패키지 0개(NFR-1)** — 런타임 의존성을 추가하지 않는다. 테스트만 pytest.
- 비밀(SMTP·API 키)은 코드·로그에 절대 넣지 않는다(NFR-6) — GitHub Actions Secrets 로만.
- 변경 후에는 `python -m pytest -q` 를 돌린다. 뱅크 파일을 추가·수정했으면
  `tests/test_topik_bank.py` 가 계약(§8) 위반을 잡는다.

## 뱅크 리필 요청을 받으면

1. `topik_daily/content.py` 의 `build_plan(날짜)` 로 각 날짜의 시드를 뽑는다.
2. `topik_daily/bank/YYYY-MM-DD.json` 에 §8 계약 그대로, `ensure_ascii=False` 로 저장한다.
3. `python -m pytest tests/test_topik_bank.py -q` 통과를 확인하고 커밋·푸시한다.
   (이 커밋이 GitHub 의 60일 무커밋 스케줄 정지도 막는다.)
