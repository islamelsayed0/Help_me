#!/usr/bin/env python
"""Diagnostic script to check server status."""
import socket
import subprocess
import sys
import json
import os
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

def check_port(host, port):
    """Check if a port is open."""
    # #region agent log
    log_debug("check_server.py:check_port", "Checking port", {"host": host, "port": port}, "C")
    # #endregion
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        
        # #region agent log
        log_debug("check_server.py:check_port", "Port check result", {"host": host, "port": port, "open": result == 0}, "C")
        # #endregion
        
        return result == 0
    except Exception as e:
        # #region agent log
        log_debug("check_server.py:check_port", "Port check error", {"error": str(e)}, "C")
        # #endregion
        return False

def check_process(port):
    """Check if a process is using the port."""
    # #region agent log
    log_debug("check_server.py:check_process", "Checking process on port", {"port": port}, "E")
    # #endregion
    
    try:
        result = subprocess.run(
            ['lsof', '-i', f':{port}'],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        # #region agent log
        log_debug("check_server.py:check_process", "Process check result", {"port": port, "output": result.stdout, "has_process": len(result.stdout) > 0}, "E")
        # #endregion
        
        return len(result.stdout) > 0
    except Exception as e:
        # #region agent log
        log_debug("check_server.py:check_process", "Process check error", {"error": str(e)}, "E")
        # #endregion
        return False

def main():
    # #region agent log
    log_debug("check_server.py:main", "Starting server diagnostics", {}, "A")
    # #endregion
    
    port = 8000
    host = '127.0.0.1'
    
    print(f"Checking server status on {host}:{port}...")
    
    # Check if port is open
    port_open = check_port(host, port)
    print(f"Port {port} is {'OPEN' if port_open else 'CLOSED'}")
    
    # Check if process is using port
    has_process = check_process(port)
    print(f"Process on port {port}: {'YES' if has_process else 'NO'}")
    
    # Check virtual environment
    venv_path = os.path.join(os.path.dirname(__file__), 'venv')
    venv_exists = os.path.exists(venv_path)
    
    # #region agent log
    log_debug("check_server.py:main", "Virtual env check", {"venv_exists": venv_exists, "venv_path": venv_path}, "A")
    # #endregion
    
    print(f"Virtual environment exists: {venv_exists}")
    
    # Check Django installation
    try:
        import django
        django_version = django.get_version()
        
        # #region agent log
        log_debug("check_server.py:main", "Django import check", {"version": django_version}, "B")
        # #endregion
        
        print(f"Django version: {django_version}")
    except ImportError:
        # #region agent log
        log_debug("check_server.py:main", "Django import failed", {}, "B")
        # #endregion
        print("Django is NOT installed")
    
    # #region agent log
    log_debug("check_server.py:main", "Diagnostics complete", {"port_open": port_open, "has_process": has_process}, "A")
    # #endregion

if __name__ == '__main__':
    main()
