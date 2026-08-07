import os
from openai import OpenAI
from dotenv import load_dotenv
from services.analyzer import detect_complexity

load_dotenv()  

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def process_slide(text):
    if not text or text.strip() == "":
        return "No readable content on this slide."

    try:
        is_complex = detect_complexity(text)

        if is_complex:
            instruction = "Explain complex concepts clearly with simple examples."
        else:
            instruction = "Only provide summary. Do NOT add extra explanation."

        prompt = f"""
You are an AI study assistant.

Analyze the slide content below and respond in this EXACT format:

SUMMARY:
- bullet point 1
- bullet point 2
- bullet point 3

EXPLANATION:
- explanation or "None"

Slide Content:
{text}

Instructions:
1. Provide a clear summary (3-5 bullets).
2. {instruction}
3. Keep output structured exactly as shown.
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3  # more consistent output
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Error processing slide: {str(e)}"