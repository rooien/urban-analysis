#!/usr/bin/env python3
"""
Victoria Urban Planning - App Runner Script

This script serves as the single entry point to run both the Backend API and
Frontend App concurrently. It automatically detects and terminates any existing
processes running on the configured ports, ensures the virtual environment and
dependencies are up to date, generates the frontend .env configuration, and
manages the server lifecycles with graceful shutdown.

Usage:
    python run_app.py
"""

import os
import sys
import subprocess
import time
import signal
import socket
from typing import List

# Define absolute paths using the project root
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PATH = os.path.join(ROOT_DIR, ".venv")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
REQUIREMENTS_FILE = os.path.join(ROOT_DIR, "requirements.txt")
CONFIG_PATH = os.path.join(ROOT_DIR, "config.yaml")


def is_port_in_use(port: int) -> bool:
    """
    Checks if a specific TCP port is already in use on localhost.

    Parameters:
        port (int): The port number to check.

    Returns:
        bool: True if the port is in use, False otherwise.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def get_listening_pids(port: int) -> List[int]:
    """
    Retrieves a list of Process IDs (PIDs) that are listening on the specified port.

    Parameters:
        port (int): The port number to check.

    Returns:
        List[int]: A list of listening PIDs.
    """
    if os.name == "nt":
        # Windows: parse netstat output
        try:
            cmd = ["netstat", "-ano", "-p", "tcp"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            pids = set()
            for line in result.stdout.splitlines():
                parts = line.strip().split()
                if len(parts) >= 5 and parts[1].endswith(f":{port}") and parts[3] == "LISTENING":
                    pid = int(parts[4])
                    if pid > 0:
                        pids.add(pid)
            return list(pids)
        except Exception:
            return []
    else:
        # POSIX (macOS/Linux): lsof
        try:
            cmd = ["lsof", "-t", f"-iTCP:{port}", "-sTCP:LISTEN"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return [int(pid) for pid in result.stdout.strip().split() if pid.isdigit()]
        except subprocess.CalledProcessError:
            return []
        except Exception:
            return []


def get_pgid(pid: int) -> int:
    """
    Retrieves the Process Group ID (PGID) for a given PID on POSIX systems.

    Parameters:
        pid (int): The process ID.

    Returns:
        int: The process group ID. Falls back to PID if PGID cannot be determined.
    """
    if os.name == "nt":
        return pid
    try:
        cmd = ["ps", "-o", "pgid=", "-p", str(pid)]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return int(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        return pid


def kill_port_processes(service_name: str, port: int) -> None:
    """
    Identifies and terminates all processes listening on a specific port,
    ensuring ports are freed before new servers are launched.

    Parameters:
        service_name (str): The display name of the service (e.g., 'Backend API').
        port (int): The port number to free.
    """
    if not is_port_in_use(port):
        print(f"[*] Port {port} ({service_name}) is free.")
        return

    print(f"[*] Port {port} ({service_name}) is occupied. Identifying running processes...")
    pids = get_listening_pids(port)
    if not pids:
        print(f"[!] Warning: Port {port} is occupied, but listening PID could not be determined.")
        return

    for pid in pids:
        pgid = get_pgid(pid)
        print(f"[*] Found PID {pid} (PGID {pgid}) on port {port}. Terminating process...")
        if os.name == "nt":
            try:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
            except Exception as e:
                print(f"[!] Error killing PID {pid}: {e}")
        else:
            try:
                os.killpg(pgid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            except PermissionError:
                print(f"[E] Permission denied when terminating process group {pgid}.")

    # Wait up to 2 seconds for graceful shutdown
    time.sleep(1.5)

    # Force kill if still occupied
    if is_port_in_use(port):
        print(f"[!] Port {port} still active. Forcing SIGKILL...")
        for pid in pids:
            if os.name == "nt":
                try:
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
                except Exception:
                    pass
            else:
                pgid = get_pgid(pid)
                try:
                    os.killpg(pgid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        time.sleep(1)

    if not is_port_in_use(port):
        print(f"[+] Port {port} ({service_name}) successfully freed.")
    else:
        print(f"[!] Warning: Port {port} could not be automatically freed.")


def activate_venv() -> None:
    """
    Ensures the Python virtual environment exists and is activated.

    If the venv does not exist, it is created and requirements are installed.
    Updates os.environ to simulate activation for all subsequently spawned
    processes.
    """
    import shutil
    
    # Ensure system tool paths (e.g. Homebrew node/npm) are present on macOS/Linux
    if os.name != "nt":
        for sys_path in ["/opt/homebrew/bin", "/usr/local/bin"]:
            if sys_path not in os.environ.get("PATH", "") and os.path.exists(sys_path):
                os.environ["PATH"] = sys_path + os.path.pathsep + os.environ.get("PATH", "")

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
    venv_bin = "Scripts" if os.name == "nt" else "bin"
    python_exe = os.path.join(VENV_PATH, venv_bin, "python.exe" if os.name == "nt" else "python")
    pip_exe = os.path.join(VENV_PATH, venv_bin, "pip.exe" if os.name == "nt" else "pip")

    if needs_install:
        print("[*] Installing/Updating backend dependencies from requirements.txt...")
        if os.path.exists(pip_exe):
            install_cmd = [pip_exe, "install", "-r", REQUIREMENTS_FILE]
        else:
            uv_bin = shutil.which("uv")
            if uv_bin:
                install_cmd = [uv_bin, "pip", "install", "--python", python_exe, "-r", REQUIREMENTS_FILE]
            else:
                install_cmd = [python_exe, "-m", "pip", "install", "-r", REQUIREMENTS_FILE]
        
        subprocess.run(install_cmd, check=True, cwd=ROOT_DIR)
        with open(venv_setup, "w") as f:
            f.write("")
        print("[*] Backend dependencies installed/updated successfully.")

    # Update environment variables to activate the venv for all child processes
    os.environ["VIRTUAL_ENV"] = VENV_PATH
    os.environ["PATH"] = (
        os.path.join(VENV_PATH, venv_bin) +
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

    This ensures that the frontend and backend are synchronized regarding
    ports, database paths, and baseline/post years without duplicate configuration.
    """
    import yaml
    if not os.path.exists(CONFIG_PATH):
        print(f"[!] Warning: config.yaml not found at {CONFIG_PATH}. Skipping .env generation.")
        return

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    ports = config.get("ports", {})
    historical = config.get("processing", {}).get("historical", {})
    
    env_path = os.path.join(FRONTEND_DIR, ".env")
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(f"VITE_API_PORT={ports.get('backend', 7000)}\n")
        f.write(f"VITE_APP_PORT={ports.get('frontend', 5000)}\n")
        f.write(f"VITE_BASELINE_YEAR={historical.get('baseline', {}).get('year', 2013)}\n")
        f.write(f"VITE_POST_YEAR={historical.get('post_intervention', {}).get('year', 2014)}\n")
    
    print(f"[*] Synchronized frontend environment at {env_path}")


