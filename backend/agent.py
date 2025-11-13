"""
Full Movi Agent with Langgraph - Tribal Knowledge Implementation
Implements the complete consequence checking and confirmation flow with LLM integration
"""

from typing import List, Annotated, TypedDict, Optional, Dict, Any, Literal
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage, BaseMessage
from langchain_openai import ChatOpenAI
import os
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0"))

# Mode detection
USE_LLM_MODE = OPENAI_API_KEY is not None

if USE_LLM_MODE:
    print("🤖 Movi Agent: LLM Mode (GPT-4) ✅")
else:
    print("📝 Movi Agent: Demo Mode (Rule-based) - Add OPENAI_API_KEY to .env for LLM mode")

# Import tools
from tools import (
    get_trip_status,
    get_unassigned_vehicles,
    list_stops_for_path,
    list_routes_for_path,
    create_daily_trip,
    assign_vehicle_and_driver,
    delete_daily_trip,
    remove_vehicle_from_trip,
    create_new_stop,
    create_new_path,
    create_new_route,
    deactivate_route,
    list_all_routes,
    get_all_drivers,
    get_trip_bookings,
    get_vehicle_details
)

# Import database utilities for consequence checking
import db_utils


# ============================================================================
# AGENT STATE DEFINITION
# ============================================================================

class AgentState(TypedDict):
    """
    State for the Movi agent with tribal knowledge
    
    Fields:
        messages: Chat history with automatic message reduction
        currentPage: UI context (busDashboard or manageRoute)
        confirmation_pending: Flag indicating we're waiting for user confirmation
        action_to_confirm: The tool call that needs confirmation
        consequence_info: Details about the consequences detected
        image_data: Optional image bytes for vision processing (future)
    """
    messages: Annotated[List[BaseMessage], add_messages]
    currentPage: str
    confirmation_pending: bool
    action_to_confirm: Optional[Dict[str, Any]]
    consequence_info: Optional[Dict[str, Any]]
    image_data: Optional[bytes]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_all_tools():
    """Returns list of all available tools for binding to LLM"""
    return [
        get_trip_status,
        get_unassigned_vehicles,
        list_stops_for_path,
        list_routes_for_path,
        create_daily_trip,
        assign_vehicle_and_driver,
        delete_daily_trip,
        remove_vehicle_from_trip,
        create_new_stop,
        create_new_path,
        create_new_route,
        deactivate_route,
        list_all_routes,
        get_all_drivers,
        get_trip_bookings,
        get_vehicle_details
    ]


def process_image_with_vision(image_data: bytes, user_message: str, current_page: str) -> str:
    """
    Process an image using GPT-4o Vision API to extract information
    
    Args:
        image_data: Raw image bytes
        user_message: User's text message accompanying the image
        current_page: Current UI page context
    
    Returns:
        Extracted information from the image (e.g., trip names, route details)
    """
    import base64
    
    if not USE_LLM_MODE:
        return "Vision processing requires OpenAI API key. Please add OPENAI_API_KEY to .env file."
    
    try:
        # Encode image to base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Create vision-enabled model (GPT-4o supports vision)
        vision_llm = ChatOpenAI(
            model="gpt-4o",  # GPT-4o has vision capabilities
            temperature=0,
            api_key=OPENAI_API_KEY
        )
        
        # Create context-aware prompt based on current page
        if current_page == "busDashboard":
            context_prompt = """You are analyzing a screenshot from the busDashboard page of a transport management system.

The busDashboard shows:
- A list of daily trips in the left panel (each trip has a name like "Bulk - 00:01", "Path-1 Evening - 19:00", etc.)
- Each trip shows booking percentage and status
- The right panel shows details for the selected trip including vehicle and driver assignments

Your task: Extract relevant information from the screenshot to help process the user's request.

Look for:
1. Trip names (like "Bulk - 00:01", "Path Path - 00:02", etc.)
2. Booking percentages
3. Vehicle license plates (like "KA-01-AB-1234")
4. Driver names
5. Any highlighted or pointed-out items (red arrows, circles, etc.)

Be specific and precise. If the user is pointing to a specific trip, identify it by its exact display name."""
        
        elif current_page == "manageRoute":
            context_prompt = """You are analyzing a screenshot from the manageRoute page of a transport management system.

The manageRoute page shows:
- Routes with their names, times, and paths
- Stop sequences for paths
- Route statuses (active/deactivated)

Your task: Extract relevant information from the screenshot to help process the user's request.

Look for:
1. Route names (like "Path-1 - 07:00")
2. Stop names in sequences
3. Path names
4. Any highlighted or pointed-out items

Be specific and precise."""
        
        else:
            context_prompt = "You are analyzing a screenshot from a transport management system. Extract any relevant information about trips, routes, vehicles, or drivers that could help process the user's request."
        
        # Build the vision message
        vision_message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": f"{context_prompt}\n\nUser's request: {user_message}\n\nPlease analyze the image and extract the relevant information to help fulfill this request. Be concise and specific."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ]
        )
        
        # Get vision analysis
        response = vision_llm.invoke([vision_message])
        
        print(f"🔍 Vision Analysis Result: {response.content}")
        
        return response.content
            
    except Exception as e:
        print(f"❌ Vision processing error: {e}")
        return f"Error processing image: {str(e)}"


