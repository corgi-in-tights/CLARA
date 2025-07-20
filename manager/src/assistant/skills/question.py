import json
import os
import httpx
from ..responses import send_text_response

from openai import AsyncOpenAI


client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def search_internet(query: str) -> str:
    """Perform a search using SerpAPI and return top result snippets."""
    url = "https://serpapi.com/search"
    params = {
        "q": query,
        "engine": "google",
        "api_key": os.getenv("SEARCH_API_KEY"),
        "num": 3,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            results = data.get("organic_results", [])
            if not results:
                return "No relevant information found."

            # Extract top 3 snippets
            snippets = []
            for r in results[:3]:
                title = r.get("title")
                snippet = r.get("snippet", "No snippet available.")
                link = r.get("link", "")
                snippets.append(f"{title} - {snippet} ({link})")

            return "\n\n".join(snippets)

        except Exception as e:
            return f"Search failed: {e}"

async def get_response_from_llm(model_data: dict, question: str, use_search: bool = False) -> str:
    model_name = model_data.get("model", "gpt-4o")

    system_msg = {
        "role": "system",
        "content": (
            "You are CLARA, an expert AI assistant. "
            "Provide clear, concise, and accurate answers. Keep all responses under 50 words. "
            "If you use external information, cite it in your response. "
            "If you are unsure, say so rather than guessing. "
            "Under no circumstances should you provide any medical advice without informing them to see a licensed professional. "
            "You are not a medical professional, and you should not provide any medical advice. "
            "Always source your information when using external data. Only use human pronouncable syntax, no markdown. If the information is sourced, start with 'From XYZ.com, ' and then provide the answer."
            "As CLARA, you are a nursing companion and assistant for convenience, you help people build routines, navigate their health, and store information."
        ),
    }

    user_msg = {
        "role": "user",
        "content": (
            f"Here is my question:\n{question}\n"
            "Please answer thoroughly and include sources if relevant. Do not use more than 2 sources and keep it under 50 words."
        ),
    }

    if not use_search:
        try:
            response = await client.chat.completions.create(
                model=model_name,
                messages=[system_msg, user_msg],
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error while generating response: {e}"

    # --- Use search with tool/function calling ---
    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_web",
                "description": "Search the internet for up-to-date information.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]

    try:
        initial_response = await client.chat.completions.create(
            model=model_name,
            messages=[system_msg, user_msg],
            temperature=0.7,
            tools=tools,
            tool_choice="auto",  # GPT decides to call or not
        )
    except Exception as e:
        return f"Error during initial generation: {e}"

    message = initial_response.choices[0].message

    if message.tool_calls:
        tool_call = message.tool_calls[0]
        function_args_str = tool_call.function.arguments

        try:
            function_args = json.loads(function_args_str)
            query = function_args.get("query")
        except Exception:
            return "Error parsing function call arguments."

        search_results = await search_internet(query)

        messages = [
            system_msg,
            user_msg,
            {
                "role": "assistant",
                "tool_calls": [tool_call],
            },
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": "search_web",
                "content": search_results,
            },
        ]

        try:
            final_response = await client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.7,
            )
            return final_response.choices[0].message.content
        except Exception as e:
            return f"Error during final generation: {e}"

    # GPT did not call tool, just responded
    return message.content


async def local_question(target_url, sentence, initial_response):
    print(f"Local question: {sentence}")
    await send_text_response(target_url, initial_response)
    response = await get_response_from_llm({}, sentence)
    await send_text_response(target_url, response)

async def internet_question(target_url, sentence, initial_response):
    print(f"Internet question: {sentence}")
    await send_text_response(target_url, initial_response)
    response = await get_response_from_llm({}, sentence, use_search=True)
    await send_text_response(target_url, response)
