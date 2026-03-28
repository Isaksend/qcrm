import os
import google.generativeai as genai
from typing import List, Optional
import json

# Setup
def get_analyzer():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-1.5-flash')

async def analyze_chat_probability(messages_text: str):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    genai.configure(api_key=api_key)
    
    # Try models in order of preference based on your account's available models
    models_to_try = [
        'models/gemini-2.0-flash', 
        'models/gemini-2.5-flash', 
        'models/gemini-flash-latest', 
        'models/gemini-1.5-flash',
        'models/gemini-pro-latest'
    ]
    
    prompt = f"""
    Analyze the following chat transcript between a Sales Manager and a Client in a CRM system.
    Transcript:
    {messages_text}

    Based on this conversation, estimate the probability of a successful deal (0-100%).
    Return the response strictly as a JSON object with the following fields:
    - confidence: integer (0-100)
    - title: string (short catchy title for the insight)
    - content: string (detailed reasoning and sentiment analysis)
    - suggestions: list of strings (3 tactical next steps for the manager)
    
    The sentiment analysis should detect if the client is interested, skeptical, or indifferent.
    JSON:
    """

    last_error = ""
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = await model.generate_content_async(prompt)
            text = response.text.strip()
            
            # Clean up possible markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            return json.loads(text)
        except Exception as e:
            last_error = str(e)
            print(f"AI: Model {model_name} failed: {e}")
            continue

    return {
        "confidence": 0,
        "title": "AI Service Unavailable",
        "content": f"All Gemini models failed. Last error: {last_error}",
        "suggestions": ["Check if your API key is valid", "Check Google Cloud Console quotas"]
    }
