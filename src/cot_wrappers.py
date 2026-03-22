"""
cot_wrappers.py
---------------
Three ways to use this file:

1. Import the verifier in your application:
       from cot_wrappers import verify

2. Test a single prompt from the terminal:
       python cot_wrappers.py single --wrapper 2 --task "What is 12 * 8?"

3. Benchmark the verifier against a labelled CSV dataset:
       python cot_wrappers.py dataset --path verifier_dataset.csv

Dataset format — CSV, no header, two columns:
    <llm_response>, <ground_truth_label>
    ground_truth_label: YES/consistent  or  NO/inconsistent  (case-insensitive)
"""

from openai import OpenAI
from string import Template
from datetime import datetime
import argparse
import csv
import re

# ── constants ─────────────────────────────────────────────────────────────────

DIVIDER          = "=" * 50 + "\n"
SUBDIV           = "-" * 40 + "\n"
TEST_LOG         = "tests.log"
VERIFIER_EVAL_LOG = "verifier_eval.log"

WRAPPERS = [
    Template("""Solve the following task step by step.

Return exactly:

COT:
1.
2.
3.

FINAL: <answer>

Task:
$task
"""),
    Template("""Think step by step and output JSON.

{
 "cot": ["step1", "step2", "step3"],
 "answer": "final_answer"
}

Task:
$task
"""),
    Template("""Solve the task.

Return strictly in this format:

T1:
T2:
T3:
ANS:

Task:
$task
"""),
    Template("""Work through the reasoning.

Output exactly:

[THOUGHT]
step

[THOUGHT]
step

[THOUGHT]
step

[FINAL]
answer

Task:
$task
"""),
]

_VERIFIER_SYSTEM = """\
You are a reasoning verifier.

Your job is to evaluate a chain-of-thought (COT) and determine whether
the reasoning correctly leads to the final answer.

Rules:
- Do not generate a new solution unless necessary.
- Check each step for logical consistency.
- Identify incorrect or unsupported steps.
- Decide whether the final answer is valid.

Output strictly in this format:
{
VERDICT: <Either YES or NO>
}
"""

client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="lmstudio"
)

# ── shared internals ──────────────────────────────────────────────────────────

def _call_llm(model: str, system: str, user: str) -> str:
    return str(client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        temperature=0.7,
        max_tokens=500,
    ).choices[0].message.content)


def _parse_verdict(raw: str) -> bool:
    match = re.search(r'VERDICT[\s":]+\b(YES|NO)\b', raw, re.IGNORECASE)
    if match:
        return match.group(1).upper() == "YES"
    if re.search(r'\bYES\b', raw, re.IGNORECASE):
        return True
    if re.search(r'\bNO\b', raw, re.IGNORECASE):
        return False
    print(f"[WARNING] Could not parse verdict:\n{raw}")
    return False


def _normalise_label(raw: str) -> bool | None:
    cleaned = raw.strip().lower()
    if cleaned in ("yes", "consistent"):
        return True
    if cleaned in ("no", "inconsistent"):
        return False
    return None

# ── public API (importable) ───────────────────────────────────────────────────

def verify(cot_response: str) -> bool:
    """
    Verify a COT response string using the verifier model.

    Import and use this in your application:
        from cot_wrappers import verify
        is_valid = verify(some_cot_string)

    Args:
        cot_response (str): Full chain-of-thought text from any LLM,
                            including reasoning steps and final answer.
    Returns:
        bool: True if the verifier judges the reasoning valid, False otherwise.
    """
    raw = _call_llm("phi-3-mini-4k-instruct", _VERIFIER_SYSTEM, cot_response)
    return _parse_verdict(raw)


def test_single(wrapper_idx: int, task: str) -> bool:
    """
    Send a task through a COT wrapper, verify the response, log to tests.log.

    Args:
        wrapper_idx (int): Index into WRAPPERS (0–3) selecting the prompt format.
        task        (str): The question or problem to solve.
    Returns:
        bool: True if the verifier passes the COT, False otherwise.
    """
    prompt       = WRAPPERS[wrapper_idx].substitute(task=task)
    cot_response = _call_llm("meta-llama-3-8b-instruct", "You are a helpful assistant.", prompt)
    passed       = verify(cot_response)

    result_str = "PASS ✓" if passed else "FAIL ✗"
    entry = (
        f"{DIVIDER}"
        f"[{datetime.now():%Y-%m-%d %H:%M:%S}]  wrapper={wrapper_idx}  result={result_str}\n"
        f"TASK: {task}\n"
        f"{SUBDIV}"
        f"PROMPT:\n{prompt}\n"
        f"{SUBDIV}"
        f"COT RESPONSE:\n{cot_response}\n"
        f"{SUBDIV}"
        f"VERDICT: {result_str}\n"
    )
    with open(TEST_LOG, "a", encoding="utf-8") as f:
        f.write(entry)

    print(f"Wrapper {wrapper_idx} | {result_str}  →  log: {TEST_LOG}")
    return passed


