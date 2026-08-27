"""topik_daily.generate — fetcher 주입으로 네트워크 없이 계약 검증을 테스트한다."""

import json

import pytest

from topik_daily.content import EPOCH_DATE, build_plan
from topik_daily.generate import GenerationError, build_prompt, generate_daily, validate_payload

PLAN = build_plan(EPOCH_DATE)


def valid_payload() -> dict:
    return {
        "passage_ko": "최근 기업들은 경쟁력을 높이고자 노력한다. 그 결과 시장이 변하고 있다. 소비자도 달라졌다.",
        "passage_en": "Recently, companies strive to raise competitiveness. As a result, the market is changing. Consumers have changed too.",
        "question": "위 글의 주제로 알맞은 것을 고르십시오.",
        "choices": [
            {"ko": "기업의 노력", "en": "Corporate efforts"},
            {"ko": "시장의 역사", "en": "History of the market"},
            {"ko": "경쟁과 변화", "en": "Competition and change"},
            {"ko": "소비자 불만", "en": "Consumer complaints"},
        ],
        "answer": 3,
        "explanation_ko": "글 전체가 경쟁으로 인한 변화를 다룬다. 따라서 3번이 주제다.",
        "explanation_en": "The passage is about change driven by competition.",
        "passage_vocab": [
            {"word": "경쟁력", "pos": "명사", "en": "competitiveness", "context": "경쟁력을 높이고자"},
            {"word": "노력하다", "pos": "동사", "en": "to strive", "context": "높이고자 노력한다"},
            {"word": "시장", "pos": "명사", "en": "market", "context": "시장이 변하고 있다"},
        ],
        "daily_vocab": [
            {"word": f"단어{i}", "pos": "명사", "en": f"word{i}",
             "example_ko": f"예문 {i}입니다.", "example_en": f"Example {i}."}
            for i in range(10)
        ],
    }


def test_prompt_contains_seeds():
    prompt = build_prompt(PLAN)
    for token in (PLAN.grammar, PLAN.topic, PLAN.passage_type, PLAN.question_type,
                  str(PLAN.day), "passage_vocab", "daily_vocab"):
        assert token in prompt


def test_blank_question_adds_blank_rule():
    from datetime import timedelta
    # 빈칸 유형이 걸리는 날을 찾는다
    for i in range(16):
        p = build_plan(EPOCH_DATE + timedelta(days=i))
        if p.question_type == "빈칸에 알맞은 말 넣기":
            assert "(    )" in build_prompt(p)
            return
    pytest.fail("빈칸 유형이 16일 순환에 없음")


def test_generate_success_first_try():
    calls = []

    def fetcher(prompt: str) -> str:
        calls.append(prompt)
        return json.dumps(valid_payload(), ensure_ascii=False)

    result = generate_daily(PLAN, fetcher=fetcher)
    assert result["answer"] == 3
    assert len(calls) == 1


def test_generate_accepts_code_fences():
    def fetcher(prompt: str) -> str:
        return "```json\n" + json.dumps(valid_payload(), ensure_ascii=False) + "\n```"

    assert generate_daily(PLAN, fetcher=fetcher)["answer"] == 3


def test_generate_retries_once_then_succeeds():
    calls = []

    def fetcher(prompt: str) -> str:
        calls.append(prompt)
        if len(calls) == 1:
            return "이건 JSON이 아님"
        return json.dumps(valid_payload(), ensure_ascii=False)

    assert generate_daily(PLAN, fetcher=fetcher)["answer"] == 3
    assert len(calls) == 2
    assert "재요청" in calls[1]


def test_generate_fails_after_two_attempts():
    def fetcher(prompt: str) -> str:
        return "{\"broken\": true}"

    with pytest.raises(GenerationError):
        generate_daily(PLAN, fetcher=fetcher)


@pytest.mark.parametrize("mutate", [
    lambda d: d.pop("passage_ko"),
    lambda d: d.update(answer=5),
    lambda d: d.update(answer=True),
    lambda d: d.update(choices=d["choices"][:3]),
    lambda d: d.update(passage_vocab=d["passage_vocab"][:2]),
    lambda d: d.update(daily_vocab=d["daily_vocab"][:9]),
    lambda d: d["choices"][0].update(en=""),
    lambda d: d["daily_vocab"][0].pop("example_en"),
])
def test_validate_rejects_contract_violations(mutate):
    data = valid_payload()
    mutate(data)
    with pytest.raises(ValueError):
        validate_payload(data)


def test_validate_accepts_valid():
    assert validate_payload(valid_payload())
