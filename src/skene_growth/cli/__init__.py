"""
Command-line interface for skene-growth.

Usage with uvx (recommended):
    uvx skene-growth analyze .
    uvx skene-growth plan
    uvx skene-growth chat .
    uvx skene-growth validate ./growth-manifest.json

Usage with pip install:
    skene-growth analyze .
    skene-growth plan
    skene-growth chat .
    skene-growth validate ./growth-manifest.json
"""

from skene_growth.cli.main import app

__all__ = ["app"]
