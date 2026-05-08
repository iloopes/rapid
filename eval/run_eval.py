"""
Eval harness: runs the agent on each test case and scores output quality.

Two scoring methods:
  1. Keyword coverage  — checks whether expected concepts appear in the bullets
  2. LLM-as-judge      — GPT-4o-mini rates factual accuracy and relevance (0-10)

Final score = 50% keyword + 20% bullet count + 30% LLM judge

Multi-model comparison:
  python run_eval.py --model gpt-4o,gpt-4o-mini
  → runs eval for each model, saves per-model JSON, generates comparison HTML
"""
import json
import os
import sys
from datetime import date
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

def run_eval(
    cases_path: str = "cases.json",
    output_path: str = "eval_results.json",
    limit: int = None,
    use_judge: bool = True,
    model: str = "gpt-4o",
) -> dict:
    with open(cases_path) as f:
        cases = json.load(f)

    if limit:
        cases = cases[:limit]

    results = []
    passed = 0
    threshold = 0.6

    print(f"\n{'='*60}")
    print(f"Running eval on {len(cases)} cases  [model={model}  judge={'on' if use_judge else 'off'}]")
    print(f"{'='*60}\n")

    for case in cases:
        print(f"[{case['id']}] processing...")
        try:
            parsed = parse_bluesky_url(case["url"])
            post = get_bluesky_post(parsed["handle"], parsed["rkey"])
            explanation = explain_post(post, model=model)
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

    payload = {
        "model": model,
        "overall_score": overall,
        "passed": passed,
        "total": len(cases),
        "cases": results,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return payload


# ── Comparison HTML ────────────────────────────────────────────────────────────

def generate_comparison_html(results_by_model: dict, output_path: str = "eval_comparison.html") -> None:
    models = list(results_by_model.keys())
    all_ids = [c["id"] for c in next(iter(results_by_model.values()))["cases"]]
    today = date.today().isoformat()

    def score_color(s):
        if s >= 0.85: return "#4ade80"
        if s >= 0.65: return "#fbbf24"
        return "#f87171"

    def delta_color(d):
        if d >= 0.05: return "#4ade80"
        if d <= -0.05: return "#f87171"
        return "#94a3b8"

    # summary rows
    summary_rows = ""
    bar_blocks = ""
    for m, res in results_by_model.items():
        judge_scores = [c["judge_score"] for c in res["cases"] if c.get("judge_score") is not None]
        avg_judge = sum(judge_scores) / max(1, len(judge_scores))
        sc = res["overall_score"]
        color = score_color(sc)
        summary_rows += f"""
        <tr>
          <td class="model-name">{m}</td>
          <td style="color:{color};font-weight:700">{sc:.2f}</td>
          <td>{res['passed']}/{res['total']}</td>
          <td>{avg_judge * 10:.1f}/10</td>
        </tr>"""
        pct = int(sc * 100)
        bar_blocks += f"""
        <div class="bar-row">
          <span class="bar-label">{m}</span>
          <div class="bar-bg">
            <div class="bar-fill" style="width:{pct}%;background:{color}"></div>
          </div>
          <span class="bar-val" style="color:{color}">{sc:.2f}</span>
        </div>"""

    # per-case rows
    case_rows = ""
    scores_by_id = {
        m: {c["id"]: c["score"] for c in res["cases"]}
        for m, res in results_by_model.items()
    }
    for cid in all_ids:
        scores = [scores_by_id[m].get(cid, 0) for m in models]
        best = max(scores)
        worst = min(scores)
        delta = best - worst
        cells = ""
        for s in scores:
            cells += f'<td style="color:{score_color(s)};font-weight:600">{s:.2f}</td>'
        delta_c = delta_color(delta if scores[0] >= scores[-1] else -delta)
        winner = models[scores.index(best)]
        case_rows += f"""
        <tr>
          <td class="case-id">{cid}</td>
          {cells}
          <td style="color:{delta_color(delta)};font-weight:600">±{delta:.2f}</td>
          <td style="color:#94a3b8;font-size:.78rem">{winner if delta > 0.01 else "tie"}</td>
        </tr>"""

    model_headers = "".join(f"<th>{m}</th>" for m in models)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Bluesky Explainer — Model Comparison</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #0f1117; color: #e2e8f0; min-height: 100vh; padding: 2rem 1rem;
    }}
    .container {{ max-width: 860px; margin: 0 auto; }}
    header {{ text-align: center; margin-bottom: 2.5rem; }}
    header h1 {{ font-size: 1.9rem; font-weight: 700; color: #fff; }}
    header p {{ color: #94a3b8; margin-top: .4rem; font-size: .95rem; }}

    h2 {{ font-size: .82rem; text-transform: uppercase; letter-spacing: .07em;
          color: #64748b; margin-bottom: .9rem; }}

    section {{ margin-bottom: 2.5rem; }}

    /* summary table */
    table {{ width: 100%; border-collapse: collapse; }}
    th {{ font-size: .72rem; text-transform: uppercase; letter-spacing: .06em;
          color: #64748b; padding: .5rem .8rem; text-align: left;
          border-bottom: 1px solid #2d3748; }}
    td {{ padding: .65rem .8rem; border-bottom: 1px solid #1e2330; font-size: .9rem; }}
    tr:hover td {{ background: #1a2035; }}
    .model-name {{ font-weight: 700; color: #e2e8f0; }}
    .case-id {{ font-size: .8rem; color: #94a3b8; font-family: monospace; }}

    /* score bars */
    .bar-row {{ display: flex; align-items: center; gap: .8rem; margin-bottom: .6rem; }}
    .bar-label {{ width: 140px; font-size: .85rem; color: #e2e8f0; flex-shrink: 0;
                  font-weight: 600; }}
    .bar-bg {{ flex: 1; background: #1e2330; border-radius: 999px; height: 10px;
               overflow: hidden; border: 1px solid #2d3748; }}
    .bar-fill {{ height: 100%; border-radius: 999px; transition: width .6s ease; }}
    .bar-val {{ width: 40px; font-size: .85rem; font-weight: 700; text-align: right;
                flex-shrink: 0; }}

    footer {{ text-align: center; margin-top: 3rem; color: #334155; font-size: .8rem; }}
  </style>
</head>
<body>
<div class="container">

  <header>
    <h1>Bluesky Post Explainer — Model Comparison</h1>
    <p>GPT-4o · DuckDuckGo search · {len(all_ids)} posts · scored {today}</p>
  </header>

  <section>
    <h2>Summary</h2>
    <table>
      <thead><tr><th>Model</th><th>Overall score</th><th>Passed</th><th>Avg judge</th></tr></thead>
      <tbody>{summary_rows}</tbody>
    </table>
  </section>

  <section>
    <h2>Score bars</h2>
    {bar_blocks}
  </section>

  <section>
    <h2>Per-case breakdown</h2>
    <table>
      <thead>
        <tr>
          <th>Case</th>
          {model_headers}
          <th>Delta</th>
          <th>Winner</th>
        </tr>
      </thead>
      <tbody>{case_rows}</tbody>
    </table>
  </section>

  <footer>Generated by the eval harness · Bluesky Post Explainer</footer>
</div>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Comparison report → {output_path}")


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases",    type=str,  default="cases.json",        help="Path to cases JSON file")
    parser.add_argument("--output",   type=str,  default="eval_results.json", help="Output JSON (single model)")
    parser.add_argument("--model",    type=str,  default="gpt-4o",            help="Model(s) — comma-separated for comparison")
    parser.add_argument("--limit",    type=int,  default=None,                help="Limit number of cases")
    parser.add_argument("--no-judge", action="store_true",                    help="Skip LLM judge (faster)")
    args = parser.parse_args()

    models = [m.strip() for m in args.model.split(",")]

    if len(models) == 1:
        run_eval(
            cases_path=args.cases,
            output_path=args.output,
            limit=args.limit,
            use_judge=not args.no_judge,
            model=models[0],
        )
    else:
        results_by_model = {}
        for m in models:
            safe = m.replace("/", "-").replace(":", "-")
            out = f"eval_results_{safe}.json"
            print(f"\n{'#'*60}")
            print(f"# MODEL: {m}")
            print(f"{'#'*60}")
            results_by_model[m] = run_eval(
                cases_path=args.cases,
                output_path=out,
                limit=args.limit,
                use_judge=not args.no_judge,
                model=m,
            )

        generate_comparison_html(results_by_model, output_path="eval_comparison.html")
