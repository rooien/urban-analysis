#!/usr/bin/env python3
"""
Victoria Urban Planning - App Stopper Script

This script identifies and stops the processes running on the Backend API
and Frontend App ports configured in config.yaml. It ensures that any orphan
processes are cleanly terminated to free up the ports for subsequent runs.

Usage:
    python stop_app.py
"""

import os
import sys
import subprocess
import signal
import time
import socket
from typing import List


# Define absolute paths using the project root
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


def is_port_in_use(port: int) -> bool:
    """
    Checks if a specific TCP port is already in use on localhost.

    Parameters:
        port (int): The port number to check.

    Returns:
        bool: True if the port is in use, False otherwise.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def get_listening_pids(port: int) -> List[int]:
    """
    Retrieves a list of Process IDs (PIDs) that are listening on the specified port.

    Parameters:
        port (int): The port number to check.

    Returns:
        List[int]: A list of listening PIDs.
    """
    try:
        # -t: terse output (PIDs only)
        # -iTCP:{port}: TCP only on specific port
        # -sTCP:LISTEN: only processes in LISTEN state (excludes clients)
        cmd = ["lsof", "-t", f"-iTCP:{port}", "-sTCP:LISTEN"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return [int(pid) for pid in result.stdout.strip().split() if pid.isdigit()]
    except subprocess.CalledProcessError:
        return []


def get_pgid(pid: int) -> int:
    """
    Retrieves the Process Group ID (PGID) for a given PID.

    Parameters:
        pid (int): The process ID.

    Returns:
        int: The process group ID. Falls back to PID if PGID cannot be determined.
    """
    try:
        cmd = ["ps", "-o", "pgid=", "-p", str(pid)]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return int(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        return pid


def stop_port(name: str, port: int) -> None:
    """
    Stops all processes listening on a specific port by killing their process groups.

    Parameters:
        name (str): The display name of the service (e.g., "Backend API").
        port (int): The port number to free.
    """
    print(f"[*] Checking {name} on port {port}...")
    if not is_port_in_use(port):
        print(f"[+] {name} is not running (port {port} is free).")
        return

    pids = get_listening_pids(port)
    if not pids:
        print(f"[!] Port {port} is in use, but listening PID could not be determined.")
        return

    for pid in pids:
        pgid = get_pgid(pid)
        print(f"[*] Found PID {pid} (PGID {pgid}) listening on port {port}.")
        try:
            print(f"[*] Sending SIGTERM to process group {pgid}...")
            os.killpg(pgid, signal.SIGTERM)
        except ProcessLookupError:
            print(f"[+] Process group {pgid} already terminated.")
            continue
        except PermissionError:
            print(f"[E] Permission denied when trying to kill process group {pgid}.")
            continue

    # Give a moment for graceful shutdown
    time.sleep(2)

    if is_port_in_use(port):
        print(f"[!] Port {port} is still in use. Forcing termination...")
        for pid in pids:
            pgid = get_pgid(pid)
            try:
                print(f"[*] Sending SIGKILL to process group {pgid}...")
                os.killpg(pgid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        
        time.sleep(1)
        if is_port_in_use(port):
            print(f"[E] Failed to free port {port}. You may need to kill it manually.")
        else:
            print(f"[+] Port {port} successfully freed.")
    else:
        print(f"[+] Port {port} successfully freed.")


def main() -> None:
    """
    Main execution function that reads ports and orchestrates shutdown.
    """
    config_path = os.path.join(ROOT_DIR, "config.yaml")
    if not os.path.exists(config_path):
        print(f"[E] config.yaml not found at {config_path}")
        sys.exit(1)

    # Ensure venv packages can be imported (for PyYAML)
    venv_path = os.path.join(ROOT_DIR, ".venv")
    if os.path.exists(venv_path):
        import glob
        lib_dirs = glob.glob(os.path.join(venv_path, "lib", "python*", "site-packages")) + \
                   glob.glob(os.path.join(venv_path, "Lib", "site-packages"))
        if lib_dirs and lib_dirs[0] not in sys.path:
            sys.path.insert(0, lib_dirs[0])
    
    try:
        import yaml
    except ImportError:
        print("[E] PyYAML not found. Please ensure dependencies are installed via run_app.py.")
        sys.exit(1)

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    ports = config.get("ports", {})
    backend_port = ports.get("backend", 8000)
    frontend_port = ports.get("frontend", 5173)

    print("=" * 60)
    print("           Victoria Urban Planning - App Stopper          ")
    print("=" * 60)

    stop_port("Backend API", backend_port)
    print("-" * 60)
    stop_port("Frontend App", frontend_port)
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
