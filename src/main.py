from DataGen2 import DataGenCCS
from regex_preprocessing import sanitize
from classifier_main import CCSClassifier
from prompt_wrapper import build_wrapped_prompt
from llm_call import call_llm

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

DataGen = DataGenCCS()
prompts = DataGen.generate_balanced_dataset(1)
prompt = prompts['prompt'][0]

print("Prompt generated")

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

# ── Main call ─────────────────────────────────────────────────────────────
main_response = call_llm(
    system_prompt = wrapped.main_system,
    user_message  = wrapped.original_prompt,
    model         = wrapped.main_model
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
        "prompt"          : wrapped.original_prompt,
        "label"           : wrapped.label,
        "vulnerability"   : wrapped.vulnerability,
        "main_response"   : main_response,
        "verify_response" : verify_response,
        "verdict"         : verdict["verdict"],    # "PASS", "WARN", "FAIL", "UNKNOWN"
        "reasoning"       : verdict["reasoning"]
}
print("----------------------------------------------------------------------------------------------------------------------------------")
print("Final Output")
print("----------------------------------------------------------------------------------------------------------------------------------")
print(data)