"""메일 렌더링 — §6 메일 구조 명세.

HTML 과 평문 대체본을 함께 만든다(FR-7, multipart/alternative 는 mailer 담당).
정답·해설은 반드시 스크롤 아래(기출 단어 다음)에 배치한다(FR-2).
"""

from __future__ import annotations

import html as _html

from topik_daily.content import DailyPlan

CIRCLED = ("①", "②", "③", "④")
DIVIDER = "─" * 29


def subject(plan: DailyPlan) -> str:
    """예: [TOPIK] 08/27 · Day 12 — 읽기 (주제 고르기)"""
    d = plan.target_date
    return f"[TOPIK] {d.month:02d}/{d.day:02d} · Day {plan.day} — 읽기 ({plan.question_type})"


def render_text(plan: DailyPlan, p: dict) -> str:
    """평문 대체본 — §6 레이아웃을 그대로 따른다."""
    lines: list[str] = []

    def section(title: str) -> None:
        lines.extend([DIVIDER, title, DIVIDER])

    section(f"📖 오늘의 지문    Day {plan.day} · {plan.target_date.isoformat()}")
    lines.append(p["passage_ko"])
    lines.append("")
    lines.append(f"❓ {p['question']}")
    for i, c in enumerate(p["choices"]):
        lines.append(f"   {CIRCLED[i]} {c['ko']}  ({c['en']})")

    section("🌐 English Translation")
    lines.append(p["passage_en"])

    section(f"📕 지문 어휘 ({len(p['passage_vocab'])}개)")
    for v in p["passage_vocab"]:
        lines.append(f"{v['word']} ({v['pos']}) — {v['en']}")
        lines.append(f"   └ 지문: \"{v['context']}\"")

    section("📗 오늘의 기출 단어 10")
    for i, v in enumerate(p["daily_vocab"], 1):
        lines.append(f"{i}. {v['word']} ({v['pos']}) — {v['en']}")
        lines.append(f"   {v['example_ko']}")
        lines.append(f"   {v['example_en']}")

    section("✅ 정답 및 해설")
    lines.append(f"정답: {CIRCLED[p['answer'] - 1]}")
    lines.append(f"해설: {p['explanation_ko']}")
    lines.append(f"({p['explanation_en']})")

    section("📎 참고 기출")
    lines.append(plan.exam_label)
    lines.append(plan.exam_url)
    lines.append("")
    lines.append("※ 지문과 문제는 기출 유형·난이도를 따라 새로 창작한 것입니다.")

    return "\n".join(lines)


# 이메일 클라이언트 호환을 위해 전부 인라인 스타일, 단일 컬럼, 시스템 글꼴만 쓴다(NFR-5).
_BASE = "font-family:-apple-system,'Apple SD Gothic Neo','Malgun Gothic',sans-serif;"
_H2 = (
    "margin:28px 0 10px;padding-bottom:6px;border-bottom:2px solid #1a2b4a;"
    "font-size:16px;color:#1a2b4a;" + _BASE
)
_P = "margin:8px 0;font-size:15px;line-height:1.7;color:#222;" + _BASE
_SMALL = "margin:4px 0;font-size:13px;line-height:1.6;color:#555;" + _BASE


def render_html(plan: DailyPlan, p: dict) -> str:
    e = _html.escape
    out: list[str] = []
    out.append(
        f'<div style="max-width:600px;margin:0 auto;padding:20px;{_BASE}">'
    )
    out.append(
        f'<p style="{_SMALL}text-align:right;">Day {plan.day} · {plan.target_date.isoformat()}</p>'
    )

    out.append(f'<h2 style="{_H2}">📖 오늘의 지문</h2>')
    out.append(f'<p style="{_P}">{e(p["passage_ko"])}</p>')
    out.append(f'<p style="{_P}"><strong>❓ {e(p["question"])}</strong></p>')
    for i, c in enumerate(p["choices"]):
        out.append(
            f'<p style="{_P}margin-left:8px;">{CIRCLED[i]} {e(c["ko"])}<br>'
            f'<span style="color:#777;font-size:13px;">&nbsp;&nbsp;&nbsp;{e(c["en"])}</span></p>'
        )

    out.append(f'<h2 style="{_H2}">🌐 English Translation</h2>')
    out.append(f'<p style="{_P}">{e(p["passage_en"])}</p>')

    out.append(f'<h2 style="{_H2}">📕 지문 어휘 ({len(p["passage_vocab"])}개)</h2>')
    for v in p["passage_vocab"]:
        out.append(
            f'<p style="{_P}"><strong>{e(v["word"])}</strong> ({e(v["pos"])}) — {e(v["en"])}<br>'
            f'<span style="color:#777;font-size:13px;">└ 지문: “{e(v["context"])}”</span></p>'
        )

    out.append(f'<h2 style="{_H2}">📗 오늘의 기출 단어 10</h2>')
    for i, v in enumerate(p["daily_vocab"], 1):
        out.append(
            f'<p style="{_P}"><strong>{i}. {e(v["word"])}</strong> ({e(v["pos"])}) — {e(v["en"])}<br>'
            f'<span style="font-size:14px;">{e(v["example_ko"])}</span><br>'
            f'<span style="color:#777;font-size:13px;">{e(v["example_en"])}</span></p>'
        )

    # 정답·해설은 스크롤 하단(FR-2)
    out.append(f'<h2 style="{_H2}">✅ 정답 및 해설</h2>')
    out.append(f'<p style="{_P}"><strong>정답: {CIRCLED[p["answer"] - 1]}</strong></p>')
    out.append(f'<p style="{_P}">{e(p["explanation_ko"])}</p>')
    out.append(f'<p style="{_SMALL}">{e(p["explanation_en"])}</p>')

    out.append(f'<h2 style="{_H2}">📎 참고 기출</h2>')
    out.append(f'<p style="{_P}">{e(plan.exam_label)}</p>')
    out.append(
        f'<p style="{_P}"><a href="{e(plan.exam_url)}" style="color:#1a5bd7;">{e(plan.exam_url)}</a></p>'
    )
    out.append(
        f'<p style="{_SMALL}margin-top:24px;">※ 지문과 문제는 기출 유형·난이도를 따라 새로 창작한 것입니다.</p>'
    )
    out.append("</div>")
    return "\n".join(out)
