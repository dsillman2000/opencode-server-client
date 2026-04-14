"""Sampler strategies for prompts and models."""

import random
from typing import Callable

from .types import ModelSampler, PromptSampler


def constant_sampler(value: str) -> Callable[[int], str]:
    """Return the same value for all sessions.
    
    Args:
        value: The constant value to return
        
    Returns:
        Sampler function that ignores session index
    """
    return lambda _: value


def from_list_sampler(values: list[str]) -> Callable[[int], str]:
    """Cycle through a list of values by session index.
    
    Args:
        values: List of values to cycle through
        
    Returns:
        Sampler function that cycles through list based on index
    """
    if not values:
        raise ValueError("Values list cannot be empty")
    return lambda idx: values[idx % len(values)]


def random_sampler(values: list[str]) -> Callable[[int], str]:
    """Randomly select from a list of values.
    
    Args:
        values: List of values to choose from
        
    Returns:
        Sampler function that randomly selects from list
    """
    if not values:
        raise ValueError("Values list cannot be empty")
    return lambda _: random.choice(values)


def index_based_sampler(func: Callable[[int], str]) -> Callable[[int], str]:
    """Use a custom function based on session index.
    
    Args:
        func: Function that takes session index and returns value
        
    Returns:
        The passed function (for convenience)
    """
    return func
