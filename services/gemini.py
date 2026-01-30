from google import genai
from config import GEMINI_API_KEY

# Initialize client once (same responsibility as old URL)
client = genai.Client(api_key=GEMINI_API_KEY)

def call_gemini(user_input: str) -> str:
    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=user_input,
        )

        # Defensive checks (old code had silent failure)
        if not response or not hasattr(response, "text"):
            return "Gemini returned no usable response."

        return response.text

    except Exception as e:
        return f"Gemini error: {str(e)}"