def speakable_identifier(identifier: str) -> str:
    """
    Convert identifiers like license plates into a TTS-friendly format.
    Example: 'KA-10-QR-3456' -> 'K A dash 1 0 dash Q R dash 3 4 5 6'
    """
    if not identifier:
        return ""
    
    parts = []
    for segment in identifier.split("-"):
        cleaned = segment.strip()
        if not cleaned:
            continue
        spoken_chars = " ".join(list(cleaned.upper()))
        parts.append(spoken_chars)
    return " dash ".join(parts)


def format_trip_status(raw_text: str) -> str:
    """
    Convert raw trip status output into a natural, TTS-friendly sentence.
    """
    text = raw_text.strip()
    pattern = (
        r"Trip '(?P<trip>.+?)': Status: (?P<status>[^,]+), "
        r"Booking: (?P<booking>[\d\.]+)%"
        r"(?:, Vehicle: (?P<vehicle>[^,]+))?"
        r"(?:, Driver: (?P<driver>.+))?"
    )
    match = re.match(pattern, text)
    if not match:
        return text

    trip_name = match.group("trip")
    status = match.group("status").strip()
    booking = match.group("booking").strip()
    vehicle = match.group("vehicle")
    driver = match.group("driver")

    # Clean booking value (remove trailing .0)
    if booking.endswith(".0"):
        booking = booking[:-2]

    parts = [
        f"The {trip_name} trip is currently {status}.",
        f"It's {booking} percent booked."
    ]

    if vehicle and vehicle.lower() not in {"none", "null", "n/a"}:
        parts.append(f"The assigned vehicle is {speakable_identifier(vehicle)}.")
    else:
        parts.append("There is no vehicle assigned right now.")

    if driver and driver.lower() not in {"none", "null", "n/a"}:
        parts.append(f"The driver on duty is {driver}.")
    else:
        parts.append("No driver has been assigned yet.")

    return " ".join(parts)


def format_tool_output(tool_name: str, raw_result: Any) -> str:
    """
    Post-process tool outputs into natural, TTS-friendly language.
    """
    text = str(raw_result).strip()

    # Don't touch error messages
    if text.lower().startswith("error"):
        return text

    if tool_name == "get_trip_status":
        return format_trip_status(text)

    # Future: add more formatters here

    return text


# ============================================================================
# NODE 1: CALL_MODEL (Main LLM Node)
# ============================================================================

