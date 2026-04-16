import json
from time import sleep

from opencode_server_client import OpencodeServerClient, RetryConfig, ServerConfig

if __name__ == "__main__":
    config = ServerConfig(base_url="http://localhost:9000", basic_auth=("opencode", "password"))
    retry = RetryConfig(max_retries=3)

    client = OpencodeServerClient(config, retry, "/home/dsillman2000/python-projects/opencode-server-client")
    client.events.subscribe(
        on_event=lambda e: print(f"Received event: {e}"),
    )
    sessions = client.list_all_sessions()
    session = client.create_session()
    message_id = client.prompts.submit_prompt(
        session_id=session["id"],
        text="What is the mass of the sun?",
        agent="build",
        provider_id="nvidia",
        model_id="z-ai/glm5",
    )
    while True:
        sleep(1)
