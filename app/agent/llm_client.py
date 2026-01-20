import os
from groq import Groq
from openai import OpenAI
from app.utils.config import GROQ_API_KEY, GROQ_API_KEY_2, OPENAI_API_KEY

# Initialize clients
groq_client_1 = Groq(api_key=GROQ_API_KEY)
groq_client_2 = Groq(api_key=GROQ_API_KEY_2) if GROQ_API_KEY_2 else None
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

def chat_json(system_prompt: str, user_prompt: str, model="llama-3.3-70b-versatile", client_num=1):
    """
    Send prompt and force JSON output using Groq.
    client_num: 1 or 2 to select which Groq API key to use
    """
    client = groq_client_1 if client_num == 1 else groq_client_2
    if not client:
        raise ValueError(f"Groq client {client_num} not configured")
    
    resp = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2
    )
    return resp.choices[0].message.content

def chat_json_openai(system_prompt: str, user_prompt: str, model="gpt-4o-mini"):
    """
    Send prompt and force JSON output using OpenAI ChatGPT.
    """
    if not openai_client:
        raise ValueError("OpenAI API key not configured")
    
    resp = openai_client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2
    )
    return resp.choices[0].message.content
