from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import uvicorn
import json

# LangChain message types
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

# Import your compiled graph and database functions
from agent import workflow as interaction_agent
from database import (
    get_all_logs, 
    save_hcp_interaction, 
    update_hcp_interaction, 
    get_all_hcp_interactions, 
    save_followup
)

app = FastAPI()

# 1. CORS CONFIGURATION
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. SESSION MEMORY
session_store: Dict[str, List] = {}

# 3. REQUEST MODELS
class InteractionRequest(BaseModel):
    user_input: str
    session_id: str 

# 4. MAIN INTERACTION ENDPOINT
@app.post("/log-interaction")
async def log_interaction(request: InteractionRequest):
    print("\n" + "="*50)
    print(f"🔍 DEBUG START: Session {request.session_id}")
    print(f"📥 User Input: {request.user_input}")
    
    try:
        session_id = request.session_id

        # Initialize/Retrieve session
        if session_id not in session_store:
            session_store[session_id] = []
            print("🆕 STATUS: NEW SESSION created.")
        else:
            print(f"📜 STATUS: EXISTING SESSION found. History size: {len(session_store[session_id])}")
        
        # 1. Add Human Message to history
        user_msg = HumanMessage(content=request.user_input)
        session_store[session_id].append(user_msg)

        # 2. Invoke Agent (LangGraph Workflow)
        # The agent will run its loops (Agent -> Tools -> Agent)
        result = interaction_agent.invoke({
            "messages": session_store[session_id]
        })

        # 3. Update Session Store with full message chain (including new ToolMessages)
        session_store[session_id] = result["messages"]

        # --- 🕵️‍♂️ UI TRUTH-FINDER LOGIC: COMBINING TOOL RESULTS WITH AI CHAT ---
        
        # A. Find Tool Results from this specific turn
        # We look at the last few messages to see if a tool just finished executing
        recent_tool_outputs = []
        for msg in reversed(result["messages"]):
            if isinstance(msg, ToolMessage):
                # We stop gathering tool messages once we hit the previous user message
                recent_tool_outputs.append(msg.content)
            if isinstance(msg, HumanMessage):
                break
        
        # B. Find the final AI text response (the 'polite' part)
        ai_reply = ""
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage) and msg.content.strip():
                ai_reply = msg.content
                break
        
        # C. Merge them. If a tool like 'suggest_next_action' ran, 
        # its output is often more "correct" than the AI's final polite check.
        if recent_tool_outputs:
            # We reverse the tool outputs back to chronological order
            tool_context = "\n".join(reversed(recent_tool_outputs))
            reply_content = f"{tool_context}\n\n{ai_reply}".strip()
            print(f"🛠️  MERGED REPLY: Tool data included in response.")
        else:
            reply_content = ai_reply

        # Fallback if somehow everything is empty
        if not reply_content:
            reply_content = "I've processed that for you. Is there anything else you need?"

        # 4. Fetch latest logs for UI Sidebar refresh
        updated_logs = get_all_logs()

        print(f"🤖 FINAL UI REPLY: {reply_content[:100]}...")
        print(f"✅ SUCCESS: {len(updated_logs)} logs sent to UI.")
        print("="*50 + "\n")

        return {
            "reply": reply_content,
            "all_logs": updated_logs,
            "status": "Success"
        }

    except Exception as e:
        print(f"🚨 CRITICAL ERROR in /log-interaction: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# 5. UI SYNC ENDPOINT (Manual Refresh)
@app.get("/get-logs")
async def fetch_logs():
    return get_all_logs()

# 6. SESSION RESET
@app.post("/reset-session/{session_id}")
async def reset_session(session_id: str):
    if session_id in session_store:
        del session_store[session_id]
        print(f"🗑️ Session {session_id} cleared.")
    return {"status": "Reset successful"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)