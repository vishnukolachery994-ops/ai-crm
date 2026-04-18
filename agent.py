import os
from typing import TypedDict, Annotated, List, Any
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages

# 1. Load environment variables
load_dotenv()

# --- 2. DEFINE TOOLS ---

@tool
def log_interaction(doctor: str, topic: str, summary: str, sentiment: str):
    """
    Logs a new interaction with an HCP.
    """
    from database import save_hcp_interaction
    
    try:
        data = {
            "doctor": doctor,
            "topic": topic,
            "summary": summary,
            "sentiment": sentiment
        }
        save_hcp_interaction(data)
        return f"CONFIRMED: Interaction with {doctor} saved."
    except Exception as e:
        return f"DATABASE ERROR: {str(e)}"


@tool
def edit_interaction(updated_content: str, log_id: Any = None, doctor_name: str = None):
    """Updates a log. Provide log_id OR doctor_name."""
    from database import update_hcp_interaction, get_latest_interaction_by_doctor
    
    target_id = None
    
    # 1. Resolve ID from Doctor Name if ID is missing
    if doctor_name and not log_id:
        latest = get_latest_interaction_by_doctor(doctor_name)
        if latest:
            target_id = latest['id']
        else:
            return f"ERROR: Could not find any previous interactions for Dr. {doctor_name}."
    else:
        target_id = log_id

    # 2. Final Check and Execution
    if target_id:
        try:
            # Explicitly cast to int to prevent DB type errors
            success = update_hcp_interaction(int(target_id), updated_content)
            if success:
                return f"SUCCESS: Log #{target_id} has been updated."
            return f"FAILURE: Log #{target_id} could not be updated in the database."
        except ValueError:
            return "ERROR: Invalid ID format provided."
    
    return "ERROR: No Log ID or Doctor Name provided to identify which log to edit."
@tool
def get_hcp_insights(name: str):
    """
    Retrieves and summarizes all past interactions with a doctor.
    """
    from database import get_all_hcp_interactions

    try:
        records = get_all_hcp_interactions(name)

        if not records:
            return f"No history found for {name}."

        total = len(records)
        latest = records[-1]

        sentiments = [r["sentiment"].lower() for r in records]
        positive = sentiments.count("positive")
        negative = sentiments.count("negative")

        if positive > negative:
            overall = "Positive"
        elif negative > positive:
            overall = "Negative"
        else:
            overall = "Mixed/Neutral"

        topics = list(set([r["topic"] for r in records]))

        return (
            f"HCP INSIGHTS:\n"
            f"Doctor: {name}\n"
            f"Total Interactions: {total}\n"
            f"Overall Sentiment: {overall}\n"
            f"Topics: {', '.join(topics)}\n"
            f"Latest Interaction:\n"
            f"- Topic: {latest['topic']}\n"
            f"- Summary: {latest['summary']}\n"
            f"- Sentiment: {latest['sentiment']}"
        )

    except Exception as e:
        return f"DATABASE ERROR: {str(e)}"


# 🔥 NEW TOOL 2: NEXT ACTION
@tool
def suggest_next_action(name: str):
    """
    Suggests next best action based on past interactions.
    """
    from database import get_all_hcp_interactions

    try:
        records = get_all_hcp_interactions(name)

        if not records:
            return f"No past data for {name}. Start with an introductory visit."

        latest = records[-1]
        sentiment = latest["sentiment"].lower()
        topic = latest["topic"]

        if sentiment == "positive":
            action = f"Schedule follow-up and pitch advanced benefits of {topic}."
        elif sentiment == "negative":
            action = f"Address concerns about {topic} before re-engaging."
        else:
            action = f"Provide educational material on {topic}."

        return f"RECOMMENDATION for {name}: {action}"

    except Exception as e:
        return f"ERROR: {str(e)}"


# 🔥 NEW TOOL 3: FOLLOW-UP (DB CONNECTED)
@tool
def schedule_follow_up(doctor: str, date: str, purpose: str):
    """
    Schedules a follow-up meeting. Format: YYYY-MM-DD.
    """
    from database import save_followup

    try:
        save_followup({
            "doctor": doctor,
            "date": date,
            "purpose": purpose
        })
        return f"SCHEDULED: Follow-up with {doctor} on {date}."
    except Exception as e:
        return f"ERROR: {str(e)}"


# --- TOOL LIST ---
tools = [
    log_interaction,
    edit_interaction,
    get_hcp_insights,
    suggest_next_action,
    schedule_follow_up
]

tool_node = ToolNode(tools)

# --- 3. DEFINE STATE ---

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

# --- 4. LLM SETUP ---

api_key = os.getenv("GROQ_API_KEY")

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    groq_api_key=api_key,
    temperature=0
).bind_tools(tools)

# --- 5. NODES ---

def call_model(state: AgentState):
    messages = state['messages']
    
    if not any(isinstance(m, SystemMessage) for m in messages):
        # Inside agent.py -> call_model function
        # Inside agent.py -> call_model function
        system_prompt = SystemMessage(content=(
    "You are a Clinical AI Assistant. You have strict rules for tool usage:\n"
    "1. If the user provides info about a doctor you ALREADY see in the conversation or says 'Update', 'Change', or 'Add to', "
    "you MUST use 'edit_interaction'. DO NOT create a new log.\n"
    "2. ONLY use 'log_interaction' if this is the very first time this doctor is being mentioned in this session.\n"
    "3. If you are unsure if a doctor exists, use 'get_hcp_insights' first to check history.\n"
    "Be precise. Duplicate logs are a system failure."
))
        messages = [system_prompt] + messages

    response = llm.invoke(messages)
    return {"messages": [response]}


def should_continue(state: AgentState):
    last_message = state['messages'][-1]
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    
    return END

# --- 6. GRAPH ---

builder = StateGraph(AgentState)

builder.add_node("agent", call_model)
builder.add_node("tools", tool_node)

builder.set_entry_point("agent")
builder.add_conditional_edges("agent", should_continue)
builder.add_edge("tools", "agent")

workflow = builder.compile()

# --- 7. TEST ---

if __name__ == "__main__":
    print("--- 🔍 STARTING AGENT TRACE ---")
    
    inputs = {
        "messages": [
            HumanMessage(content="I met Dr. Vishnu. He was positive about the Vaccine.")
        ]
    }

    for output in workflow.stream(inputs):
        print(output)