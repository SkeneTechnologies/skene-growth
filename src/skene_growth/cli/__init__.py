"""
Command-line interface for skene-growth.

Usage with uvx (recommended):
    uvx skene-growth analyze .
    uvx skene-growth generate
    uvx skene-growth inject --csv loops.csv
    uvx skene-growth validate ./growth-manifest.json

Usage with pip install:
    skene-growth analyze .
    skene-growth generate
    skene-growth inject --csv loops.csv
    skene-growth validate ./growth-manifest.json
"""

from skene_growth.cli.main import app

__all__ = ["app"]
