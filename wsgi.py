"""
PythonAnywhere WSGI entry point.

In your PythonAnywhere Web tab set:
  Source code:   /home/<username>/<project-folder>
  Working dir:   /home/<username>/<project-folder>
  WSGI file:     /home/<username>/<project-folder>/wsgi.py
  Python ver:    3.11
"""
import sys
import os

# Add the project directory to sys.path so imports resolve correctly.
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

from app import app as application  # noqa: F401
