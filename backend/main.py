"""
FastAPI server for Movi Transport Management System
Provides API endpoints for the frontend and integrates with the langgraph agent
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
from datetime import datetime, timedelta
from langchain_core.messages import HumanMessage
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our agent (the custom graph implementation is correct for our use case!)
from agent import invoke_agent, movi_agent

# Import database for future use
from database import get_session, Stop, Path, Route, Vehicle, Driver, DailyTrip, Deployment

# API Keys for audio services
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# ============================================================================
# SESSION MANAGEMENT FOR STATEFUL CONVERSATIONS
# ============================================================================

# In-memory session storage (use Redis/DB in production)
# NOTE: This is a MODULE-LEVEL variable that persists across requests
# but is cleared on server restart
session_states: Dict[str, Dict[str, Any]] = {}
SESSION_TIMEOUT = 3600  # 1 hour

print("=" * 70)
print("🚀 Backend Module Loaded - Session Storage Initialized")
print("=" * 70)

# Request counter to track server continuity
request_counter = 0

def get_session_id_from_page(current_page: str) -> str:
    """Generate a simple session ID based on page (in real app, use cookies/JWT)"""
    return f"session_{current_page}"

def get_or_create_session(session_id: str, current_page: str) -> Dict[str, Any]:
    """Get existing session state or create new one"""
    if session_id not in session_states:
        session_states[session_id] = {
            "messages": [],
            "currentPage": current_page,
            "confirmation_pending": False,
            "action_to_confirm": None,
            "consequence_info": None,
            "image_data": None,
            "last_access": datetime.now()
        }
    else:
        # Update last access time
        session_states[session_id]["last_access"] = datetime.now()
    
    return session_states[session_id]

def cleanup_old_sessions():
    """Remove sessions older than timeout"""
    current_time = datetime.now()
    expired = []
    for sid, state in list(session_states.items()):
        # Handle old sessions that might not have last_access
        last_access = state.get("last_access")
        if last_access is None:
            # Old session without timestamp - mark for cleanup
            print(f"⚠️  Cleaning up old session without timestamp: {sid}")
            expired.append(sid)
        else:
            age_seconds = (current_time - last_access).total_seconds()
            if age_seconds > SESSION_TIMEOUT:
                print(f"⚠️  Cleaning up expired session: {sid} (age: {age_seconds}s)")
                expired.append(sid)
    
    for sid in expired:
        del session_states[sid]
    
    if expired:
        print(f"🧹 Cleaned up {len(expired)} expired sessions")


# Initialize FastAPI app
app = FastAPI(
    title="Movi Transport API",
    description="API for Movi AI Assistant - Multimodal Transport Management",
    version="1.0.0"
)

# Configure CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default dev server
        "http://localhost:3000",  # Alternative React port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class ChatRequest(BaseModel):
    message: str
    currentPage: str = "unknown"


class ChatResponse(BaseModel):
    response: str
    success: bool = True
    error: Optional[str] = None


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "Movi Transport API",
        "version": "2.0.0",
        "agent": "Full Movi Agent with 14 Tools",
        "features": [
            "13+ Database Tools",
            "Consequence Checking",
            "Confirmation Flow",
            "Context Awareness"
        ]
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(
    message: str = Form(...),
    currentPage: str = Form(default="unknown"),
    image: Optional[UploadFile] = File(default=None)
):
    """
    Main chat endpoint for Movi AI assistant with SESSION MANAGEMENT
    
    Args:
        message: User's text message
        currentPage: Current page context (busDashboard or manageRoute)
        image: Optional image file upload
    
    Returns:
        ChatResponse with agent's response
    """
    global request_counter
    request_counter += 1
    
    try:
        # Handle image if provided
        image_data = None
        if image:
            image_data = await image.read()
            print(f"📷 Received image: {image.filename} ({len(image_data)} bytes)")
        
        print(f"\n{'='*70}")
        print(f"💬 Chat Request #{request_counter}")
        print(f"{'='*70}")
        print(f"   Message: {message}")
        print(f"   Page: {currentPage}")
        print(f"   Has Image: {image is not None}")
        
        # Clean up old sessions periodically
        cleanup_old_sessions()
        
        # Get or create session for this page
        session_id = get_session_id_from_page(currentPage)
        print(f"🔑 Session ID: {session_id}")
        print(f"📦 Existing sessions: {list(session_states.keys())}")
        
        session_state = get_or_create_session(session_id, currentPage)
        
        print(f"📊 Loaded Session State (BEFORE adding new message):")
        print(f"   Confirmation Pending: {session_state.get('confirmation_pending', False)}")
        print(f"   Action to Confirm: {session_state.get('action_to_confirm', 'None')}")
        print(f"   Messages in History: {len(session_state['messages'])}")
        
        # Add new message to session
        session_state["messages"].append(HumanMessage(content=message))
        session_state["currentPage"] = currentPage
        
        if image_data:
            session_state["image_data"] = image_data
        
        print(f"📊 Session State (AFTER adding new message):")
        print(f"   Messages in History: {len(session_state['messages'])}")
        
        # Invoke the agent with session state
        result = movi_agent.invoke(session_state)
        
        # Update session with result and timestamp
        result["last_access"] = datetime.now()
        session_states[session_id] = result
        
        print(f"💾 Saved Session State:")
        print(f"   Session ID: {session_id}")
        print(f"   Confirmation Pending: {result.get('confirmation_pending', False)}")
        action = result.get('action_to_confirm')
        if action:
            print(f"   Action to Confirm: {str(action)[:100]}...")
        else:
            print(f"   Action to Confirm: None")
        print(f"   Total Messages: {len(result.get('messages', []))}")
        print(f"   Sessions in Memory: {list(session_states.keys())}")
        
        # Extract response
        messages = result.get("messages", [])
        agent_response = "I processed your request."
        
        for msg in reversed(messages):
            if hasattr(msg, 'content') and msg.content and not isinstance(msg, HumanMessage):
                agent_response = msg.content
                break
        
        print(f"🤖 Agent Response: {agent_response[:100]}...")
        
        return ChatResponse(
            response=agent_response,
            success=True
        )
        
    except Exception as e:
        print(f"❌ Error in chat endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return ChatResponse(
            response="I apologize, but I encountered an error processing your request.",
            success=False,
            error=str(e)
        )


# =============================================================================
# AUDIO ENDPOINTS (Speech-to-Text and Text-to-Speech)
# =============================================================================

@app.post("/api/speech-to-text")
async def speech_to_text(audio: UploadFile = File(...)):
    """
    Transcribe audio to text using Deepgram
    
    Args:
        audio: Audio file (webm, mp3, wav, etc.)
    
    Returns:
        JSON with transcript
    """
    if not DEEPGRAM_API_KEY:
        raise HTTPException(status_code=500, detail="Deepgram API key not configured")
    
    try:
        # Read audio file
        audio_data = await audio.read()

        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": audio.content_type or "audio/webm",
        }

        params = {
            "model": "nova-2",
            "smart_format": "true",
            "language": "en-US",
            "punctuate": "true",
            "numerals": "true",
        }

        response = requests.post(
            "https://api.deepgram.com/v1/listen",
            params=params,
            headers=headers,
            data=audio_data,
            timeout=30,
        )
        response.raise_for_status()

        result = response.json()
        transcript = result["results"]["channels"][0]["alternatives"][0]["transcript"]

        print(f"🎤 Transcribed: {transcript}")

        return {"transcript": transcript, "success": True}

    except Exception as e:
        print(f"❌ STT Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error transcribing audio: {str(e)}")


@app.post("/api/text-to-speech")
async def text_to_speech(request: dict):
    """
    Convert text to speech using ElevenLabs
    
    Args:
        request: JSON with "text" field
    
    Returns:
        Audio file (MP3)
    """
    if not ELEVENLABS_API_KEY:
        raise HTTPException(status_code=500, detail="ElevenLabs API key not configured")
    
    try:
        text = request.get("text", "")
        if not text:
            raise HTTPException(status_code=400, detail="No text provided")

        print(f"🔊 Generating speech for: {text[:100]}...")

        voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }

        payload = {
            "text": text,
            "model_id": "eleven_turbo_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True,
            },
        }

        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()

        audio_bytes = response.content

        print(f"✅ TTS generated successfully ({len(audio_bytes)} bytes)")

        return Response(content=audio_bytes, media_type="audio/mpeg")

    except Exception as e:
        print(f"❌ TTS Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating speech: {str(e)}")


# =============================================================================
# DATABASE ENDPOINTS (for frontend data fetching)
# =============================================================================

@app.get("/api/stops")
async def get_stops():
    """Get all stops"""
    try:
        session = get_session()
        stops = session.query(Stop).all()
        result = [
            {
                "stop_id": s.stop_id,
                "name": s.name,
                "latitude": s.latitude,
                "longitude": s.longitude
            }
            for s in stops
        ]
        session.close()
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/paths")
async def get_paths():
    """Get all paths"""
    try:
        session = get_session()
        paths = session.query(Path).all()
        result = [
            {
                "path_id": p.path_id,
                "path_name": p.path_name,
                "ordered_list_of_stop_ids": p.ordered_list_of_stop_ids
            }
            for p in paths
        ]
        session.close()
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/routes")
async def get_routes():
    """Get all routes"""
    try:
        session = get_session()
        routes = session.query(Route).all()
        result = [
            {
                "route_id": r.route_id,
                "path_id": r.path_id,
                "route_display_name": r.route_display_name,
                "shift_time": r.shift_time,
                "direction": r.direction,
                "start_point": r.start_point,
                "end_point": r.end_point,
                "status": r.status
            }
            for r in routes
        ]
        session.close()
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/vehicles")
async def get_vehicles():
    """Get all vehicles"""
    try:
        session = get_session()
        vehicles = session.query(Vehicle).all()
        result = [
            {
                "vehicle_id": v.vehicle_id,
                "license_plate": v.license_plate,
                "type": v.type,
                "capacity": v.capacity
            }
            for v in vehicles
        ]
        session.close()
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/drivers")
async def get_drivers():
    """Get all drivers"""
    try:
        session = get_session()
        drivers = session.query(Driver).all()
        result = [
            {
                "driver_id": d.driver_id,
                "name": d.name,
                "phone_number": d.phone_number
            }
            for d in drivers
        ]
        session.close()
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trips")
async def get_trips():
    """Get all daily trips with deployment info"""
    try:
        session = get_session()
        trips = session.query(DailyTrip).all()
        result = []
        
        for trip in trips:
            # Get deployment info
            deployment = session.query(Deployment).filter_by(trip_id=trip.trip_id).first()
            
            vehicle_info = None
            driver_info = None
            
            if deployment:
                if deployment.vehicle_id:
                    vehicle = session.query(Vehicle).filter_by(vehicle_id=deployment.vehicle_id).first()
                    if vehicle:
                        vehicle_info = {
                            "vehicle_id": vehicle.vehicle_id,
                            "license_plate": vehicle.license_plate,
                            "type": vehicle.type
                        }
                
                if deployment.driver_id:
                    driver = session.query(Driver).filter_by(driver_id=deployment.driver_id).first()
                    if driver:
                        driver_info = {
                            "driver_id": driver.driver_id,
                            "name": driver.name,
                            "phone_number": driver.phone_number
                        }
            
            result.append({
                "trip_id": trip.trip_id,
                "route_id": trip.route_id,
                "display_name": trip.display_name,
                "booking_status_percentage": trip.booking_status_percentage,
                "live_status": trip.live_status,
                "vehicle": vehicle_info,
                "driver": driver_info
            })
        
        session.close()
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# SERVER STARTUP
# =============================================================================

if __name__ == "__main__":
    print("="*70)
    print("🚀 Starting Movi Transport API Server")
    print("="*70)
    print(f"📍 Server: http://localhost:8000")
    print(f"📚 Docs: http://localhost:8000/docs")
    print(f"🤖 Agent: Movi")
    print("="*70)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

