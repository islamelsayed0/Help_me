#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import json
from datetime import datetime

# #region agent log
def log_debug(location, message, data=None, hypothesis_id=None):
    try:
        log_entry = {
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": hypothesis_id or "A",
            "location": location,
            "message": message,
            "data": data or {},
            "timestamp": int(datetime.now().timestamp() * 1000)
        }
        with open("/Users/islamelsayed/Documents/Help Me /.cursor/debug.log", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass
# #endregion

def main():
    """Run administrative tasks."""
    # #region agent log
    log_debug("manage.py:main", "Starting Django management command", {"argv": sys.argv}, "A")
    # #endregion
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'helpme_hub.settings')
    
    # #region agent log
    log_debug("manage.py:main", "DJANGO_SETTINGS_MODULE set", {"module": os.environ.get('DJANGO_SETTINGS_MODULE')}, "B")
    # #endregion
    
    try:
        from django.core.management import execute_from_command_line
        
        # #region agent log
        log_debug("manage.py:main", "Django import successful", {}, "B")
        # #endregion
        
    except ImportError as exc:
        # #region agent log
        log_debug("manage.py:main", "Django import failed", {"error": str(exc)}, "B")
        # #endregion
        
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # #region agent log
    log_debug("manage.py:main", "Executing command", {"command": sys.argv[1] if len(sys.argv) > 1 else "unknown"}, "A")
    # #endregion
    
    execute_from_command_line(sys.argv)
    
    # #region agent log
    log_debug("manage.py:main", "Command execution completed", {}, "A")
    # #endregion


if __name__ == '__main__':
    main()