def check_dependencies() -> None:
    """
    Ensures frontend dependencies (node_modules) and database are available.
    """
    if not os.path.exists(os.path.join(FRONTEND_DIR, "node_modules")):
        print("[*] Frontend dependencies (node_modules) not found.")
        print("[*] Running 'npm install' in frontend directory...")
        npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
        subprocess.run([npm_cmd, "install"], cwd=FRONTEND_DIR, check=True)
        print("[*] Frontend dependencies installed successfully.")

    import yaml
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    db_rel_path = config.get("paths", {}).get("database", "team_b/data/parking_analytics.duckdb")
    db_file = os.path.join(ROOT_DIR, db_rel_path)

    if not os.path.exists(db_file):
        print(f"\n[!] Warning: Database file not found at {db_file}.")
        print("[!] Please run 'python team_b/run_ingestion.py' to generate the DuckDB analytics store.\n")


def start_process(cmd: list, cwd: str) -> subprocess.Popen:
    """
    Starts a subprocess as the leader of a new process group.

    Parameters:
        cmd (list): The command to run as a list of strings.
        cwd (str): The working directory for the command.

    Returns:
        subprocess.Popen: The started subprocess object.
    """
    if os.name == "nt":
        return subprocess.Popen(
            cmd,
            cwd=cwd,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            stdout=None,
            stderr=None
        )
    return subprocess.Popen(
        cmd,
        cwd=cwd,
        start_new_session=True,  # POSIX: calls setsid()
        stdout=None,
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
            if os.name == "nt":
                proc.terminate()
            else:
                pgid = os.getpgid(proc.pid)
                os.killpg(pgid, signal.SIGTERM)

            proc.wait(timeout=4)

        except subprocess.TimeoutExpired:
            print(f"[!] {name} did not stop gracefully. Forcing termination...")
            if os.name == "nt":
                proc.kill()
            else:
                pgid = os.getpgid(proc.pid)
                os.killpg(pgid, signal.SIGKILL)
        except Exception as e:
            print(f"[!] Error stopping {name}: {e}")


def main() -> None:
    """
    Main execution function that orchestrates port cleanup, startup, and monitoring.
    """
    print("=" * 65)
    print("         Victoria Urban Planning - Executive App Runner          ")
    print("=" * 65)

    # Step 1: Ensure virtual environment is created and activated
    activate_venv()

    # Safely load ports from config.yaml
    import yaml
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    backend_port = config.get("ports", {}).get("backend", 7000)
    frontend_port = config.get("ports", {}).get("frontend", 5000)

    # Step 2: Auto-clean ports before launch
    print("\n[*] Auditing and freeing required server ports...")
    kill_port_processes("Backend API", backend_port)
    kill_port_processes("Frontend App", frontend_port)

    # Step 3: Generate frontend .env synchronized with config.yaml
    generate_frontend_env()

    # Step 4: Ensure dependencies are installed
    check_dependencies()

    api_process = None
    frontend_process = None

    try:
        # Step 5: Start Backend API (FastAPI / Uvicorn)
        print(f"\n[*] Starting Backend API (Uvicorn) on port {backend_port}...")
        uvicorn_exe = os.path.join(
            VENV_PATH,
            "Scripts" if os.name == "nt" else "bin",
            "uvicorn.exe" if os.name == "nt" else "uvicorn"
        )
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

        # Step 6: Start Frontend App (Vite)
        print(f"[*] Starting Frontend App (Vite) on port {frontend_port}...")
        frontend_cmd = [
            "npm.cmd" if os.name == "nt" else "npm", 
            "run", 
            "dev", 
            "--", 
            "--host", "0.0.0.0",
            "--port", str(frontend_port),
            "--strictPort"
        ]
        frontend_process = start_process(frontend_cmd, cwd=FRONTEND_DIR)

        print("\n" + "=" * 65)
        print(" [✓] Victoria Urban Planning Dashboard is live!")
        print(f"     • Executive Dashboard: http://localhost:{frontend_port}")
        print(f"     • REST API & Docs:     http://localhost:{backend_port}/docs")
        print("     • Press Ctrl+C to stop all services.")
        print("=" * 65 + "\n")

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
        print("\n\n[*] Received shutdown signal (Ctrl+C). Stopping all services...")
    finally:
        if api_process:
            stop_process(api_process, "Backend API")
        if frontend_process:
            stop_process(frontend_process, "Frontend App")
        print("[+] All services stopped cleanly.")


if __name__ == "__main__":
    main()

