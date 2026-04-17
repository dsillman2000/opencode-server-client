import datetime
import json
import os
import uuid
from pathlib import Path
from time import sleep
from typing import Optional, TypedDict

from opencode_server_client import (
    AnyEvent,
    OpencodeServerClient,
    RetryConfig,
    ServerConfig,
)
from opencode_server_client.identifiers import generate_session_id

MessageState = TypedDict(
    "MessageState", {"messageID": str, "content": Optional[str], "finished": bool, "updated_at": datetime.datetime}
)

SESSION_COMPLETED = False
SESSION_MESSAGES = dict()
SESSION_TOOL_CALLS = dict()
SESSION_FILE = "/tmp/session-state.log"


def dump_event(event: AnyEvent):
    if event.__class__.__name__ not in {
        "MessageUpdatedEvent",
        "MessagePartUpdatedEvent",
        "SessionStatusEvent",
    }:
        return
    timestamp = event.timestamp.isoformat()
    with open(SESSION_FILE, "a") as f:
        event_json = json.dumps(event.__dict__, default=str)
        f.write(f"{timestamp}\t{event.__class__.__name__}\t{event_json}\n")


def handle_oc_event(event: AnyEvent):
    global SESSION_TOOL_CALLS, SESSION_MESSAGES
    match event.__class__.__name__:
        case "SessionIdleEvent":
            SESSION_IDLE = True
        case "MessageUpdatedEvent":
            if event.message_id not in SESSION_MESSAGES:
                SESSION_MESSAGES[event.message_id] = MessageState(
                    messageID=event.message_id, content=None, finished=False, updated_at=event.timestamp
                )
        case "MessagePartUpdatedEvent":
            part_type = event.part.get("type")
            if part_type == "step-finish":
                if event.message_id in SESSION_MESSAGES:
                    SESSION_MESSAGES[event.message_id]["finished"] = True
                    SESSION_MESSAGES[event.message_id]["updated_at"] = event.timestamp
            elif part_type == "text":
                if event.message_id in SESSION_MESSAGES:
                    current_content = SESSION_MESSAGES[event.message_id]["content"] or ""
                    SESSION_MESSAGES[event.message_id]["content"] = current_content + (event.part.get("text") or "")
                    SESSION_MESSAGES[event.message_id]["updated_at"] = event.timestamp
            elif part_type == "tool":
                tool = event.part.get("tool")
                call_id = event.part.get("callID")
                tool_state = event.part.get("state", {})
                if event.message_id in SESSION_MESSAGES:
                    if event.message_id not in SESSION_TOOL_CALLS:
                        SESSION_TOOL_CALLS[event.message_id] = {}
                    SESSION_TOOL_CALLS[event.message_id][call_id] = {"tool": tool, "state": tool_state}
            if event.message_id not in SESSION_MESSAGES:
                SESSION_MESSAGES[event.message_id] = MessageState(
                    messageID=event.message_id, content=None, finished=False, updated_at=event.timestamp
                )
        case "SessionStatusEvent":
            SESSION_IDLE = event.status == "idle"
        case _:
            return


def mark_completed(_):
    global SESSION_COMPLETED
    SESSION_COMPLETED = True


if __name__ == "__main__":
    opencode_user = "opencode"
    opencode_pass = os.getenv("OPENCODE_PASSWORD", "password")
    config = ServerConfig(base_url="http://localhost:9000", basic_auth=(opencode_user, opencode_pass))
    retry = RetryConfig(max_retries=3)

    client = OpencodeServerClient(config, retry, "/home/dsillman2000/python-projects/opencode-server-client")
    Path(SESSION_FILE).write_text("")  # Clear previous session log
    # Subscribe to events
    client.events.subscribe(on_event=dump_event, on_idle=mark_completed, on_error=mark_completed)

    # Create a session and submit the prompt
    uid = str(uuid.uuid4())[:8]
    session = client.create_session(title=f"sun-mass (temp {uid})")
    client.update_session(session["id"], title=f"sun-mass ({session['id']})")

    sun_prompt = """
What is the mass of the sun? You must search the web to find the answer, and return the answer in the following JSON format:

    {
        "sun_mass_kg_int": 123,
        "sun_mass_kg_scientific": "1.2e3",
        "source_url": "https://example.com"
    }

Return your answer with no additional text or explanation, just the JSON. You must use the web search tool to find the answer, you cannot rely on any internal knowledge.
    """.strip()
    message_id = client.prompts.submit_prompt(
        session_id=session["id"],
        text=sun_prompt,
        agent="build",
        provider_id="deepseek",
        model_id="deepseek-chat",
    )

    while not SESSION_COMPLETED:
        sleep(1)

    print("Session is idle, final session log:")
    print(Path(SESSION_FILE).read_text())
