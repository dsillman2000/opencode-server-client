# opencode-server-client

An unofficial, SSE-first client for interacting with an Opencode server. See the official Opencode AI SDK
([Python](https://github.com/anomalyco/opencode-sdk-python), [TypeScript](https://github.com/anomalyco/opencode-sdk-js))
for an official client implementation.

Type definitions for SSE events are available in the official Opencode server implementation:

- [anomalyco/opencode](https://github.com/anomalyco/opencode/blob/dev/packages/sdk/js/src/gen/core/types.gen.ts)

## Installation

_Once this client implementation is published to PyPI, you can install it with pip or your package manager of choice._

```bash
# pip installation
pip install opencode-server-client
# poetry installation
poetry add opencode-server-client
# uv installation
uv add opencode-server-client
```

## Quick start

Assuming you have an Opencode server up and running on port 9000, you can use the client like this:

**Synchronous pattern**

```python
from opencode_server_client import OpencodeServerClient, ServerConfig

server = ServerConfig(base_url="http://<user>:<password>@localhost:9000")
client = OpencodeServerClient(server_config=server)
session = client.create_session(
    directory="/path/to/my/project",
    title="My chat"
)
client.submit_prompt_and_wait(
    session["id"],
    text="What is Opencode?",
)
```

## Acknowledgements

Authors:

- David Sillman <dsillman2000@gmail.com>
