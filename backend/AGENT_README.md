# Movi Agent – Backend Reference

This document describes the LangGraph agent that powers Movi’s multimodal transport assistant.  
Status: **feature-complete for the assignment brief** (16 tools, tribal knowledge flow, voice + vision support).

---

## 1. Architecture Snapshot

```
User Input (text / voice / image + currentPage)
        │
        ▼
call_model (LLM with tool binding)
        │
        ├─ if high‑risk → check_consequences → handle_confirmation
        └─ otherwise     → call_tool
        │
        ▼
Tool output formatted for speech → response returned to FastAPI
```

Key design choices:

- **Stateful**: `AgentState` tracks `messages`, `currentPage`, pending confirmations, consequence metadata, and optional `image_data`.
- **Two-pass safety**: high-risk tools are intercepted by `check_consequences`; execution only resumes after an explicit “yes.”
- **Human-friendly speech**: all tool outputs are rewritten (license plates spaced, numbers preserved) before the LLM speaks.
- **Multimodal aware**: screenshots are summarized by GPT‑4o Vision and injected as system context.

---

## 2. Tools (16 total)

| Category | Tool | Notes | Typical Prompt |
|----------|------|-------|----------------|
| Read – Dynamic | `get_trip_status` | Status, booking %, vehicle, driver | “Status of Bulk - 00:01” |
| | `get_unassigned_vehicles` | Free vehicles list | “Which vehicles are available?” |
| | `get_trip_bookings` | Booking percentage | “How booked is Bulk - 00:01?” |
| Read – Static | `list_stops_for_path` | Ordered stops | “List stops on Path-2” |
| | `list_routes_for_path` | Routes using a path | “Routes that use Path-1” |
| | `list_all_routes` | Optional status filter | “Show active routes” |
| Create – Dynamic | `create_daily_trip` | Adds trip for a route | “Create a morning trip on Path-1” |
| | `assign_vehicle_and_driver` | Deployment | “Assign KA-03-EF-9012 and Suresh” |
| Delete – Dynamic | `delete_daily_trip` ⚠️ | Removes trip + deployment | “Delete Tech-Park Morning” |
| | `remove_vehicle_from_trip`⚠️ | Unassign vehicle | “Remove vehicle from Bulk - 00:01” |
| Create – Static | `create_new_stop` | Adds stop to catalog | “Add stop Odeon Circle” |
| | `create_new_path` | Path from stops | “Create path Tech-Loop with …” |
| | `create_new_route` | Route for path/time | “Route Path-2 at 19:45 Outbound” |
| Update – Static | `deactivate_route` ⚠️ | Deactivates route | “Deactivate Path-1 - 07:00” |
| Additional | `get_all_drivers` | Optional assigned-only filter | “List available drivers” |
| | `get_vehicle_details` | Type, capacity, assignment | “Details for KA-05-GH-3456” |

⚠️ Tools flagged high-risk are guarded by the consequence workflow.

---

## 3. Consequence & Confirmation Flow

1. **Detection** – `check_consequences` inspects the most recent tool call.  
   - Trips with bookings → warning before removing vehicle / deleting trip  
   - Routes with active trips → warning before deactivation

2. **Warning message** (speech-friendly, no markdown):
   ```
   ⚠️ CONSEQUENCE WARNING
   I can remove the vehicle from Bulk - 00:01. However:
   • This trip is currently 25% booked by employees
   • Removing the vehicle will cancel these bookings
   • Trip-sheet generation will fail
   • Affected employees will need to be notified
   
   ❓ Do you want to proceed? (Reply 'yes' to confirm or 'no' to cancel)
   ```

3. **Confirmation** – `handle_confirmation` waits for “yes” / “no”.  
   - “yes” → action executed, success message spoken  
   - “no”  → operation cancelled

---

## 4. Multimodal & Audio Handling

- **Screenshots**: `process_image_with_vision` (GPT‑4o) extracts highlighted trip/route info and appends it as a system message so the LLM can act on “remove this one.”
- **Speech-to-Text**: Deepgram REST API (`/api/speech-to-text`). `numerals=true` keeps trip names like “Test-1” intact.
- **Text-to-Speech**: ElevenLabs REST API (`/api/text-to-speech`). Voice output separates characters (“K A dash zero three …”) for clarity.
- **LLM Prompting**: system prompt reinforces conversational tone, numeric fidelity, and speech pacing.

---

## 5. Testing & Verification

- **Manual flows**: documented in `TESTING_GUIDE.md`. Covers happy paths, high-risk confirmations, and voice/image scenarios.
- **Automated tests**: pytest suite for individual tools is planned but not yet merged (see root README section 6).
- **Seed data**: `seed.py` ensures deterministic results for every tool (e.g., “Bulk - 00:01” is always 25% booked with KA-01-AB-1234 assigned).

---

## 6. Known Gaps

| Area | Status | Rationale |
|------|--------|-----------|
| Tool-level pytest coverage | Pending | Manual testing complete; automated assertions queued next |
| Performance profiling | Not executed | Dataset is small; baseline acceptable for assignment |
| Additional consequence rules | Scoped out | Booking and active-trip checks satisfy brief; extra rules would be speculative |

---

## 7. Quick Reference (Code Snippets)

```python
# Invoking the agent from FastAPI (main.py)
    agent_response = invoke_agent(
        message=message,
        current_page=currentPage,
    image_data=image_bytes
)
```

```python
# Formatting tool output for TTS (agent.py)
result = tool.invoke(args)
formatted = format_tool_output(tool_name, result)
messages.append(ToolMessage(content=formatted, tool_call_id=tool_id))
```

```python
# Example: deleting a trip with confirmation
> User: Delete the trip Tech-Park Morning
< Movi: Warning... trip is 80% booked... proceed?
> User: yes
< Movi: ✅ Action completed. Deleted daily trip Tech-Park Morning [had 80% bookings].
```

---

## 8. Table of Implemented Requirements

| Requirement | Delivered |
|-------------|-----------|
| 10+ tools across read/create/update/delete | **16 tools** implemented |
| Tribal knowledge consequence flow | Fully functional with confirmation |
| Agent state with context + confirmations | `AgentState` covers all flags |
| Vision integration | GPT‑4o processes screenshots |
| Voice input & output | Deepgram STT + ElevenLabs TTS |
| Frontend context awareness | `currentPage` passed through chat |

---

## 9. Summary

- The Movi agent now mirrors the assignment’s operational expectations end-to-end.  
- Speech and vision inputs are first-class citizens—no markup artifacts reach TTS.  
- Only outstanding backlog items are automated tool tests and any production-grade hardening (auth, rate limiting, etc.).

Refer to `AUDIO_INTEGRATION_COMPLETE.md` for deeper audio notes and the root `README.md` for full-stack instructions.