def call_model(state: AgentState) -> AgentState:
    """
    Main LLM node - binds tools and decides what action to take
    This uses OpenAI's function calling to understand user intent
    Handles multimodal input (text + images).
    """
    messages = state["messages"]
    current_page = state.get("currentPage", "unknown")
    image_data = state.get("image_data")
    
    print(f"\n🧠 CALL_MODEL Node")
    print(f"   Page: {current_page}")
    print(f"   Messages: {len(messages)}")
    print(f"   Has Image: {image_data is not None}")
    
    # Process image first if present
    vision_context = None
    if image_data:
        print(f"📷 Processing image with GPT-4o Vision...")
        last_user_message = ""
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                last_user_message = msg.content
                break
        
        vision_context = process_image_with_vision(image_data, last_user_message, current_page)
        print(f"🔍 Vision extracted: {vision_context[:150]}...")
        
        # Add vision context to messages for the agent
        if vision_context:
            messages.append(SystemMessage(content=f"📷 Image Analysis:\n{vision_context}"))
        
        # Clear image data after processing to avoid reprocessing
        state["image_data"] = None
    
    if USE_LLM_MODE:
        # PRODUCTION MODE: Use GPT-4 with tool binding
        try:
            llm = ChatOpenAI(
                model=OPENAI_MODEL,
                temperature=OPENAI_TEMPERATURE
            )
            llm_with_tools = llm.bind_tools(get_all_tools())
            
            # Add ReAct-style system message for human-like reasoning
            system_message = SystemMessage(
                content=(
                    "You are Movi, an intelligent transport management assistant for MoveInSync. "
                    "You follow a Reasoning plus Acting pattern to help users.\n\n"
                    f"Current context:\n"
                    f"- Page: {current_page}\n"
                    "- You have sixteen specialized tools, including create and delete daily trips.\n\n"
                    "Important: Your replies are spoken aloud through text to speech.\n"
                    "Speak naturally, like a friendly assistant. Use short sentences and natural pauses. "
                    "Avoid technical jargon and avoid colon-separated data dumps. Present tool results in plain language. "
                    "Keep numeric identifiers such as 'Test-1' or '00:01' exactly as digits. "
                    "When you mention identifiers such as license plates, for example KA-10-QR-3456, "
                    "separate the characters so they are easy to understand aloud.\n\n"
                    "Example of a robotic response to avoid:\n"
                    "Trip 'Path-1 Evening - 19:00': Status: DEPLOYED, Booking: 60.0%, Vehicle: KA-02-CD-5678, Driver: Rajesh Singh.\n\n"
                    "Example of a natural response to emulate:\n"
                    "The Path-1 Evening trip at seven PM is currently deployed. It is sixty percent booked. "
                    "The assigned vehicle is K A dash zero two dash C D dash five six seven eight, "
                    "and the driver on duty is Rajesh Singh.\n\n"
                    "Workflow you must follow:\n"
                    "Think: briefly explain what you understand from the user's request.\n"
                    "Act: call tools when you need real data.\n"
                    "Observe and reformulate: present tool results in natural, speakable language.\n\n"
                    "Response tips:\n"
                    "- Start by acknowledging the request, for example, 'Let me check that for you.'\n"
                    "- Present findings in conversational sentences, such as, 'It looks like the trip is still not started.'\n"
                    "- Use transitions like 'Additionally' or 'Also' when adding details.\n"
                    "- Keep the pace comfortable for listening.\n"
                    "- Avoid abbreviations or dense strings that do not read well aloud.\n\n"
                    "Example conversation:\n"
                    "User: What's the status of Bulk - 00:01?\n"
                    "You: Let me check that trip for you.\n"
                    "Tool result: Trip 'Bulk - 00:01': Status: 00:01 IN, Booking: 25.0%\n"
                    "You: The Bulk trip at zero zero zero one is currently in progress and it is twenty five percent booked.\n\n"
                    "User: How many vehicles aren't assigned?\n"
                    "You: I'll look up the available vehicles.\n"
                    "Tool result: Unassigned vehicles (4): KA-01-AB-1234 (Bus), KA-02-CD-5678 (Bus)...\n"
                    "You: I found four vehicles that are not currently assigned. They include bus K A dash zero one and bus K A dash zero two, among others.\n\n"
                    "User: List stops for Path-2.\n"
                    "Tool result: Path 'Path-2' stops: Peenya → Whitefield → Marathahalli → Indiranagar\n"
                    "You: Path two has four stops in sequence. It starts at Peenya, then goes to Whitefield, Marathahalli, and ends at Indiranagar.\n\n"
                    "Be a helpful assistant who reasons clearly and conveys information in speech-friendly language."
                )
            )
            
            # Get LLM response with tool calling
            response = llm_with_tools.invoke([system_message] + messages)
            
            print(f"✅ LLM Response: {response.content if response.content else 'Tool calls'}")
            if hasattr(response, 'tool_calls') and response.tool_calls:
                print(f"🔧 Tool calls: {[tc.get('name') for tc in response.tool_calls]}")
            
            return {"messages": [response]}
            
        except Exception as e:
            print(f"⚠️ OpenAI API Error: {e}")
            fallback = AIMessage(
                content="I ran into an issue reaching my language model, but I'm still here. "
                        "Please try again in a moment."
            )
            return {"messages": [fallback]}
    else:
        print("📝 Demo mode (no OpenAI API key). Responding with a simple acknowledgment.")
        fallback = AIMessage(
            content=f"I'm Movi on the {current_page} page. Please configure OPENAI_API_KEY for full functionality."
        )
        return {"messages": [fallback]}


