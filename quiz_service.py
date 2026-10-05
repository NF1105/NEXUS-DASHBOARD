import json
import re

from ai_service import generate_study_response
from quick_reference_content import QUICK_REFERENCE_SUBJECTS


REFERENCE_SUBJECTS = {
    "Biology": ("biology", "ap biology"),
    "Chemistry": ("chemistry",),
    "Computer Science": ("computer science", "cs101", "programming", "computing"),
    "Economics": ("economics",),
    "English": ("english", "writing", "language arts", "literature"),
    "History": ("history",),
    "Mathematics": ("mathematics", "math", "calculus", "algebra", "trigonometry", "geometry"),
    "Physics": ("physics", "physical science"),
    "Statistics": ("statistics",),
    "Study Skills": ("study skills",),
    "Social Studies": ("social studies",),
}


def match_reference_subject(subject_name):
    normalized_name = subject_name.casefold()
    for reference_subject, aliases in REFERENCE_SUBJECTS.items():
        if any(alias in normalized_name for alias in aliases):
            return reference_subject
    return None


def get_reference_topics(reference_subject):
    if reference_subject == "Social Studies":
        return [
            (f"{subject}: {title}", description)
            for subject in ("History", "Economics")
            for title, description in QUICK_REFERENCE_SUBJECTS[subject]
        ]
    return QUICK_REFERENCE_SUBJECTS.get(reference_subject, [])


def format_reference_context(reference_subject, focus_topic=None):
    topics = get_reference_topics(reference_subject)
    if not topics:
        return ""

    formatted_topics = "\n".join(
        f"- {title}: {description}" for title, description in topics
    )
    focus = focus_topic or "Mixed review across the subject"
    return (
        f"Subject reference: {reference_subject}\n"
        f"Quiz focus: {focus}\n"
        "Key topics and equations:\n"
        f"{formatted_topics}"
    )


def parse_quiz_response(response_text, question_count):
    text = response_text.strip()
    fenced_response = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if fenced_response:
        text = fenced_response.group(1)

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError("The generated quiz was not valid JSON. Please try again.") from error

    questions = payload.get("questions") if isinstance(payload, dict) else None
    if not isinstance(questions, list) or len(questions) < question_count:
        raise ValueError(
            f"The generated quiz did not contain all {question_count} requested questions. Please try again."
        )

    validated_questions = []
    for index, item in enumerate(questions[:question_count], start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Question {index} was not in the expected format.")

        question = item.get("q")
        options = item.get("options")
        answer = item.get("ans")
        explanation = item.get("explanation", "")
        if (
            not isinstance(question, str)
            or not question.strip()
            or not isinstance(options, list)
            or len(options) != 4
            or any(not isinstance(option, str) or not option.strip() for option in options)
            or not isinstance(answer, str)
            or answer not in options
            or not isinstance(explanation, str)
        ):
            raise ValueError(f"Question {index} had missing or invalid question data.")

        validated_questions.append(
            {
                "q": question.strip(),
                "options": [option.strip() for option in options],
                "ans": answer.strip(),
                "explanation": explanation.strip(),
            }
        )
    return validated_questions


def generate_quiz(api_key, subject_name, context, question_count, focus_topic):
    prompt = (
        f"Create exactly {question_count} multiple-choice practice questions for "
        f"{subject_name}. Focus: {focus_topic}. Use the provided reference context "
        "as the source of truth. Assess important concepts and, where relevant, "
        "important equations, formulas, and how to apply or interpret them. If the "
        "context includes formulas, include questions that test their meaning, "
        "conditions, or application rather than only asking students to memorize "
        "the formula. Make every question specific to the source material; avoid "
        "generic filler, unsupported facts, and duplicate questions. Each question "
        "must have exactly four plausible answer options, one unambiguous correct "
        "answer, and a brief explanation. Return only valid JSON in this format: "
        '{"questions":[{"q":"Question text","options":["Option 1","Option 2",'
        '"Option 3","Option 4"],"ans":"Option 1","explanation":"Why it is correct"}]}. '
        "The ans value must exactly match one of the four options."
    )
    response = generate_study_response(api_key, prompt, context)
    return parse_quiz_response(response, question_count)
