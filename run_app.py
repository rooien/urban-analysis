#!/usr/bin/env python3
"""
Victoria Urban Planning - App Runner Script

This script automates all the steps required to run the Victoria Urban Planning
app, including activating the Python virtual environment, checking/installing
dependencies, dynamically generating frontend configuration from config.yaml,
and starting both the Backend API and Frontend App concurrently.

Usage:
    python run_app.py
"""

import os
import sys
import subprocess
import time
import signal
import socket

# Define absolute paths using the project root
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PATH = os.path.join(ROOT_DIR, ".venv")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
REQUIREMENTS_FILE = os.path.join(ROOT_DIR, "requirements.txt")


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


def activate_venv() -> None:
    """
    Ensures the Python virtual environment exists and is activated.

    If the venv does not exist, it is created and requirements are installed.
    Updates os.environ to simulate activation for all subsequently spawned
    processes.
    """
    if not os.path.exists(VENV_PATH):
        print(f"[*] Virtual environment not found at {VENV_PATH}.")
        print("[*] Creating virtual environment...")
        subprocess.run(
            [sys.executable, "-m", "venv", VENV_PATH], 
            check=True, 
            cwd=ROOT_DIR
        )

    venv_setup = os.path.join(VENV_PATH, "setup_complete")
    needs_install = (
        not os.path.exists(venv_setup) or 
        os.path.getmtime(REQUIREMENTS_FILE) > os.path.getmtime(venv_setup)
    )

    if needs_install:
        print("[*] Installing/Updating backend dependencies from requirements.txt...")
        pip_exe = os.path.join(VENV_PATH, "bin", "pip")
        subprocess.run(
            [pip_exe, "install", "-r", REQUIREMENTS_FILE], 
            check=True, 
            cwd=ROOT_DIR
        )
        with open(venv_setup, "w") as f:
            f.write("")
        print("[*] Backend dependencies installed/updated successfully.")

    # Update environment variables to activate the venv for all child processes
    os.environ["VIRTUAL_ENV"] = VENV_PATH
    os.environ["PATH"] = (
        os.path.join(VENV_PATH, "bin") + 
        os.path.pathsep + 
        os.environ.get("PATH", "")
    )
    os.environ.pop("PYTHONHOME", None)
    print("[*] Virtual environment activated.")

    # Ensure the current process can also import venv packages
    import glob
    lib_dirs = glob.glob(os.path.join(VENV_PATH, "lib", "python*", "site-packages")) + \
               glob.glob(os.path.join(VENV_PATH, "Lib", "site-packages"))
    if lib_dirs and lib_dirs[0] not in sys.path:
        sys.path.insert(0, lib_dirs[0])


def generate_frontend_env() -> None:
    """
    Generates a .env file in the frontend directory based on config.yaml values.

    This ensures that the frontend and backend are perfectly synchronized
    regarding ports and historical years without duplicating configuration.
    """
    import yaml  # Imported here since venv activation guarantees it is installed
    
    config_path = os.path.join(ROOT_DIR, "config.yaml")
    if not os.path.exists(config_path):
        print(f"[!] Warning: config.yaml not found at {config_path}. Skipping .env generation.")
        return

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    ports = config.get("ports", {})
    historical = config.get("processing", {}).get("historical", {})
    
    env_path = os.path.join(FRONTEND_DIR, ".env")
    with open(env_path, "w") as f:
        f.write(f"VITE_API_PORT={ports.get('backend', 8000)}\n")
        f.write(f"VITE_APP_PORT={ports.get('frontend', 5173)}\n")
        f.write(f"VITE_BASELINE_YEAR={historical.get('baseline', {}).get('year', 2013)}\n")
        f.write(f"VITE_POST_YEAR={historical.get('post_intervention', {}).get('year', 2014)}\n")
    
    print(f"[*] Generated frontend environment file at {env_path}")


def check_dependencies() -> None:
    """
    Ensures all necessary dependencies and files are present.

    Checks for frontend 'node_modules' and runs 'npm install' if missing.
    Checks for the duckdb database and prints a warning if it is not found.
    """
    # Check frontend dependencies
    if not os.path.exists(os.path.join(FRONTEND_DIR, "node_modules")):
        print("[*] Frontend dependencies (node_modules) not found.")
        print("[*] Running 'npm install' in frontend directory...")
        subprocess.run(["npm", "install"], cwd=FRONTEND_DIR, check=True)
        print("[*] Frontend dependencies installed successfully.")

    # Check backend database (load path from config.yaml safely)
    import yaml
    with open(os.path.join(ROOT_DIR, "config.yaml"), "r") as f:
        config = yaml.safe_load(f)
    
    db_rel_path = config.get("paths", {}).get("database", "data/parking_analytics.duckdb")
    db_file = os.path.join(ROOT_DIR, db_rel_path)

    if not os.path.exists(db_file):
        print(f"\n[!] Warning: Database file not found at {db_file}.")
        print("[!] The API will start, but endpoints will return errors.")
        print("[!] Please run 'python run_ingestion.py' to build the database.\n")