# ============================================================================
# NODE 2: CALL_TOOL (Manual tool execution)
# ============================================================================

def call_tool(state: AgentState) -> AgentState:
    """
    Executes tools manually (not using ToolNode)
    This allows us to check consequences BEFORE execution
    """
    messages = state["messages"]
    
    if not messages:
        return state
    
    last_message = messages[-1]
    
    # Check if we have tool calls to execute
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return state
    
    tool_map = {t.name: t for t in get_all_tools()}
    tool_messages = []
    
    for tool_call in last_message.tool_calls:
        tool_name = tool_call.get("name")
        tool_args = tool_call.get("args", {})
        tool_id = tool_call.get("id", "")
        
        if tool_name in tool_map:
            try:
                result = tool_map[tool_name].invoke(tool_args)
                formatted_content = format_tool_output(tool_name, result)
                tool_messages.append(
                    ToolMessage(content=formatted_content, tool_call_id=tool_id)
                )
            except Exception as e:
                tool_messages.append(
                    ToolMessage(content=f"Error: {str(e)}", tool_call_id=tool_id)
                )
        else:
            tool_messages.append(
                ToolMessage(content=f"Error: Tool '{tool_name}' not found", tool_call_id=tool_id)
            )
    
    return {"messages": tool_messages}


# ============================================================================
# NODE 3: CHECK_CONSEQUENCES (THE KEY NODE - Tribal Knowledge)
# ============================================================================

