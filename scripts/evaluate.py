import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.policy import evaluate_policy
from app.provider import DeterministicFakeProvider

def main():
    cases=json.loads((Path(__file__).resolve().parents[1]/"evals"/"cases.json").read_text())
    provider=DeterministicFakeProvider(); passed=0
    for case in cases:
        response=provider.analyze(case["document"]); review,reasons,tool=evaluate_policy(response.extraction)
        ok=review==case["expected_review"] and (tool.tool_name if tool else None)==case["expected_tool"]
        if case.get("expected_reason"): ok=ok and case["expected_reason"] in reasons
        passed+=int(ok); print(f"{case['name']}: {'PASS' if ok else 'FAIL'} review={review} reasons={reasons}")
    score=passed/len(cases); print(f"evaluation_score={score:.4f}")
    if score < 1.0: raise SystemExit(1)
if __name__=="__main__": main()
