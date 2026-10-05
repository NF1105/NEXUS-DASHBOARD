import json
import re

from ai_service import generate_study_response


def parse_flashcard_response(response_text, card_count):
    text = response_text.strip()
    fenced_response = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if fenced_response:
        text = fenced_response.group(1)

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError("The generated flashcards were not valid JSON. Please try again.") from error

    cards = payload.get("cards") if isinstance(payload, dict) else None
    if not isinstance(cards, list) or len(cards) < card_count:
        raise ValueError(
            f"The response did not contain all {card_count} requested flashcards. Please try again."
        )

    validated_cards = []
    for index, card in enumerate(cards[:card_count], start=1):
        if not isinstance(card, dict):
            raise ValueError(f"Flashcard {index} was not in the expected format.")

        front = card.get("front")
        back = card.get("back")
        if (
            not isinstance(front, str)
            or not front.strip()
            or not isinstance(back, str)
            or not back.strip()
        ):
            raise ValueError(f"Flashcard {index} had missing or invalid front/back text.")

        validated_cards.append({"front": front.strip(), "back": back.strip()})
    return validated_cards


def generate_flashcards(api_key, subject_name, context, card_count):
    prompt = (
        f"Create exactly {card_count} concise study flashcards for {subject_name} "
        "using only the provided source material. Test a mix of key concepts, "
        "definitions, relationships, and useful applications. Make each front a "
        "clear question or prompt and each back a focused answer. Avoid duplicates, "
        "trivia, and facts not supported by the source. Return only valid JSON in "
        'this format: {"cards":[{"front":"Question or prompt","back":"Answer"}]}.'
    )
    response = generate_study_response(api_key, prompt, context)
    return parse_flashcard_response(response, card_count)
