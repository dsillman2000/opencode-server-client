import json

from opencode_server_client import RetryConfig, ServerConfig, SyncHttpClient

if __name__ == "__main__":
    config = ServerConfig(base_url="http://localhost:9000", basic_auth=("opencode", "***REMOVED***"))
    retry = RetryConfig(max_retries=3)
    with SyncHttpClient(config, retry) as client:
        response = client.get("/session")
        print(json.dumps(response.json(), indent=2))
