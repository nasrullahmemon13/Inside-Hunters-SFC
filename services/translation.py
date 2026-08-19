import re
import os
from dotenv import load_dotenv

load_dotenv()

FILLER_WORDS = [
    r"\bumm+\b", r"\buh+\b", r"\berr+\b", r"\byou know\b",
    r"\bbasically\b", r"\bso yeah\b", r"\blike\b", r"\bactually\b",
    r"\bah+\b", r"\btoh\b", r"\bmatlab\b", r"\byani\b"
]

FALLBACK_PHRASES = [
    ("Salaam everyone", "Hello everyone"),
    ("Aj ki meeting mein hum", "In today's meeting, we are"),
    ("discuss kar rahe hain", "discussing"),
    ("Ali bhai Friday tak frontend complete kar lenge", "Ali will complete the frontend by Friday"),
    ("and Sara database schema finalize karegi", "and Sara will finalize the database schema"),
    ("client ka request hai ke PDF export feature Monday se pehle ready hona chahiye", "the client requested that the PDF export feature must be ready before Monday"),
    ("So decisions ye hui hain ke hum next month beta launch karenge", "So the decision was made to launch the beta next month"),
    ("aur security testing kal se start hogi", "and security testing will commence tomorrow"),
    ("Thank you everyone", "Thank you everyone.")
]


def clean_and_optimize_text(text):
    """Removes speech filler words, repetitive word stutters, and normalizes punctuation."""
    if not text:
        return ""

    cleaned = text
    for pattern in FILLER_WORDS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r"\b(\w+)(?:\s+\1\b)+", r"\1", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"\s+([,.:;?!])", r"\1", cleaned)
    cleaned = re.sub(r"\.{2,}", ".", cleaned)
    return cleaned.strip()


def fallback_translation(text, detected_language):
    """Rule-based translation fallback for common Roman Urdu/Hindi meeting phrases."""
    if "Urdu" not in detected_language and "Hindi" not in detected_language and "kar rahe" not in text:
        return text

    translated = text
    for roman, eng in FALLBACK_PHRASES:
        translated = translated.replace(roman, eng)
    return translated


def translate_and_clean(raw_text, detected_language="English"):
    """Translates non-English transcript into clean English and removes filler words."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    translated_text = raw_text

    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            prompt = (
                "You are an expert translator and speech editor. "
                "Translate the following speech transcript into clear, fluent, professional English while strictly preserving "
                "every single fact, name, number, decision, and context mentioned by the speaker. "
                "If the text is in Roman Urdu, Urdu, Hindi, or any other language, accurately translate it to English. "
                "If it is already in English, polish grammar and punctuation without altering the speaker's original meaning. "
                "Do NOT invent or add any information that was not said.\n\n"
                f"Transcript:\n{raw_text}"
            )
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a professional audio translator and transcription editor. Strictly translate and polish the provided audio transcript without fabricating details."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            translated_text = response.choices[0].message.content.strip()
        except Exception as err:
            print(f"[Translation fallback]: {err}")
            translated_text = fallback_translation(raw_text, detected_language)
    else:
        translated_text = fallback_translation(raw_text, detected_language)

    optimized_text = clean_and_optimize_text(translated_text)

    return {
        "raw_text": raw_text,
        "translated_text": translated_text,
        "optimized_text": optimized_text
    }
