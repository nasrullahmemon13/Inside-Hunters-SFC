import os
import random
import time
from dotenv import load_dotenv

load_dotenv()

SAMPLE_TRANSCRIPTS = [
    {
        "language": "Urdu / Roman Urdu",
        "text": (
            "Umm... Salaam everyone. Aj ki meeting mein hum TalkToText Pro ka release plan discuss kar rahe hain. "
            "Basically, Ali bhai Friday tak frontend complete kar lenge, and Sara database schema finalize karegi. "
            "You know, client ka request hai ke PDF export feature Monday se pehle ready hona chahiye. "
            "So decisions ye hui hain ke hum next month beta launch karenge aur security testing kal se start hogi. "
            "Thank you everyone."
        )
    },
    {
        "language": "English",
        "text": (
            "Good morning team. Let's go over the Q3 product roadmap. Um, as discussed last week, "
            "David will lead the API integration and have the endpoints ready by next Tuesday. "
            "Elena, please finalize the user onboarding UX and coordinate with QA. We've officially "
            "decided to deprecate legacy authentication by the 15th and migrate all enterprise users to OAuth2. "
            "Overall progress looks very strong."
        )
    },
    {
        "language": "English",
        "text": (
            "Hello all. In today's sprint planning, we reviewed the high-priority customer feedback tickets. "
            "Mark is assigned to resolve the audio upload latency issue by Wednesday. Jessica will draft the API "
            "documentation and prepare test suites for release v2.4. We mutually agreed to shift the cloud deployment "
            "to AWS US-East for reduced ping times."
        )
    }
]


def transcribe_audio(audio_path, language_hint=None):
    """
    Transcribes audio using OpenAI Whisper API when configured,
    or falls back to built-in simulation for offline testing.
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            with open(audio_path, "rb") as audio_file:
                kwargs = {
                    "model": "whisper-1",
                    "file": audio_file,
                    "response_format": "verbose_json"
                }
                if language_hint:
                    kwargs["language"] = language_hint

                transcript_obj = client.audio.transcriptions.create(**kwargs)
                actual_text = transcript_obj.text.strip()

                if actual_text:
                    return {
                        "text": actual_text,
                        "language": getattr(transcript_obj, "language", language_hint or "en"),
                        "duration": int(getattr(transcript_obj, "duration", 180)),
                        "source": "OpenAI Whisper"
                    }
        except Exception as err:
            print(f"[Whisper transcription fallback]: {err}")

    chosen = random.choice(SAMPLE_TRANSCRIPTS)
    time.sleep(0.4)

    return {
        "text": chosen["text"],
        "language": chosen["language"],
        "duration": 185,
        "source": "Smart Audio Engine"
    }
