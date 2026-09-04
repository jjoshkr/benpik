# benpik — TOPIK II 읽기 일일 학습 메일

매일 아침 08:45(KST) 전후, TOPIK II 4급 수준의 창작 지문 + 문제 + 번역 + 어휘를 담은
학습 메일을 발송하는 자동화 저장소다. **운영 비용 0원** — 하루치 콘텐츠를 미리 만들어
`topik_daily/bank/`에 커밋해 두고, GitHub Actions 는 렌더링·발송만 한다.

> `jjoshkr/josharchv` 저장소의 `topik_daily/` 로 시작했고, 2026-09 에 커밋 히스토리를
> 보존해 단독 저장소로 분리했다. 상세 설계·운영 절차 정본은
> [`docs/topik-daily.md`](docs/topik-daily.md).

## 빠른 확인

```bash
python -m pytest -q              # 콘텐츠 계약·렌더러·뱅크 전량 검증
python -m topik_daily --dry-run  # 발송 없이 오늘자 생성 결과 출력
```

## 운영 설정 (GitHub → Settings → Secrets and variables → Actions)

| Secret | 용도 |
|---|---|
| `SMTP_USER` | 발신 계정 (예: Gmail 주소) |
| `SMTP_PASS` | 앱 비밀번호 |
| `ANTHROPIC_API_KEY` | (선택) 뱅크에 없는 날짜의 API 생성 폴백 |

수신자는 워크플로의 `TOPIK_TO` 환경변수로 지정한다
([`.github/workflows/topik-daily.yml`](.github/workflows/topik-daily.yml)).

## 뱅크 리필

잔여 7일 이하가 되면 Actions 로그에 경고가 뜬다. Cowork/Claude Code 세션에서
"topik 뱅크 30일치 리필해서 커밋해줘"라고 요청하면 된다 — 절차는
[`docs/topik-daily.md`](docs/topik-daily.md)의 "뱅크 리필 절차" 참고.
