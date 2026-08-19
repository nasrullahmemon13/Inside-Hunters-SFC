import os
import sys

# Add the repo root to sys.path so Flask can find app.py, models/, services/, templates/
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app

# Vercel looks for an object named 'app' or 'handler' in this file.
# Exporting 'app' is enough for @vercel/python to serve the Flask WSGI app.