def start_process(cmd: list, cwd: str) -> subprocess.Popen:
    """
    Starts a subprocess as the leader of a new process group.

    This allows signals (like SIGTERM) to be sent to the entire process tree,
    preventing orphan background processes when shutting down.

    Parameters:
        cmd (list): The command to run as a list of strings.
        cwd (str): The working directory for the command.

    Returns:
        subprocess.Popen: The started subprocess object.
    """
    return subprocess.Popen(
        cmd,
        cwd=cwd,
        start_new_session=True,  # POSIX (macOS): calls setsid()
        stdout=None,  # Share stdout/stderr to stream logs to terminal
        stderr=None
    )


def stop_process(proc: subprocess.Popen, name: str) -> None:
    """
    Stops a subprocess and all its children cleanly.

    Parameters:
        proc (subprocess.Popen): The subprocess object to stop.
        name (str): The display name of the process for logging.
    """
    if proc and proc.poll() is None:
        try:
            # Kill the entire process group
            pgid = os.getpgid(proc.pid)
            os.killpg(pgid, signal.SIGTERM)
            proc.Wait(timeout=5)
        except subprocess.TimeoutExpired:
            print(f"[!] {name} did not stop gracefully. Forcing termination...")
            pgid = os.getpgid(proc.pid)
            os.killpg(pgid, signal.SIGKILL)
        except Exception as e:
            print(f"[!] Error stopping {name}: {e}")


def main() -> None:
    """
    Main execution function that orchestrates startup and monitoring.
    """
    print("=" * 60)
    print("           Victoria Urban Planning - App Runner           ")
    print("=" * 60)

    # Step 1: Ensure venv is created and activated
    activate_venv()

    # Safely load ports from config.yaml now that dependencies are installed
    import yaml
    with open(os.path.join(ROOT_DIR, "config.yaml"), "r") as f:
        config = yaml.safe_load(f)
    
    backend_port = config.get("ports", {}).get("backend", 8000)
    frontend_port = config.get("ports", {}).get("frontend", 5173)

    # Step 2: Generate frontend .env synchronized with config.yaml
    generate_frontend_env()

    # Step 3: Ensure dependencies are installed
    check_dependencies()

    # Step 4: Check if required ports are already in use
    port_errors = []
    if is_port_in_use(backend_port):
        port_errors.append(
            f"Port {backend_port} is already in use. The Backend API cannot start."
        )
    if is_port_in_use(frontend_port):
        port_errors.append(
            f"Port {frontend_port} is already in use. Frontend cannot start correctly."
        )
    
    if port_errors:
        print("\n[E] Required ports are blocked:")
        for err in port_errors:
            print(f" - {err}")
        print("[E] Please stop processes using these ports and try again.\n")
        sys.exit(1)

    api_process = None
    frontend_process = None

    try:
        # Step 5: Start Backend API
        print(f"\n[*] Starting Backend API (Uvicorn) on port {backend_port}...")
        uvicorn_exe = os.path.join(VENV_PATH, "bin", "uvicorn")
        api_cmd = [
            uvicorn_exe, 
            "src.api.main:app", 
            "--reload", 
            "--host", "127.0.0.1", 
            "--port", str(backend_port)
        ]
        api_process = start_process(api_cmd, cwd=ROOT_DIR)

        # Give API a moment to bind to the port before starting frontend
        time.sleep(1)

        # Step 6: Start Frontend App
        print(f"\n[*] Starting Frontend App (Vite) on port {frontend_port}...")
        frontend_cmd = ["npm", "run", "dev"]
        frontend_process = start_process(frontend_cmd, cwd=FRONTEND_DIR)

        print("\n" + "=" * 60)
        print(" App is running!")
        print(f" - Backend API:  http://127.0.0.1:{backend_port}")
        print(f" - Frontend App: http://127.0.0.1:{frontend_port}")
        print(" Press Ctrl+C to stop all services.")
        print("=" * 60 + "\n")

        # Monitor processes while running
        while True:
            if api_process.poll() is not None:
                print("\n[!] Backend API exited unexpectedly.")
                break
            if frontend_process.poll() is not None:
                print("\n[!] Frontend App exited unexpectedly.")
                break
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n[*] Received Ctrl+C. Stopping all services...")
    finally:
        if api_process:
            stop_process(api_process, "Backend API")
        if frontend_process:
            stop_process(frontend_process, "Frontend App")
        print("[*] All services stopped successfully.")


if __name__ == "__main__":
    main()