def check_consequences(state: AgentState) -> AgentState:
    """
    THE CRITICAL NODE - Implements "Tribal Knowledge"
    
    This is a Python function (not LLM) that checks if the last tool call
    will have consequences. If so, it updates state to pause and ask for confirmation.
    
    This implements the exact flow from the assignment:
    1. Check the last tool call
    2. Query database for consequences
    3. If consequences found, set confirmation_pending = True
    4. Generate warning message
    5. Save action for later execution
    """
    messages = state["messages"]
    
    if not messages:
        return {"confirmation_pending": False}
    
    last_message = messages[-1]
    
    # Check if last message has tool calls
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return {"confirmation_pending": False}
    
    # Get the last tool call
    last_tool_call = last_message.tool_calls[0]
    tool_name = last_tool_call.get("name", "")
    tool_args = last_tool_call.get("args", {})
    
    # HIGH-RISK OPERATION 1: Remove Vehicle from Trip
    if tool_name == "remove_vehicle_from_trip":
        trip_name = tool_args.get("trip_name", "")
        
        # Query database for consequences
        status = db_utils.check_trip_has_bookings(trip_name)
        
        if status["has_bookings"]:
            # CONSEQUENCE FOUND! Generate warning message
            warning_msg = (
                f"⚠️ CONSEQUENCE WARNING\n\n"
                f"I can remove the vehicle from '{trip_name}'. However, please be aware that:\n\n"
                f"• This trip is currently {status['percentage']}% booked by employees\n"
                f"• Removing the vehicle will cancel these bookings\n"
                f"• Trip-sheet generation will fail\n"
                f"• Affected employees will need to be notified\n\n"
                f"This is a high-impact operation.\n\n"
                f"❓ Do you want to proceed? (Reply 'yes' to confirm or 'no' to cancel)"
            )
            
            # Return state with confirmation pending
            pause_message = ToolMessage(
                content="⏸️ Action paused pending confirmation. No changes made yet.",
                tool_call_id=last_tool_call.get("id", "")
            )

            return {
                "confirmation_pending": True,
                "action_to_confirm": last_tool_call,
                "consequence_info": {
                    "type": "vehicle_removal",
                    "trip_name": trip_name,
                    "booking_percentage": status["percentage"]
                },
                "messages": [pause_message, AIMessage(content=warning_msg)]
            }
    
    # HIGH-RISK OPERATION 2: Delete Daily Trip
    elif tool_name == "delete_daily_trip":
        trip_name = tool_args.get("trip_name", "")
        
        # Query database for consequences
        status = db_utils.check_trip_has_bookings(trip_name)
        
        if status["has_bookings"]:
            # CONSEQUENCE FOUND! Generate warning message
            warning_msg = (
                f"⚠️ CONSEQUENCE WARNING\n\n"
                f"I can delete the trip '{trip_name}'. However, please be aware that:\n\n"
                f"• This trip is currently {status['percentage']}% booked by employees\n"
                f"• Deleting this trip will permanently remove all bookings\n"
                f"• Assigned vehicle and driver will be freed up\n"
                f"• Affected employees will need to be notified and rescheduled\n"
                f"• This action cannot be undone\n\n"
                f"This is a high-impact operation.\n\n"
                f"❓ Do you want to proceed? (Reply 'yes' to confirm or 'no' to cancel)"
            )
            
            # Return state with confirmation pending
            pause_message = ToolMessage(
                content="⏸️ Action paused pending confirmation. No changes made yet.",
                tool_call_id=last_tool_call.get("id", "")
            )

            return {
                "confirmation_pending": True,
                "action_to_confirm": last_tool_call,
                "consequence_info": {
                    "type": "trip_deletion",
                    "trip_name": trip_name,
                    "booking_percentage": status["percentage"]
                },
                "messages": [pause_message, AIMessage(content=warning_msg)]
            }
    
    # HIGH-RISK OPERATION 3: Deactivate Route
    elif tool_name == "deactivate_route":
        route_name = tool_args.get("route_name", "")
        
        # Query database for consequences
        trip_info = db_utils.check_route_has_active_trips(route_name)
        
        if trip_info["has_trips"]:
            # CONSEQUENCE FOUND! Generate warning message
            warning_msg = (
                f"⚠️ CONSEQUENCE WARNING\n\n"
                f"I can deactivate route '{route_name}'. However, please be aware that:\n\n"
                f"• This route currently has {trip_info['count']} active trip(s)\n"
                f"• Deactivating will affect these trips\n"
                f"• New bookings will be disabled\n"
                f"• Existing schedules may need adjustment\n\n"
                f"This is a high-impact operation.\n\n"
                f"❓ Do you want to proceed? (Reply 'yes' to confirm or 'no' to cancel)"
            )
            
            pause_message = ToolMessage(
                content="⏸️ Action paused pending confirmation. No changes made yet.",
                tool_call_id=last_tool_call.get("id", "")
            )

            return {
                "confirmation_pending": True,
                "action_to_confirm": last_tool_call,
                "consequence_info": {
                    "type": "route_deactivation",
                    "route_name": route_name,
                    "active_trips": trip_info["count"]
                },
                "messages": [pause_message, AIMessage(content=warning_msg)]
            }
    
    # NO CONSEQUENCES FOUND - Proceed normally
    return {"confirmation_pending": False}


# ============================================================================
# NODE 4: HANDLE_CONFIRMATION
# ============================================================================

