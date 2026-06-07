"""Antenna MVP — automatic daily discovery brief from public feeds.

Purpose: surface things worth paying attention to across AI, Robotics, Space,
China, and Macro. This is *not* investment advice and does not recommend stocks.

Brutally simple by design: fetch RSS -> select/summarise -> write one Markdown
brief. No frameworks, no database, no server.
"""

__version__ = "0.1.0"

THEMES = ("ai", "robotics", "space", "china", "macro")
