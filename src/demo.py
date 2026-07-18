from DataGen2 import DataGenCCS
from regex_preprocessing import sanitize
from classifier_main import CCSClassifier
from prompt_wrapper import build_wrapped_prompt
from llm_call import call_llm
from summarize import summarize_results
import os
import csv

import time

start = time.time()

# ── VERDICT PARSER ────────────────────────────────────────────────────────────
import re

VALID_VERDICTS = {"PASS", "WARN", "FAIL"}

def parse_verdict(verify_response: str) -> dict:
    """
    Extracts the PASS/WARN/FAIL verdict from the verifier's response.

    Returns:
        {
            "verdict"   : "PASS" | "WARN" | "FAIL" | "UNKNOWN",
            "reasoning" : str
        }
    """
    match = re.search(r"\b(PASS|WARN|FAIL)\b", verify_response.upper())

    if match:
        verdict   = match.group(1)
        reasoning = verify_response[match.end():].strip(" :\n-")
    else:
        verdict   = "UNKNOWN"
        reasoning = verify_response.strip()

    return {
        "verdict"   : verdict,
        "reasoning" : reasoning
    }

def extract_rows(filepath, row_numbers: list[int]) -> list[dict]:
    row_numbers = set(row_numbers)  # O(1) lookup
    results = []

    with open(filepath, "r", newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i in row_numbers:
                results.append(dict(row))

    return results

def process_prompt(prompt, id = -1, filename = "output.csv", without_pipeline = False):
    sanitized_prompt = sanitize(prompt)

    print("Prompt sanitized")

    # Step 2 output
    classifier = CCSClassifier()
    result = classifier.classify(prompt)

    print("Prompt classified")

    # Step 3 output
    wrapped = build_wrapped_prompt(sanitized_prompt, result)

    print("Wrapper generated")

    print("----------------------------------------------------------------------------------------------------------------------------------")
    print("Sending prompt to LLM")
    print("----------------------------------------------------------------------------------------------------------------------------------")

    if not without_pipeline:
        # ── Main call ─────────────────────────────────────────────────────────────
        main_response = call_llm(
            system_prompt = wrapped.main_system,
            user_message  = wrapped.main_system + wrapped.original_prompt,
            model         = wrapped.verifier_model
        )
    else:
        main_response = call_llm(
            system_prompt = "",
            user_message  = wrapped.original_prompt,
            model         = wrapped.verifier_model
        )

    print("Main LLM Call complete")

    # ── Verifier call ─────────────────────────────────────────────────────────
    # Pass the original prompt + main response as context for the verifier
    verify_response = call_llm(
        system_prompt = wrapped.verify_system,
        user_message  = "Original Prompt: \n" + wrapped.original_prompt + "Response: \n" + main_response + "\n" + wrapped.verify_system,   # only the response to audit
        model         = wrapped.main_model,
        history       = None             # no history needed
    )

    verdict = parse_verdict(verify_response)

    data = {
            "id"              : id,
            "prompt"          : wrapped.original_prompt,
            "label"           : wrapped.label,
            "vulnerability"   : wrapped.vulnerability,
            "main_response"   : main_response,
            "verdict"         : verdict["verdict"],    # "PASS", "WARN", "FAIL", "UNKNOWN"
            "reasoning"       : verdict["reasoning"]
    }

    file_exists = os.path.exists(filename)
    
    with open(filename, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data.keys())
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(data)

    print("Data written to csv file")
    print(str(id) + " complete")
    print()


def process_rows(filepath, row_numbers, pipeline = True, output_file = "output.csv"):
    row_numbers = set(row_numbers)  # O(1) lookup
    results = []

    with open(filepath, "r", newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i in row_numbers:
                results.append(dict(row))

    for result in results:
        process_prompt(result["prompt"], result["id"], without_pipeline=not pipeline, filename=output_file)

process_rows("dataset_demo.csv", [i for i in range(8)], pipeline=True, output_file="output_demo.csv")
process_rows("dataset_demo.csv", [i for i in range(8)], pipeline=False, output_file="output_demo_normal.csv")

summarize_results(results_csv = "output_demo.csv",summary_csv = "summary_demo.csv", text="With Pipeline")
summarize_results(results_csv = "output_demo_normal.csv",summary_csv = "summary_demo_raw.csv", text="Without Pipeline")

elapsed = time.time() - start

with open("log.txt", "a") as f:
    f.write(f"Took {elapsed:.2f} seconds\n")