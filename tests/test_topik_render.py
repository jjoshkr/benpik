"""topik_daily.render / mailer — 메일 구조(§6)와 multipart 조립을 테스트한다."""

from topik_daily.content import EPOCH_DATE, build_plan
from topik_daily.mailer import build_message
from topik_daily.render import render_html, render_text, subject
from tests.test_topik_generate import valid_payload

PLAN = build_plan(EPOCH_DATE)
PAYLOAD = valid_payload()


def test_subject_format():
    s = subject(PLAN)
    assert s.startswith("[TOPIK] ")
    assert f"Day {PLAN.day}" in s
    assert PLAN.question_type in s
    assert f"{PLAN.target_date.month:02d}/{PLAN.target_date.day:02d}" in s


def test_text_section_order():
    text = render_text(PLAN, PAYLOAD)
    order = ["오늘의 지문", "English Translation", "지문 어휘",
             "오늘의 기출 단어 10", "정답 및 해설", "참고 기출"]
    positions = [text.index(k) for k in order]
    assert positions == sorted(positions), "§6 섹션 순서가 어긋남"
    # 정답은 지문·선택지보다 뒤에 있어야 한다(FR-2)
    assert text.index("정답:") > text.index(PAYLOAD["choices"][3]["ko"])


def test_text_contains_all_content():
    text = render_text(PLAN, PAYLOAD)
    assert PAYLOAD["passage_ko"] in text
    assert PAYLOAD["passage_en"] in text
    assert PAYLOAD["question"] in text
    # 선택지는 한국어만 — 영어 병기는 힌트가 되므로 렌더링하지 않는다
    for c in PAYLOAD["choices"]:
        assert c["ko"] in text
        assert c["en"] not in text
    assert "③" in text  # answer=3
    assert PLAN.exam_label in text
    assert PLAN.exam_url in text
    for v in PAYLOAD["daily_vocab"]:
        assert v["word"] in text and v["example_en"] in text


def test_html_structure_and_escaping():
    p = dict(PAYLOAD)
    p["passage_ko"] = "기업은 <성장>했다 & 변했다."
    html = render_html(PLAN, p)
    assert "&lt;성장&gt;" in html and "&amp;" in html
    assert "<성장>" not in html
    # HTML 에서도 선택지 영어는 렌더링하지 않는다
    for c in p["choices"]:
        assert c["en"] not in html
    # 정답 섹션이 기출 단어 섹션보다 뒤
    assert html.index("정답 및 해설") > html.index("오늘의 기출 단어 10")
    assert PLAN.exam_url in html


def test_build_message_multipart_alternative():
    msg = build_message("제목", "평문 본문", "<p>HTML 본문</p>",
                        sender="a@example.com", to="b@example.com")
    assert msg["Subject"] == "제목"
    assert msg["From"] == "a@example.com"
    assert msg["To"] == "b@example.com"
    assert msg.get_content_type() == "multipart/alternative"
    parts = list(msg.iter_parts())
    assert [p.get_content_type() for p in parts] == ["text/plain", "text/html"]
    # UTF-8 왕복 (NFR-5)
    raw = msg.as_bytes()
    assert b"multipart/alternative" in raw
