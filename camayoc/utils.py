# coding=utf-8
"""Utility functions."""
import uuid


def uuid4():
    """Return a random UUID, as a unicode string."""
    return str(uuid.uuid4())
