"""
Entry point for `python -m overlap.web` — runs the web app standalone.

Same reasoning as overlap/__main__.py: a package needs this file to be
executed directly with `python -m`.
"""
from overlap.web.server import run_server

run_server()
