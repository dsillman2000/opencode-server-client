import json

from opencode_server_client import (
    OpencodeServerClient,
    RetryConfig,
    ServerConfig,
    SyncHttpClient,
)

if __name__ == "__main__":
    config = ServerConfig(base_url="http://localhost:9000", basic_auth=("opencode", "***REMOVED***"))
    retry = RetryConfig(max_retries=3)

    client = OpencodeServerClient(config, retry, "/home/dsillman2000/python-projects/opencode-server-client")
    sessions = client.list_all_sessions()

    print(json.dumps(sessions, indent=2))
