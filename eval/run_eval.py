"""
Eval harness: runs the agent on each test case and scores output quality.

Two scoring methods:
  1. Keyword coverage  — checks whether expected concepts appear in the bullets
  2. LLM-as-judge      — GPT-4o-mini rates factual accuracy and relevance (0-10)

Final score = 50% keyword + 20% bullet count + 30% LLM judge
"""
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / "backend" / ".env")

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from agent.bluesky import parse_bluesky_url, get_bluesky_post
from agent.explainer import explain_post, openai_client


# ── LLM-as-judge ──────────────────────────────────────────────────────────────

JUDGE_SYSTEM = """You are an evaluation judge for an AI agent that explains social media posts.
Given a post and the agent's explanation, rate the explanation on two criteria:
1. Factual accuracy — are the facts correct and grounded in reality?
2. Relevance — does the explanation actually address what the post is about?

Return ONLY valid JSON in this exact format:
{"score": <integer 0-10>, "reasoning": "<one sentence>"}

Score guide: 0-3 = wrong or off-topic, 4-6 = partially correct, 7-9 = good, 10 = excellent."""


def llm_judge(post_text: str, bullets: list[str], sources: list[str]) -> dict:
    bullets_block = "\n".join(f"- {b}" for b in bullets)
    sources_block = "\n".join(sources) if sources else "(none)"

    prompt = f"""Post:
"{post_text}"

Agent explanation:
{bullets_block}

Sources cited:
{sources_block}

Rate this explanation."""

    try:
        response = openai_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM},
                {"role": "user",   "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=150,
        )
        data = json.loads(response.choices[0].message.content or "{}")
        raw_score = int(data.get("score", 0))
        return {
            "judge_score": round(raw_score / 10, 2),
            "judge_reasoning": data.get("reasoning", ""),
        }
    except Exception as e:
        return {"judge_score": 0.0, "judge_reasoning": f"judge error: {e}"}


# ── Keyword + count scoring ────────────────────────────────────────────────────

def score_case(result: dict, case: dict, use_judge: bool = True) -> dict:
    bullets_text = " ".join(result["bullets"]).lower()

    keywords_found = [kw for kw in case["expected_keywords"] if kw.lower() in bullets_text]
    keyword_score = len(keywords_found) / len(case["expected_keywords"])

    bullet_count = len(result["bullets"])
    count_ok = case["expected_bullet_count_min"] <= bullet_count <= case["expected_bullet_count_max"]
    count_score = 1.0 if count_ok else 0.0

    judge = {"judge_score": None, "judge_reasoning": ""}
    if use_judge:
        judge = llm_judge(
            case["post_text"],
            result["bullets"],
            result.get("sources", []),
        )

    if judge["judge_score"] is not None:
        final_score = (keyword_score * 0.5) + (count_score * 0.2) + (judge["judge_score"] * 0.3)
    else:
        final_score = (keyword_score * 0.7) + (count_score * 0.3)

    return {
        "id": case["id"],
        "score": round(final_score, 2),
        "keyword_score": round(keyword_score, 2),
        "count_score": count_score,
        "judge_score": judge["judge_score"],
        "judge_reasoning": judge["judge_reasoning"],
        "keywords_found": keywords_found,
        "keywords_missing": [kw for kw in case["expected_keywords"] if kw not in keywords_found],
        "bullet_count": bullet_count,
        "count_ok": count_ok,
        "bullets": result["bullets"],
        "sources": result.get("sources", []),
    }


# ── Runner ─────────────────────────────────────────────────────────────────────

def run_eval(cases_path: str = "cases.json", output_path: str = "eval_results.json", limit: int = None, use_judge: bool = True) -> float:
    with open(cases_path) as f:
        cases = json.load(f)

    if limit:
        cases = cases[:limit]

    results = []
    passed = 0
    threshold = 0.6

    print(f"\n{'='*60}")
    print(f"Running eval on {len(cases)} cases  [judge={'on' if use_judge else 'off'}]")
    print(f"{'='*60}\n")

    for case in cases:
        print(f"[{case['id']}] processing...")
        try:
            parsed = parse_bluesky_url(case["url"])
            post = get_bluesky_post(parsed["handle"], parsed["rkey"])
            explanation = explain_post(post)
            scored = score_case(explanation, case, use_judge=use_judge)
        except Exception as e:
            scored = {
                "id": case["id"],
                "score": 0.0,
                "keyword_score": 0.0,
                "count_score": 0.0,
                "judge_score": None,
                "judge_reasoning": "",
                "error": str(e),
                "bullets": [],
                "sources": [],
            }

        results.append(scored)
        status = "PASS" if scored["score"] >= threshold else "FAIL"
        if scored["score"] >= threshold:
            passed += 1

        judge_str = f"  judge={scored['judge_score']:.1f}" if scored.get("judge_score") is not None else ""
        print(f"  [{status}] score={scored['score']:.2f}  kw={scored.get('keyword_score', 0):.2f}{judge_str}")
        if scored.get("judge_reasoning"):
            print(f"  judge says: {scored['judge_reasoning']}")
        if scored.get("keywords_missing"):
            print(f"  missing keywords: {scored['keywords_missing']}")
        if "error" in scored:
            print(f"  error: {scored['error']}")
        print()

    overall = sum(r["score"] for r in results) / len(results)
    print(f"{'='*60}")
    print(f"Overall score: {overall:.2f} | Passed: {passed}/{len(cases)}")
    print(f"{'='*60}\n")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"overall_score": overall, "passed": passed, "total": len(cases), "cases": results}, f, indent=2, ensure_ascii=False)

    return overall


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases",    type=str,  default="cases.json",        help="Path to cases JSON file")
    parser.add_argument("--output",   type=str,  default="eval_results.json", help="Path to output JSON file")
    parser.add_argument("--limit",    type=int,  default=None,                help="Limit number of cases")
    parser.add_argument("--no-judge", action="store_true",                    help="Skip LLM judge (faster)")
    args = parser.parse_args()
    run_eval(cases_path=args.cases, output_path=args.output, limit=args.limit, use_judge=not args.no_judge)
