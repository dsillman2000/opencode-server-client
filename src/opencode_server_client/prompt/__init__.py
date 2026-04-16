"""Prompt submission for sending prompts to OpenCode sessions.

This module provides:
- PromptSubmitter: Submit prompts to sessions (sync)
- (Future) AsyncPromptSubmitter: Submit prompts to sessions (async)

Typical usage:
    >>> from opencode_server_client.prompt import PromptSubmitter
    >>> submitter = PromptSubmitter(http_client)
    >>> result = submitter.submit_prompt(session_id="abc", text="Hello")
"""

from opencode_server_client.prompt.sync_submitter import PromptSubmitter

__all__ = ["PromptSubmitter"]
