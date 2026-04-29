import os
import operator
from typing import TypedDict, Annotated, Literal, Optional
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field

load_dotenv()

# Require GOOGLE_API_KEY to be set
if not os.environ.get("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY environment variable is missing. Please set it in a .env file.")

# Using Gemini 1.5 Flash as requested, temperature 0 for deterministic outputs and tool calls
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0)

# 1. State Definition
class AppState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    intent: str
    name: Optional[str]
    email: Optional[str]
    platform: Optional[str]

# 2. Structured output definitions
class IntentClassification(BaseModel):
    intent: Literal["GREETING", "RAG", "LEAD_CAPTURE"]
    reasoning: str = Field(description="Reasoning for the chosen intent")

class LeadInfo(BaseModel):
    name: Optional[str] = Field(description="The user's name if provided in the text. Empty if not.", default=None)
    email: Optional[str] = Field(description="The user's email address if provided in the text. Empty if not.", default=None)
    platform: Optional[str] = Field(description="The user's creator platform (e.g. YouTube, Instagram) if provided in the text. Empty if not.", default=None)

# 3. Tool Function (Strictly called when all info is gathered)
def mock_lead_capture(name: str, email: str, platform: str):
    print(f"\n[LEAD CAPTURED] 🎉 Successful Mock Tool Execution!")
    print(f"Name: {name} | Email: {email} | Platform: {platform}\n")
    return {"status": "success"}

# 4. Nodes
def classify_intent_node(state: AppState):
    """Determine the intent of the user's latest message."""
    messages = state.get("messages", [])
    if not messages:
        return {"intent": "GREETING"}
    
    last_user_msg = next((m for m in reversed(messages) if isinstance(m, HumanMessage)), None)
    if not last_user_msg:
        return {"intent": "GREETING"}
        
    classification_prompt = """You are an intent classifier for AutoStream, a video editing SaaS platform.
Classify the user's latest message into one of three intents based on the conversation history:
1. "GREETING": The user is casually greeting, making small talk, or saying hello.
2. "RAG": The user is asking about product features, pricing, or plans.
3. "LEAD_CAPTURE": The user expresses high intent to sign up, buy, or try a plan.

User's latest message: {last_msg}
"""
    structured_llm = llm.with_structured_output(IntentClassification)
    res = structured_llm.invoke(classification_prompt.format(last_msg=last_user_msg.content))
    return {"intent": res.intent}

def greeting_node(state: AppState):
    """Handle casual greetings."""
    sys_msg = SystemMessage(content="You are a friendly agent for AutoStream, automated video editing tools for creators. Respond politely to greetings and introduce the service briefly.")
    res = llm.invoke([sys_msg] + state["messages"])
    return {"messages": [res]}

def rag_node(state: AppState):
    """Answer questions using RAG."""
    with open("knowledge_base.md", "r") as f:
        kb_text = f.read()
    
    prompt = f"""You are an authoritative sales assistant for AutoStream. Answer the user's questions based ONLY on the following knowledge base:
<knowledge_base>
{kb_text}
</knowledge_base>

If the answer is not in the knowledge base, say you don't know but offer to connect them with a human. 
Keep your response concise and persuasive. Do not hallucinate pricing or features."""
    
    msgs = [SystemMessage(content=prompt)] + state["messages"]
    res = llm.invoke(msgs)
    return {"messages": [res]}

def lead_capture_node(state: AppState):
    """Collect lead info iteratively and trigger mock service when full."""
    last_msg = state["messages"][-1].content
    
    # Use LLM to extract any missing info from the latest message
    extractor_llm = llm.with_structured_output(LeadInfo)
    extracted = extractor_llm.invoke(f"Extract lead info from this message if present: {last_msg}")
    
    # Merge existing state with newly extracted info
    current_name = state.get("name") or extracted.name
    current_email = state.get("email") or extracted.email
    current_platform = state.get("platform") or extracted.platform
    
    # Check if we have gathered all 3 specific features
    if current_name and current_email and current_platform:
        # FIRE TOOL!
        mock_lead_capture(current_name, current_email, current_platform)
        
        success_msg = "Fantastic! I've successfully captured your details. Our team will reach out to you shortly to get you set up with your AutoStream plan. Let me know if you need anything else!"
        
        return {
            "messages": [AIMessage(content=success_msg)],
            "name": current_name,
            "email": current_email,
            "platform": current_platform
        }
    else:
        # Construct missing array
        missing = []
        if not current_name: missing.append("name")
        if not current_email: missing.append("email")
        if not current_platform: missing.append("creator platform (e.g. YouTube, Instagram)")
        
        system_prompt = f"""You are an expert sales qualifier for AutoStream. The user wants to sign up or try a plan. 
You need to collect their Name, Email, and Creator Platform. 

You are currently missing: {", ".join(missing)}.

Acknowledge any information they have already provided seamlessly. Do not mention that you have an automated process.
Ask politely for the remaining missing information in a colloquial, helpful tone. Keep it very conversational."""
        
        msgs = [SystemMessage(content=system_prompt)] + state["messages"]
        response = llm.invoke(msgs)
        return {
            "messages": [response],
            "name": current_name,
            "email": current_email,
            "platform": current_platform
        }

def route_intent(state: AppState):
    return state["intent"]

# 5. Build Graph
workflow = StateGraph(AppState)
workflow.add_node("classify", classify_intent_node)
workflow.add_node("GREETING", greeting_node)
workflow.add_node("RAG", rag_node)
workflow.add_node("LEAD_CAPTURE", lead_capture_node)

workflow.add_edge(START, "classify")
workflow.add_conditional_edges("classify", route_intent, {
    "GREETING": "GREETING", 
    "RAG": "RAG", 
    "LEAD_CAPTURE": "LEAD_CAPTURE"
})
workflow.add_edge("GREETING", END)
workflow.add_edge("RAG", END)
workflow.add_edge("LEAD_CAPTURE", END)

# Configure Memory Checkpointer for persisting multi-turn conversation context
memory = MemorySaver()
app_runner = workflow.compile(checkpointer=memory)

def process_message(session_id: str, message: str) -> dict:
    """Invokes the LangGraph chain and returns the AI response text and current state values."""
    config = {"configurable": {"thread_id": session_id}}
    result = app_runner.invoke({"messages": [HumanMessage(content=message)]}, config=config)
    
    # Return both the content and visually what is known
    return {
        "reply": result["messages"][-1].content,
        "state": {
            "intent": result.get("intent", "UNKNOWN"),
            "name": result.get("name"),
            "email": result.get("email"),
            "platform": result.get("platform")
        }
    }
