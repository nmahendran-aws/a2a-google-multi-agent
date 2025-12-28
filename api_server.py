
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import vertexai
from vertexai import agent_engines
from dotenv import load_dotenv

# Load env variables from the purchasing_concierge specific .env directly
load_dotenv("./purchasing_concierge/.env")

app = FastAPI()

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development convenience
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Vertex AI
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
STAGING_BUCKET = os.getenv("STAGING_BUCKET")
AGENT_ENGINE_RESOURCE_NAME = os.getenv("AGENT_ENGINE_RESOURCE_NAME")

print(f"Initializing Vertex AI with Project: {PROJECT_ID}, Location: {LOCATION}")
print(f"Targeting Agent Engine: {AGENT_ENGINE_RESOURCE_NAME}")

vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET,
)

# Initialize Agent Engine connection
try:
    REMOTE_APP = agent_engines.get(AGENT_ENGINE_RESOURCE_NAME)
    print("Successfully connected to Agent Engine.")
except Exception as e:
    print(f"Failed to connect to Agent Engine: {e}")
    REMOTE_APP = None

class ChatRequest(BaseModel):
    user_id: str
    message: str
    session_id: str | None = None

class ChatResponse(BaseModel):
    session_id: str
    response_text: str
    tool_calls: list[dict] = []

@app.post("/chat")
async def chat(request: ChatRequest):
    if not REMOTE_APP:
        raise HTTPException(status_code=503, detail="Agent Engine not connected")

    # Reuse session or create new one
    session_id = request.session_id
    if not session_id:
        try:
            print(f"Creating new session for user: {request.user_id}")
            session = REMOTE_APP.create_session(user_id=request.user_id)
            session_id = session["id"]
        except Exception as e:
             raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

    print(f"Querying Agent Engine (Session: {session_id}): {request.message}")
    
    full_text = ""
    tool_usage = []

    try:
        # Stream response from Agent Engine
        for event in REMOTE_APP.stream_query(
            user_id=request.user_id,
            session_id=session_id,
            message=request.message,
        ):
            parts = event.get("content", {}).get("parts", [])
            for part in parts:
                if "text" in part:
                     full_text += part["text"]
                if "function_call" in part:
                    tool_usage.append({
                        "type": "function_call",
                        "name": part["function_call"].get("name"),
                        "args": part["function_call"].get("args")
                    })
                if "function_response" in part:
                     tool_usage.append({
                        "type": "function_response",
                        "name": part["function_response"].get("name"),
                        # Response might be large, maybe truncate or struct log in real app
                        "snippet": str(part["function_response"].get("response"))[:200]
                    })
    except Exception as e:
        print(f"Error during streaming query: {e}")
        raise HTTPException(status_code=500, detail=f"Agent query failed: {str(e)}")

    if not full_text and not tool_usage:
        full_text = "No response received from agent."

    return {
        "session_id": session_id,
        "response_text": full_text,
        "tool_calls": tool_usage
    }

if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