def evaluate_verifier(dataset_path: str) -> dict:
    """
    Benchmark the verifier against a labelled CSV dataset and return metrics.

    Args:
        dataset_path (str): Path to CSV with rows: <llm_response>, <label>
                            Label: YES/consistent or NO/inconsistent (case-insensitive).
                            Rows with unrecognised labels are skipped.
    Returns:
        dict: accuracy, precision, recall, f1, confusion matrix, and counts.
              Full results are also appended to verifier_eval.log.
    """
    TP = TN = FP = FN = skipped = 0
    row_details = []

    with open(dataset_path, newline="", encoding="utf-8") as fh:
        for row_num, row in enumerate(csv.reader(fh), start=1):
            if len(row) < 2:
                print(f"[WARNING] Row {row_num}: fewer than 2 columns — skipping.")
                skipped += 1
                continue

            ground_truth = _normalise_label(row[1])
            if ground_truth is None:
                print(f"[WARNING] Row {row_num}: unrecognised label '{row[1].strip()}' — skipping.")
                skipped += 1
                continue

            predicted = verify(row[0].strip())

            if   predicted and ground_truth:         TP += 1
            elif not predicted and not ground_truth: TN += 1
            elif predicted and not ground_truth:     FP += 1
            else:                                    FN += 1

            match = predicted == ground_truth
            row_details.append({
                "row": row_num,
                "gt":  "YES" if ground_truth else "NO",
                "pred":"YES" if predicted    else "NO",
                "match": match,
            })
            print(f"  Row {row_num:>3}: gt={row_details[-1]['gt']}  "
                  f"pred={row_details[-1]['pred']}  {'✓' if match else '✗'}")

    total     = len(row_details)
    passed    = TP + TN
    failed    = FP + FN
    accuracy  = passed / total                        if total             else 0.0
    precision = TP / (TP + FP)                        if (TP + FP)         else 0.0
    recall    = TP / (TP + FN)                        if (TP + FN)         else 0.0
    f1        = 2*precision*recall/(precision+recall) if (precision+recall) else 0.0

    metrics = {
        "total": total, "passed": passed, "failed": failed, "skipped": skipped,
        "accuracy": round(accuracy, 4), "precision": round(precision, 4),
        "recall": round(recall, 4), "f1": round(f1, 4),
        "confusion": {"TP": TP, "TN": TN, "FP": FP, "FN": FN},
    }

    lines = [
        DIVIDER,
        f"[{datetime.now():%Y-%m-%d %H:%M:%S}]  VERIFIER EVALUATION\n",
        f"Dataset : {dataset_path}\n", SUBDIV,
        f"{'Metric':<12}{'Value':>10}\n", f"{'-'*22}\n",
        f"{'Total':<12}{total:>10}\n",     f"{'Passed':<12}{passed:>10}\n",
        f"{'Failed':<12}{failed:>10}\n",   f"{'Skipped':<12}{skipped:>10}\n",
        f"{'Accuracy':<12}{accuracy:>10.2%}\n",
        f"{'Precision':<12}{precision:>10.4f}\n",
        f"{'Recall':<12}{recall:>10.4f}\n",
        f"{'F1':<12}{f1:>10.4f}\n", SUBDIV,
        f"Confusion Matrix\n  TP={TP}  FP={FP}\n  FN={FN}  TN={TN}\n", SUBDIV,
        "Per-row results:\n",
        *[f"  [{'✓' if d['match'] else '✗'}] row={d['row']:>3}  gt={d['gt']}  pred={d['pred']}\n"
          for d in row_details],
        DIVIDER,
    ]
    with open(VERIFIER_EVAL_LOG, "a", encoding="utf-8") as fh:
        fh.writelines(lines)

    print(f"\n{'='*40}\n  Accuracy : {accuracy:.2%}\n  Precision: {precision:.4f}"
          f"\n  Recall   : {recall:.4f}\n  F1       : {f1:.4f}"
          f"\n  Confusion: TP={TP} TN={TN} FP={FP} FN={FN}"
          f"\n  Full log → {VERIFIER_EVAL_LOG}\n{'='*40}")
    return metrics

# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="COT testing toolkit")
    sub = parser.add_subparsers(dest="command", required=True)

    p_single = sub.add_parser("single", help="Test a single prompt")
    p_single.add_argument("--wrapper", type=int, default=2, help="Wrapper index (0-3)")
    p_single.add_argument("--task",    type=str, required=True, help="Task string")

    p_dataset = sub.add_parser("dataset", help="Evaluate verifier on a CSV dataset")
    p_dataset.add_argument("--path", type=str, required=True, help="Path to CSV file")

    args = parser.parse_args()
    if args.command == "single":
        test_single(args.wrapper, args.task)
    elif args.command == "dataset":
        evaluate_verifier(args.path)
