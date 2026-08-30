# topik-daily — TOPIK II 읽기 일일 학습 메일

PRD v0.3(2026-08-27) 구현. 매일 아침 창작 지문(4급) 1개 + 문제 1문항 + 전문 영어 번역 +
지문 어휘 3~5개 + 기출 단어 10개를 담은 메일을 1인 수신자에게 발송한다.

**운영 비용 0원 설계 — 콘텐츠 뱅크.** 생성과 발송을 분리한다. 하루치 콘텐츠 JSON을
Cowork/Claude Code 세션(구독 사용량)에서 미리 만들어 `topik_daily/bank/`에 커밋해 두고,
매일 아침 워크플로는 오늘 날짜의 파일을 렌더링·발송만 한다. 뱅크에 없는 날짜만
`ANTHROPIC_API_KEY`가 있을 때 API 생성으로 폴백한다.

## 구성

| 경로 | 역할 |
|---|---|
| `topik_daily/content.py` | 날짜 기반 순환 시드 — 문법 40 × 주제 10, 지문·문제 유형 4×4, 기출 378섹터 |
| `topik_daily/bank/` | **콘텐츠 뱅크** — `YYYY-MM-DD.json` (§8 계약), 발송의 1순위 소스 |
| `topik_daily/bank.py` | 뱅크 로더 — 날짜 파일 조회·검증, 잔여일 계산(7일 이하 경고) |
| `topik_daily/generate.py` | LLM 생성 폴백 (JSON 데이터 계약 §8, fetcher 주입 가능, 실패 시 1회 재요청) |
| `topik_daily/render.py` | HTML + 평문 렌더러 (§6 메일 구조) |
| `topik_daily/mailer.py` | SMTP 발송 (`multipart/alternative`) |
| `topik_daily/__main__.py` | 진입점 `python -m topik_daily [--dry-run]` — 뱅크 → API 폴백 순 |
| `.github/workflows/topik-daily.yml` | 매일 23:30 UTC(08:30 KST) cron — 지연 흡수 후 08:45 전후 발송 |

## 뱅크 리필 절차

1. 잔여 7일 이하가 되면 워크플로 로그에 `::warning::` 경고가 뜬다 (Actions 실행 화면에 노란 배지).
2. Cowork(또는 Claude Code)에서 요청한다: **"topik 뱅크 30일치 리필해서 커밋해줘"**.
   - 각 날짜의 시드는 `build_plan(날짜)`로 뽑는다 (문법·주제·지문/문제 유형이 자동 결정됨).
   - 파일은 `topik_daily/bank/YYYY-MM-DD.json`, §8 계약 그대로, `ensure_ascii=False`.
3. `python -m pytest tests/test_topik_bank.py -q` 가 커밋 전 전량 검증한다
   (계약 위반·빈칸 누락·파일명 오류를 잡는 CI 가드).
4. 커밋·푸시하면 끝. 이 커밋이 GitHub 의 60일 무커밋 스케줄 정지도 함께 막아 준다.

외부 패키지 0개(NFR-1) — 표준 라이브러리만 사용한다. 영속 저장소 없음(NFR-3) —
모든 순환은 `Day = (날짜 − 2026-08-28) + 1` 계산으로 결정된다.

## 운영 설정

GitHub Secrets (NFR-6):

| Secret | 값 |
|---|---|
| `SMTP_USER` | 발신 계정 (예: Gmail 주소) |
| `SMTP_PASS` | Gmail 앱 비밀번호 (2단계 인증 → 앱 비밀번호 발급) |
| `ANTHROPIC_API_KEY` | (선택) 뱅크에 없는 날짜의 API 폴백. 미등록 시 뱅크 소진하면 당일 실패 |

수신자는 워크플로의 `TOPIK_TO` env 로 지정되어 있다: `benrico@handong.ac.kr`.

환경변수(선택): `TOPIK_MODEL`(기본 `claude-haiku-4-5`), `TOPIK_EPOCH`(Day 1 기준일,
기본 2026-08-28), `TOPIK_DATE`(대상 날짜 고정 — 검수용), `SMTP_HOST`/`SMTP_PORT`.

## 로컬 검증

```bash
python -m pytest tests/test_topik_*.py -q   # 로직 + 뱅크 파일 전량 검증 (네트워크 불필요)
python -m topik_daily --dry-run             # 오늘자 메일 본문을 발송 없이 확인 (뱅크 사용, 키 불필요)
```

Actions 탭에서 `topik-daily` 워크플로를 `workflow_dispatch`(dry_run 옵션 지원)로
수동 실행해 실발송을 확인할 수 있다.

## PRD 결정 기록

- **Q1 (지문 출처):** B안 — 창작 지문 채택(§4.2). 저작권 리스크 회피. 실제 기출은
  메일 하단 378섹터 순환 링크로만 병행하며, 지문·문제가 창작물임을 메일에 명시한다.
- **Q2 (문법 작문 연습):** 제거 전제대로 구현. 읽기 전용 구성.
- **선택지 영어 병기 (FR-3 수정, 2026-08-28):** 4지선다 선택지는 **한국어만** 표기한다.
  영어 번역이 정답 힌트가 된다는 운영자 판단. 데이터(뱅크 JSON)에는 `choices[].en` 을
  계속 저장하되 렌더링만 생략한다.
- **Q3 (기출 단어 출처):** (b) LLM 판단 TOPIK 빈출 어휘로 시작. 즉시 구현 가능하며,
  국립국어원 4급 어휘 목록(a안)을 확보하면 프롬프트에 목록을 주입하는 방식으로 상향 가능.
- **비용 (NFR-2 강화):** 뱅크 방식 채택으로 운영 비용 0원. 생성은 Cowork 세션
  (구독 사용량)에서 배치로 수행한다. API 폴백을 쓸 경우에만 과금되며, 기본 모델
  `claude-haiku-4-5` 기준 일 1회 약 $0.014 (`TOPIK_MODEL` 로 교체 가능).
- **발송 시각:** 목표 08:45 KST. cron 지연(5~20분)을 흡수하기 위해 23:30 UTC
  (08:30 KST)에 스케줄한다.

## 리스크 메모 (§11)

- **60일 무커밋 시 스케줄 자동 정지** — GitHub 무료 계정 정책. 2개월마다 커밋하거나
  Actions 탭에서 워크플로를 재활성화한다.
- **JSON 계약 이탈** — 1회 재요청 후에도 실패하면 당일 미발송으로 워크플로가 실패하며
  GitHub 알림으로 드러난다(NFR-4). 재시도는 다음 날 자동 순환에 맡긴다.
- **첫 메일 스팸 분류** — 첫 발송 전 수신자에게 발신 주소를 알려 주소록 등록을 권한다.