def handle_confirmation(state: AgentState) -> AgentState:
    """
    Handles user's yes/no confirmation response
    
    If user says "yes", executes the pending action
    If user says "no", cancels the action
    """
    messages = state["messages"]
    action_to_confirm = state.get("action_to_confirm")
    
    if not messages or not action_to_confirm:
        return {
            "confirmation_pending": False,
            "action_to_confirm": None
        }
    
    last_message = messages[-1]
    if not isinstance(last_message, HumanMessage):
        return state
    
    user_response = last_message.content.lower().strip()
    
    # User confirmed - execute the action
    if user_response in ["yes", "y", "confirm", "proceed", "ok", "sure"]:
        tool_name = action_to_confirm.get("name")
        tool_args = action_to_confirm.get("args", {})
        
        # Get the tool and execute it
        tool_map = {t.name: t for t in get_all_tools()}
        
        tool_call_id = action_to_confirm.get("id", "")
        messages_to_add: List[BaseMessage] = []

        if tool_name in tool_map:
            try:
                result = tool_map[tool_name].invoke(tool_args)
                tool_output = str(result)
                messages_to_add.append(
                    ToolMessage(content=tool_output, tool_call_id=tool_call_id)
                )
                messages_to_add.append(
                    AIMessage(content=f"✅ Action completed\n\n{tool_output}")
                )
            except Exception as e:
                error_text = str(e)
                messages_to_add.append(
                    ToolMessage(content=f"Error: {error_text}", tool_call_id=tool_call_id)
                )
                messages_to_add.append(
                    AIMessage(content=f"❌ Error executing action: {error_text}")
                )
        else:
            error_text = f"Tool '{tool_name}' not found"
            messages_to_add.append(
                ToolMessage(content=f"Error: {error_text}", tool_call_id=tool_call_id)
            )
            messages_to_add.append(
                AIMessage(content=f"❌ {error_text}")
            )
        
        return {
            "messages": messages_to_add,
            "confirmation_pending": False,
            "action_to_confirm": None,
            "consequence_info": None
        }
    
    # User cancelled
    elif user_response in ["no", "n", "cancel", "abort", "stop", "nope"]:
        response = AIMessage(
            content="✋ Action cancelled\n\nThe operation was not performed. How else can I help you?"
        )
        
        return {
            "messages": [response],
            "confirmation_pending": False,
            "action_to_confirm": None,
            "consequence_info": None
        }
    
    # Unclear response - ask again
    else:
        response = AIMessage(
            content="I didn't understand your response. Please reply with:\n"
                   "• 'yes' to proceed with the action\n"
                   "• 'no' to cancel"
        )
        return {"messages": [response]}


# ============================================================================
# ROUTING FUNCTIONS (Conditional Edges)
# ============================================================================

