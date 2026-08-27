"""LLM 생성 — JSON 데이터 계약(§8) 기반.

fetcher(프롬프트 → 모델 응답 텍스트)를 주입할 수 있어 네트워크 없이 픽스처로
테스트한다. 기본 fetcher는 Anthropic Messages API를 표준 라이브러리(urllib)로
호출한다(NFR-1: 외부 패키지 0개).

파싱·검증 실패 시 1회만 재요청하고, 그래도 실패하면 예외를 던져 워크플로를
중단한다(§8 — 잘못된 메일을 보내느니 안 보낸다).
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Callable

from topik_daily.content import DailyPlan

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"
# NFR-2(월 1천 원 미만)에 맞춘 기본 모델. TOPIK_MODEL 환경변수로 교체 가능.
DEFAULT_MODEL = "claude-haiku-4-5"
MAX_TOKENS = 4096

Fetcher = Callable[[str], str]


class GenerationError(RuntimeError):
    """생성·파싱·검증이 최종 실패했을 때. 워크플로 실패로 이어진다(NFR-4)."""


_SCHEMA_EXAMPLE = """{
  "passage_ko": "...",
  "passage_en": "...",
  "question": "...",
  "choices": [
    {"ko": "...", "en": "..."},
    {"ko": "...", "en": "..."},
    {"ko": "...", "en": "..."},
    {"ko": "...", "en": "..."}
  ],
  "answer": 3,
  "explanation_ko": "...",
  "explanation_en": "...",
  "passage_vocab": [
    {"word": "경쟁력", "pos": "명사", "en": "competitiveness", "context": "지문 내 쓰임"}
  ],
  "daily_vocab": [
    {"word": "유지하다", "pos": "동사", "en": "to maintain",
     "example_ko": "...", "example_en": "..."}
  ]
}"""


def build_prompt(plan: DailyPlan) -> str:
    blank_rule = (
        "- 문제 유형이 빈칸 넣기이므로 지문 안에 빈칸을 '(    )' 하나로 표시한다.\n"
        if plan.question_type == "빈칸에 알맞은 말 넣기"
        else ""
    )
    return f"""당신은 TOPIK II 읽기 영역 출제·교육 전문가다. 영어권 4급 준비 학습자를 위한
하루치 학습 자료를 만든다.

[오늘의 시드 — 반복 억제용]
- 날짜: {plan.target_date.isoformat()} (Day {plan.day})
- 주제: {plan.topic}
- 문법 포인트: {plan.grammar}
- 지문 유형: {plan.passage_type}
- 문제 유형: {plan.question_type}

[지문 조건 — FR-1]
- TOPIK II 4급 수준의 한국어 지문을 새로 창작한다. 실제 기출 지문을 복제하지 않는다.
- 분량은 3~5문장. 유형은 '{plan.passage_type}' 형식을 따른다.
- 문법 포인트 '{plan.grammar}'를 지문에 자연스럽게 1회 이상 사용한다.
{blank_rule}
[문제 조건 — FR-2]
- '{plan.question_type}' 유형의 객관식 1문항, 선택지 4개.
- answer 는 정답 선택지 번호(1~4)의 정수.
- explanation_ko 는 한국어 해설 2~3문장, explanation_en 은 영어 요약 1문장.

[번역 조건 — FR-3]
- passage_en 은 지문 전문의 자연스러운 영어 번역. 원문 문장 순서를 유지한다.
- 선택지 4개 모두 en 에 영어 번역을 병기한다.

[지문 어휘 조건 — FR-4]
- passage_vocab: 지문에서 4급 이상 수준의 한자어·추상명사·관용 표현을 3~5개 선별한다.
  3급 이하 기초 어휘는 제외한다. context 에는 지문 속 해당 구절을 짧게 인용한다.

[기출 단어 조건 — FR-5]
- daily_vocab: 지문과 독립적인 TOPIK 빈출 어휘 정확히 10개.
- 주제 '{plan.topic}'와 느슨하게 연관시키되, Day {plan.day} 시드를 기준으로 매일
  다른 구간의 단어를 골라 최근 발송분과 겹치지 않게 한다.
- 각 항목: 단어·품사·영어 뜻·한국어 예문 1개·예문의 영어 번역.

