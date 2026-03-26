# ── LLM API CALL ──────────────────────────────────────────────────────────────
# Single reusable function for both main and verifier calls.
# Assumes OpenAI-compatible local endpoint (LM Studio / Ollama).

from openai import OpenAI

client = OpenAI(
    base_url = "http://localhost:1234/v1",  # adjust port if needed
    api_key  = "local"                      # required by client but unused locally
)

def call_llm(
    system_prompt : str,
    user_message  : str,
    model         : str,
    history       : list[dict] | None = None,
    temperature   : float = 0.2,
    max_tokens    : int   = 2048
) -> str:
    """
    Reusable LLM call function for both main and verifier models.

    Args:
        system_prompt : System prompt (main_system or verify_system)
        user_message  : The user turn content
        model         : Model name string
        history       : Optional list of prior messages for multi-turn context
        temperature   : Sampling temperature
        max_tokens    : Max output tokens

    Returns:
        Response text as string
    """
    messages = [{"role": "system", "content": system_prompt}]

    if history:
        messages.extend(history)

    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model       = model,
        messages    = messages,
        temperature = temperature,
        max_tokens  = max_tokens
    )

    return response.choices[0].message.content