import os
import logging
import tempfile
import requests
import base64
from dotenv import load_dotenv

from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai

load_dotenv()

app = Flask(__name__)
CORS(app, resources={
    r"/generate-audio-guide": {
        "origins": [
            "http://127.0.0.1:5500",
            "http://localhost:5500",
            "https://travelguide-frontend-xi.vercel.app"
        ]
    }
})
logging.basicConfig(level=logging.INFO)

PROMPTS = {
    "Summary": """
You are a professional tourist guide.

Provide a concise but informative overview of "{place}" in {language}.

Cover:
- Historical significance
- Why the place is famous
- Important architectural or cultural highlights
- A few interesting visitor insights

Keep the response between 1200 and 2200 characters.
Do not exceed 2500 characters.

Write it as a natural audio guide that sounds good when spoken aloud.
""",
    "Detailed": """
You are a professional tourist guide.

Provide a detailed but concise explanation of "{place}" in {language}.

Cover:
- Historical background
- Architectural design and unique features
- Cultural importance
- Notable events
- Interesting facts
- Visitor insights

Keep the response between 1800 and 2500 characters.
Do not exceed 2700 characters.

Write it as a natural audio guide that sounds good when spoken aloud.
"""
}

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing GOOGLE_API_KEY environment variable.")

client = genai.Client(api_key=API_KEY)


def generate_description(place, answer_type, language):
    prompt_template = PROMPTS.get(answer_type, PROMPTS["Summary"])
    prompt = prompt_template.format(place=place, language=language)
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
    )
    return response.text

def generate_speech(text, voice_id, locale):
    if len(text) > 2800:
        text = text[:2800]

        # Avoid cutting the audio in the middle of a sentence
        last_period = text.rfind(".")
        if last_period > 1500:
            text = text[:last_period + 1]

    temp_file = tempfile.NamedTemporaryFile(
        suffix=".mp3",
        delete=False
    )

    url = "https://global.api.murf.ai/v1/speech/stream"

    headers = {
        "api-key": os.getenv("MURF_API_KEY"),
        "Content-Type": "application/json"
    }

    data = {
        "voice_id": voice_id,
        "text": text,
        "locale": locale,
        "model": "FALCON",
        "format": "MP3",
        "sampleRate": 24000,
        "channelType": "MONO"
    }

    response = requests.post(
        url,
        headers=headers,
        json=data
    )

    if response.status_code == 200:
        with open(temp_file.name, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

        logging.info("Audio streaming completed.")
    else:
        logging.error(
            "Murf API error: %s - %s",
            response.status_code,
            response.text
        )
        raise RuntimeError(
            f"Murf API request failed: HTTP {response.status_code}"
        )

    return temp_file


@app.route("/generate-audio-guide", methods=["POST"])
def generate_audio_guide():
    data = None

    try:
        data = request.get_json()

        if not isinstance(data, dict):
            raise ValueError("Request body must be a JSON object.")

        place = data.get("place")

        if not isinstance(place, str) or not place.strip():
            raise ValueError("A non-empty place is required.")

        answer_type = data.get("answerType", "Summary")
        language = data.get("language", "English")

        voice_id = data.get("voiceId")
        locale = data.get("locale")

        logging.info(
            "Voice settings: voice_id=%s, locale=%s",
            voice_id,
            locale
        )

        text_description = generate_description(
            place,
            answer_type,
            language
        )

        audio_path = generate_speech(
            text_description,
            voice_id,
            locale
        )

        audio_bytes = open(audio_path.name, "rb").read()

        encoded_audio = base64.b64encode(
            audio_bytes
        ).decode("utf-8")

        return jsonify({
            "success": True,
            "description": text_description,
            "audioBase64": encoded_audio
        })

    except Exception as error:
        place = data.get("place") if isinstance(data, dict) else None

        logging.exception(
            "Failed to generate audio guide for place %r",
            place
        )

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