[출력 형식 — §8 데이터 계약]
아래 스키마의 JSON 객체 하나만 출력한다. 코드펜스·설명·주석 없이 JSON만 출력한다.
{_SCHEMA_EXAMPLE}"""


def _strip_fences(text: str) -> str:
    """모델이 코드펜스를 붙였을 때를 대비해 첫 '{'부터 마지막 '}'까지 자른다."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("응답에 JSON 객체가 없다")
    return text[start : end + 1]


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


def validate_payload(data: dict) -> dict:
    """§8 데이터 계약 검증. 실패 시 ValueError."""
    _require(isinstance(data, dict), "최상위가 JSON 객체가 아니다")
    for key in ("passage_ko", "passage_en", "question", "explanation_ko", "explanation_en"):
        _require(isinstance(data.get(key), str) and data[key].strip() != "", f"{key} 누락 또는 빈 문자열")

    choices = data.get("choices")
    _require(isinstance(choices, list) and len(choices) == 4, "choices 는 4개여야 한다")
    for i, c in enumerate(choices, 1):
        _require(isinstance(c, dict), f"choices[{i}] 형식 오류")
        _require(isinstance(c.get("ko"), str) and c["ko"].strip() != "", f"choices[{i}].ko 누락")
        _require(isinstance(c.get("en"), str) and c["en"].strip() != "", f"choices[{i}].en 누락")

    answer = data.get("answer")
    _require(isinstance(answer, int) and not isinstance(answer, bool) and 1 <= answer <= 4,
             "answer 는 1~4 정수여야 한다")

    vocab = data.get("passage_vocab")
    _require(isinstance(vocab, list) and 3 <= len(vocab) <= 5, "passage_vocab 은 3~5개여야 한다")
    for i, v in enumerate(vocab, 1):
        _require(isinstance(v, dict), f"passage_vocab[{i}] 형식 오류")
        for key in ("word", "pos", "en", "context"):
            _require(isinstance(v.get(key), str) and v[key].strip() != "",
                     f"passage_vocab[{i}].{key} 누락")

    daily = data.get("daily_vocab")
    _require(isinstance(daily, list) and len(daily) == 10, "daily_vocab 은 정확히 10개여야 한다")
    for i, v in enumerate(daily, 1):
        _require(isinstance(v, dict), f"daily_vocab[{i}] 형식 오류")
        for key in ("word", "pos", "en", "example_ko", "example_en"):
            _require(isinstance(v.get(key), str) and v[key].strip() != "",
                     f"daily_vocab[{i}].{key} 누락")

    return data


def default_fetcher(prompt: str) -> str:
    """Anthropic Messages API 호출 (표준 라이브러리만 사용)."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise GenerationError("ANTHROPIC_API_KEY 가 설정되지 않았다")
    body = json.dumps({
        "model": os.environ.get("TOPIK_MODEL", DEFAULT_MODEL),
        "max_tokens": MAX_TOKENS,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=body,
        method="POST",
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": API_VERSION,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:500]
        raise GenerationError(f"API 오류 HTTP {e.code}: {detail}") from e
    except urllib.error.URLError as e:
        raise GenerationError(f"API 연결 실패: {e.reason}") from e

    if payload.get("stop_reason") == "refusal":
        raise GenerationError("모델이 요청을 거부했다 (stop_reason=refusal)")
    texts = [b.get("text", "") for b in payload.get("content", []) if b.get("type") == "text"]
    if not texts:
        raise GenerationError("API 응답에 텍스트 블록이 없다")
    return "".join(texts)


def generate_daily(plan: DailyPlan, fetcher: Fetcher | None = None) -> dict:
    """하루치 콘텐츠를 생성한다. 파싱/검증 실패 시 1회 재요청 후 예외(§8)."""
    fetch = fetcher or default_fetcher
    prompt = build_prompt(plan)
    last_error: Exception | None = None
    for attempt in (1, 2):
        ask = prompt if attempt == 1 else (
            prompt + f"\n\n[재요청] 직전 응답이 데이터 계약을 어겼다: {last_error}\n"
            "이번에는 스키마를 정확히 지킨 JSON 객체 하나만 출력하라."
        )
        raw = fetch(ask)
        try:
            return validate_payload(json.loads(_strip_fences(raw)))
        except (ValueError, json.JSONDecodeError) as e:
            last_error = e
    raise GenerationError(f"JSON 계약 검증 2회 실패: {last_error}")
