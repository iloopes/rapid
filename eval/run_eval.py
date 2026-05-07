"""
Eval harness: roda o agente em cada caso de teste e calcula score de qualidade.
Usa LLM-as-judge para comparar output gerado com keywords esperadas.
"""
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / "backend" / ".env")

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from agent.bluesky import parse_bluesky_url, get_bluesky_post
from agent.explainer import explain_post


def score_case(result: dict, case: dict) -> dict:
    bullets_text = " ".join(result["bullets"]).lower()
    keywords_found = [kw for kw in case["expected_keywords"] if kw.lower() in bullets_text]
    keyword_score = len(keywords_found) / len(case["expected_keywords"])

    bullet_count = len(result["bullets"])
    count_ok = case["expected_bullet_count_min"] <= bullet_count <= case["expected_bullet_count_max"]
    count_score = 1.0 if count_ok else 0.0

    final_score = (keyword_score * 0.7) + (count_score * 0.3)

    return {
        "id": case["id"],
        "score": round(final_score, 2),
        "keywords_found": keywords_found,
        "keywords_missing": [kw for kw in case["expected_keywords"] if kw not in keywords_found],
        "bullet_count": bullet_count,
        "count_ok": count_ok,
        "bullets": result["bullets"],
    }


def run_eval(cases_path: str = "cases.json", limit: int = None) -> None:
    with open(cases_path) as f:
        cases = json.load(f)

    if limit:
        cases = cases[:limit]

    results = []
    passed = 0
    threshold = 0.6

    print(f"\n{'='*60}")
    print(f"Rodando eval em {len(cases)} casos...")
    print(f"{'='*60}\n")

    for case in cases:
        print(f"[{case['id']}] processando...")
        try:
            parsed = parse_bluesky_url(case["url"])
            post = get_bluesky_post(parsed["handle"], parsed["rkey"])
            explanation = explain_post(post)
            scored = score_case(explanation, case)
        except Exception as e:
            scored = {
                "id": case["id"],
                "score": 0.0,
                "error": str(e),
                "bullets": [],
            }

        results.append(scored)
        status = "PASS" if scored["score"] >= threshold else "FAIL"
        if scored["score"] >= threshold:
            passed += 1

        print(f"  [{status}] score={scored['score']:.2f}")
        if "keywords_missing" in scored and scored["keywords_missing"]:
            print(f"  keywords faltando: {scored['keywords_missing']}")
        if "error" in scored:
            print(f"  erro: {scored['error']}")
        print()

    overall = sum(r["score"] for r in results) / len(results)
    print(f"{'='*60}")
    print(f"Score geral: {overall:.2f} | Passaram: {passed}/{len(cases)}")
    print(f"{'='*60}\n")

    with open("eval_results.json", "w") as f:
        json.dump({"overall_score": overall, "cases": results}, f, indent=2)

    return overall


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Limitar número de casos")
    args = parser.parse_args()
    run_eval(limit=args.limit)
