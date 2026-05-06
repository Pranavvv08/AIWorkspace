import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
import json

load_dotenv()

# We use the mini model as requested by the user for cost efficiency
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def process_chat_message(message: str, history: list) -> dict:
    if not os.getenv("OPENAI_API_KEY"):
        # Mock behavior if no API key is provided
        tasks = []
        if "build" in message.lower() or "need to" in message.lower() or "task" in message.lower():
            tasks = [{"title": "Example extracted task", "priority": "Medium"}]
        return {"reply": "This is your AI Agent. (API Key not set up). I have received your message.", "tasks": tasks}

    messages_payload = [
        {"role": "system", "content": "You are a helpful AI Personal Agent. Analyze the user message, respond naturally, and if there are any actionable tasks mentioned by the user, extract them. You must return a JSON object with two keys: 'reply' (your natural conversational response) and 'tasks' (an array of objects with 'title' and 'priority' [High, Medium, Low]). If no tasks, 'tasks' should be []."}
    ]
    
    for msg in history[-5:]: # Include last 5 messages for context
        role = "assistant" if msg.role == "ai" else msg.role
        messages_payload.append({"role": role, "content": msg.content})
        
    messages_payload.append({"role": "user", "content": message})

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages_payload,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        return data
    except Exception as e:
        print(f"Agent error: {e}")
        return {"reply": "I'm having trouble connecting to my brain (OpenAI) right now.", "tasks": []}
