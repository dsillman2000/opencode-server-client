import os
from time import sleep

from opencode_server_client import OpencodeServerClient, RetryConfig, ServerConfig

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
    client.events.subscribe(
        on_event=lambda e: print(f"Received event: {e}"),
    )

    # Create a session and submit the prompt
    session = client.create_session()
    print(f"Created session: {session['id']}")

    message_id = client.prompts.submit_prompt(
        session_id=session["id"],
        text="What is the mass of the sun?",
        agent="build",
        provider_id="deepseek",
        model_id="deepseek-chat",
    )
    print(f"Submitted prompt with message_id: {message_id}")

    while True:
        sleep(1)