def should_continue_after_model(state: AgentState) -> Literal["check_consequences", "end"]:
    """
    Routing after call_model node
    
    If the LLM decided to use tools, route to check_consequences FIRST
    Otherwise, route to end
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    # If there are tool calls, check consequences first!
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "check_consequences"
    
    # Otherwise, end
    return "end"


def should_get_confirmation(state: AgentState) -> Literal["handle_confirmation", "tools"]:
    """
    Routing after check_consequences node
    
    If confirmation is pending, route to handle_confirmation
    Otherwise, safe to execute tools
    """
    if state.get("confirmation_pending"):
        return "handle_confirmation"
    return "tools"


def route_after_confirmation(state: AgentState) -> Literal["end"]:
    """
    Routing after handle_confirmation
    
    After handling confirmation, always end
    (The handle_confirmation node executes the action if yes, or cancels if no)
    """
    return "end"


def start_router(state: AgentState) -> Literal["handle_confirmation", "call_model"]:
    """
    Decide initial routing based on confirmation state.
    
    If we're awaiting confirmation and the latest message is from the user,
    go straight to handle_confirmation so we can resolve the request without
    invoking the LLM again.
    """
    if state.get("confirmation_pending"):
        messages = state.get("messages", [])
        if messages and isinstance(messages[-1], HumanMessage):
            return "handle_confirmation"
    return "call_model"


# ============================================================================
# GRAPH CONSTRUCTION
# ============================================================================

def create_movi_agent():
    """
    Creates the complete Movi agent graph with Tribal Knowledge
    
    Graph Flow (THE CRITICAL ARCHITECTURE):
    START → call_model → check_consequences → [has consequences?]
                                            → YES → handle_confirmation → END
                                            → NO → tools → END
    
    This is the "Tribal Knowledge" flow from the assignment!
    """
    # Create the state graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("call_model", call_model)
    workflow.add_node("check_consequences", check_consequences)
    workflow.add_node("tools", call_tool)
    workflow.add_node("handle_confirmation", handle_confirmation)
    
    # Set entry point with conditional routing
    workflow.add_conditional_edges(
        START,
        start_router,
        {
            "handle_confirmation": "handle_confirmation",
            "call_model": "call_model"
        }
    )
    
    # Conditional edge from call_model
    # Routes to check_consequences if tools needed, otherwise END
    workflow.add_conditional_edges(
        "call_model",
        should_continue_after_model,
        {
            "check_consequences": "check_consequences",
            "end": END
        }
    )
    
    # Conditional edge from check_consequences (THE KEY ROUTING!)
    # If consequences found, ask for confirmation
    # If safe, proceed to execute tools
    workflow.add_conditional_edges(
        "check_consequences",
        should_get_confirmation,
        {
            "handle_confirmation": "handle_confirmation",
            "tools": "tools"
        }
    )
    
    # After tools execute, end
    workflow.add_edge("tools", END)
    
    # After confirmation handling, end
    workflow.add_edge("handle_confirmation", END)
    
    # Compile the graph
    return workflow.compile()


# Create agent instance
movi_agent = create_movi_agent()


# ============================================================================
# INVOCATION FUNCTION
# ============================================================================

def invoke_agent(message: str, current_page: str = "unknown", image_data: bytes = None) -> str:
    """
    Invoke the Movi agent with a message
    
    Args:
        message: User's text message
        current_page: Current page context (busDashboard or manageRoute)
        image_data: Optional image bytes for vision processing (future)
    
    Returns:
        str: Agent's response
    """
    initial_state = {
        "messages": [HumanMessage(content=message)],
        "currentPage": current_page,
        "confirmation_pending": False,
        "action_to_confirm": None,
        "consequence_info": None,
        "image_data": image_data
    }
    
    try:
        result = movi_agent.invoke(initial_state)
        
        # Extract response from messages
        if result and "messages" in result:
            # Look for the last meaningful message
            for msg in reversed(result["messages"]):
                if isinstance(msg, AIMessage) and msg.content:
                    return msg.content
                elif isinstance(msg, ToolMessage):
                    # Tool execution result
                    return msg.content
        
        return "I processed your request."
        
    except Exception as e:
        import traceback
        print(f"Error in agent: {e}")
        print(traceback.format_exc())
        return f"I encountered an error: {str(e)}\n\nPlease try rephrasing your request."


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("🧠 Testing Movi Agent - Tribal Knowledge Graph")
    print("="*70)
    print()
    
    # Test 1: Simple query
    print("📝 Test 1: Simple Status Query")
    print("-" * 70)
    response = invoke_agent("What's the status of Bulk - 00:01?", "busDashboard")
    print(f"User: What's the status of Bulk - 00:01?")
    print(f"Movi: {response}")
    print()
    
    # Test 2: Unassigned vehicles
    print("📝 Test 2: Unassigned Vehicles")
    print("-" * 70)
    response = invoke_agent("How many vehicles are not assigned?", "busDashboard")
    print(f"User: How many vehicles are not assigned?")
    print(f"Movi: {response}")
    print()
    
    # Test 3: HIGH CONSEQUENCE - This should trigger the warning
    print("📝 Test 3: HIGH CONSEQUENCE - Remove Vehicle from Booked Trip")
    print("-" * 70)
    response = invoke_agent("Remove the vehicle from Bulk - 00:01", "busDashboard")
    print(f"User: Remove the vehicle from Bulk - 00:01")
    print(f"Movi: {response}")
    print()
    print("⚠️  This should show the consequence warning!")
    print()
    
    # Test 4: Path stops
    print("📝 Test 4: List Stops for Path")
    print("-" * 70)
    response = invoke_agent("List all stops for Path-2", "manageRoute")
    print(f"User: List all stops for Path-2")
    print(f"Movi: {response}")
    print()
    
    print("="*70)
    print("✅ Tribal Knowledge Graph Testing Complete!")
    print("="*70)
    print()
    print("📊 Graph Architecture:")
    print("   START → call_model → tools → check_consequences → handle_confirmation → END")
    print()
    print("🔥 Key Features:")
    print("   ✅ LLM with tool binding (call_model)")
    print("   ✅ ToolNode execution (tools)")
    print("   ✅ Consequence checking (check_consequences)")
    print("   ✅ Confirmation flow (handle_confirmation)")
    print("   ✅ Conditional routing (smart edges)")
    print()
