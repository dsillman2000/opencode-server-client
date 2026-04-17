import os
import uuid
from time import sleep

from opencode_server_client import (
    AnyEvent,
    OpencodeServerClient,
    RetryConfig,
    ServerConfig,
)


def handle_oc_event(event: AnyEvent):
    # print(f"Received event: {event}")
    match event.__class__.__name__:
        case "SessionIdleEvent":
            print(f"Session {event.session_id} is now idle")
        case "MessageUpdatedEvent":
            print(f"Message {event.message_id} was updated with new content")
        case "SessionStatusEvent":
            print(f"Session {event.session_id} status changed to {event.status}")
        case _:
            return


if __name__ == "__main__":
    opencode_user = "opencode"
    opencode_pass = os.getenv("OPENCODE_PASSWORD", "password")
    config = ServerConfig(base_url="http://localhost:9000", basic_auth=(opencode_user, opencode_pass))
    retry = RetryConfig(max_retries=3)

    client = OpencodeServerClient(config, retry, "/home/dsillman2000/python-projects/opencode-server-client")

    # Find the deepseek provider and deepseek-chat model
    deepseek_provider = client.providers.get_provider("deepseek")
    if deepseek_provider is None:
        print("Error: deepseek provider not found")
        # List available providers for debugging
        providers = client.providers.list_providers(connected_only=True)
        print(f"Available providers: {[p.id for p in providers]}")
        exit(1)

    deepseek_chat_model = deepseek_provider.get_model("deepseek-chat")
    if deepseek_chat_model is None:
        print("Error: deepseek-chat model not found in deepseek provider")
        # List available models in the provider
        print(f"Available models: {list(deepseek_provider.models.keys())}")
        exit(1)

    print(f"Found provider: {deepseek_provider.id}")
    print(f"Found model: {deepseek_chat_model.id}")
    print(f"Model capabilities - Text I/O: {deepseek_chat_model.capabilities.has_text_io()}")
    print(f"Model capabilities - Toolcall: {deepseek_chat_model.capabilities.has_toolcall()}")

    # Subscribe to events
    client.events.subscribe(on_event=handle_oc_event)

    # Create a session and submit the prompt
    uid = str(uuid.uuid4())[:8]
    session = client.create_session(title=f"sun-mass (temp {uid})")
    print(f"Created session: {session['id']}")

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
    print(f"Submitted prompt with message_id: {message_id}")

    while True:
        sleep(1)
