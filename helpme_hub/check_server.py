#!/usr/bin/env python
"""Diagnostic script to check server status."""
import socket
import subprocess
import sys
import os


def check_port(host, port):
    """Check if a port is open."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def check_process(port):
    """Check if a process is using the port."""
    try:
        result = subprocess.run(
            ['lsof', '-i', f':{port}'],
            capture_output=True,
            text=True,
            timeout=2
        )
        return len(result.stdout) > 0
    except Exception:
        return False


def main():
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
    print(f"Virtual environment exists: {venv_exists}")

    # Check Django installation
    try:
        import django
        django_version = django.get_version()
        print(f"Django version: {django_version}")
    except ImportError:
        print("Django is NOT installed")


if __name__ == '__main__':
    main()
