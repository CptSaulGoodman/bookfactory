import json
import asyncio
import fastapi
from sse_starlette.sse import EventSourceResponse
from langchain_openai import ChatOpenAI

# 1. Create a FastAPI app instance
app = fastapi.FastAPI()

# 2. Hardcode the configuration for the ChatOpenAI client
model = ChatOpenAI(
    openai_api_base="http://192.168.22.251:8090/v1",
    openai_api_key="ollama",
    model_name="gemma-3-12b",
)

# 3. Implement an event_generator async function
async def event_generator():
    """
    Calls model.astream() and yields formatted server-sent events.
    """
    async for chunk in model.astream("Tell me a short story."):
        content = chunk.content
        if content:
            try:
                # The content from astream is often a string representation of a dict
                # We need to handle potential JSON parsing errors
                if isinstance(content, str):
                    # It might be a JSON string, so we try to parse it
                    try:
                        data = json.loads(content)
                        if isinstance(data, dict) and "content" in data:
                            text_content = data["content"]
                        else:
                            # If not a dict with 'content', use the string directly
                            text_content = content
                    except json.JSONDecodeError:
                        # If it's not valid JSON, treat it as plain text
                        text_content = content
                elif isinstance(content, dict) and "content" in content:
                    text_content = content["content"]
                else:
                    text_content = str(content)

                if text_content:
                    yield {"data": text_content}

            except Exception as e:
                # Log errors if something unexpected happens
                print(f"Error processing chunk: {e}")
                # Optionally yield an error event to the client
                yield {"event": "error", "data": str(e)}
    # Signal the end of the stream
    yield {"event": "end", "data": "Stream ended"}


# 4. Create a FastAPI endpoint
@app.get("/stream-test")
async def stream_test(request: fastapi.Request):
    """
    Endpoint to stream AI-generated content using SSE.
    """
    return EventSourceResponse(event_generator())