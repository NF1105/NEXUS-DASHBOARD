import requests


MODEL_NAME = "gpt-4o-mini"
CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"


def generate_study_response(api_key, prompt, context="", history=None):
    if not api_key:
        raise ValueError("Add an OpenAI API key to enable generated answers.")

    system_message = (
        "You are NEXUS-DASHBOARD, a careful college-level study assistant. Explain concepts clearly, "
        "help students understand rather than just copy answers, and distinguish evidence "
        "from uncertainty. When context is provided, use it as the primary source and say "
        "when it does not contain enough information. Do not invent citations or facts."
    )
    if context:
        system_message += f"\n\nReference context:\n{context[:24000]}"

    messages = [{"role": "system", "content": system_message}]
    for message in (history or [])[-8:]:
        if message.get("role") in {"user", "assistant"} and message.get("content"):
            messages.append(
                {"role": message["role"], "content": message["content"][:6000]}
            )
    messages.append({"role": "user", "content": prompt[:6000]})

    try:
        response = requests.post(
            CHAT_COMPLETIONS_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": MODEL_NAME, "messages": messages, "temperature": 0.3},
            timeout=(10, 90),
        )
    except requests.Timeout as error:
        raise RuntimeError("The AI service took too long to respond. Try again.") from error
    except requests.RequestException as error:
        raise RuntimeError("Could not connect to the AI service. Check your connection.") from error

    if response.status_code == 401:
        raise RuntimeError("The API key was not accepted. Check it and try again.")
    if response.status_code == 429:
        raise RuntimeError("The AI service rate limit or account quota was reached.")
    if response.status_code >= 400:
        raise RuntimeError(f"The AI service returned an error ({response.status_code}).")

    try:
        answer = response.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise RuntimeError("The AI service returned an unexpected response.") from error

    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError("The AI service returned an empty answer.")
    return answer.strip()
