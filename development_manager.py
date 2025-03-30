"""
PyTrade Development Manager

This script provides an easy way to start, stop, and manage all components of the PyTrade
application during development. It handles the Flask backend, WebSocket server,
Swing Trading service, and Angular frontend.

Usage:
    python development_manager.py start              # Start all services
    python development_manager.py start <service>    # Start a specific service
    python development_manager.py stop               # Stop all services
    python development_manager.py stop <service>     # Stop a specific service
    python development_manager.py restart            # Restart all services
    python development_manager.py restart <service>  # Restart a specific service
    python development_manager.py status             # Check status of all services
"""

import os
import sys
import signal
import subprocess
import time
import argparse
import socket
import webbrowser
import logging
from pathlib import Path
import json
import atexit
import platform
import ctypes
import shutil
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("development_manager")

# Configuration
ANGULAR_PORT = 5010
FLASK_PORT = 5011
WEBSOCKET_PORT = 5012  # For WebSocket server
SWING_TRADING_PORT = 5013  # For Swing Trading Service

# Path to the application root directory
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
ATTACHED_ASSETS = os.path.join(APP_ROOT, "attached_assets")
PID_DIR = os.path.join(APP_ROOT, ".pids")
PORT_CONFIG_FILE = os.path.join(PID_DIR, "port_config.json")
CONFIG_FILE = os.path.join(APP_ROOT, "development_config.json")
LOG_DIR = os.path.join(APP_ROOT, "logs")

# Load config file if it exists, otherwise use defaults
DEFAULT_CONFIG = {
    "angular": {"port": 5010},
    "flask": {"port": 5011, "api_prefix": "/api"},
    "websocket": {"port": 5012, "path": "/ws"},
    "swing_trading": {"port": 5013, "api_prefix": "/api/swing-trading"}
}

def load_config():
    """Load configuration from file or use defaults."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading configuration: {e}")
    else:
        logger.warning(f"Configuration file not found: {CONFIG_FILE}. Using default configuration.")
    return DEFAULT_CONFIG

# Load configuration
SERVICE_CONFIG = load_config()

# Update port constants from config
ANGULAR_PORT = SERVICE_CONFIG.get("angular", {}).get("port", 5010)
FLASK_PORT = SERVICE_CONFIG.get("flask", {}).get("port", 5011)
WEBSOCKET_PORT = SERVICE_CONFIG.get("websocket", {}).get("port", 5012)
SWING_TRADING_PORT = SERVICE_CONFIG.get("swing_trading", {}).get("port", 5013)

# Add this variable to track active processes
running_processes = {}

# Process info
PROCESSES = {
    "angular": {
        "name": "Angular Frontend",
        "cmd": ["npx", "ng", "serve", "--proxy-config", "proxy.conf.json", "--host", "0.0.0.0", "--port", str(ANGULAR_PORT), "--disable-host-check"],
        "cwd": APP_ROOT,
        "pid_file": os.path.join(PID_DIR, "angular.pid"),
        "url": f"http://localhost:{ANGULAR_PORT}",
        "ready_message": f"Angular Live Development Server is listening on localhost:{ANGULAR_PORT}",
        "port": ANGULAR_PORT
    },
    "flask": {
        "name": "Flask Backend",
        "cmd": ["python", "simplified_pytrade.py"],
        "cwd": ATTACHED_ASSETS,
        "pid_file": os.path.join(PID_DIR, "flask.pid"),
        "port": FLASK_PORT,
        "url": f"http://localhost:{FLASK_PORT}",
        "ready_message": f"Running on http://0.0.0.0:{FLASK_PORT}",
        "port_env_var": "PORT"
    },
    "websocket": {
        "name": "WebSocket Server",
        "cmd": ["python", "websocket_server.py"],
        "cwd": ATTACHED_ASSETS,
        "pid_file": os.path.join(PID_DIR, "websocket.pid"),
        "port": WEBSOCKET_PORT,
        "ready_message": f"WebSocket server successfully started on 0.0.0.0:{WEBSOCKET_PORT}",
        "port_env_var": "WEBSOCKET_PORT"
    },
    "swing_trading": {
        "name": "Swing Trading Service",
        "cmd": ["python", "swing_trading_service.py"],
        "cwd": ATTACHED_ASSETS,
        "pid_file": os.path.join(PID_DIR, "swing_trading.pid"),
        "port": SWING_TRADING_PORT,
        "ready_message": "Swing Trading Service started",
        "port_env_var": "SWING_TRADING_PORT"
    }
}

def ensure_pid_dir():
    """Ensure the PID directory exists."""
    os.makedirs(PID_DIR, exist_ok=True)

def is_port_in_use(port):
    """Check if a port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_available_port(start_port, max_attempts=10):
    """Find an available port starting from start_port."""
    port = start_port
    for _ in range(max_attempts):
        if not is_port_in_use(port):
            return port
        port += 1
    return None  # No available port found

def write_pid(pid_file, pid):
    """Write a PID to a file."""
    with open(pid_file, 'w') as f:
        f.write(str(pid))

def read_pid(pid_file):
    """Read a PID from a file."""
    try:
        with open(pid_file, 'r') as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return None

def is_process_running(pid):
    """Check if a process is running based on its PID."""
    if pid is None:
        return False
        
    try:
        # Check if process exists - sending signal 0 doesn't kill the process
        os.kill(pid, 0)
        return True
    except OSError:
        return False

def is_windows():
    """Check if running on Windows."""
    return platform.system() == "Windows"

def terminate_windows_process(pid):
    """Terminate a process on Windows."""
    try:
        # Try using taskkill (recommended way on Windows)
        subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=False, 
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except Exception as e:
        logger.error(f"Error terminating Windows process: {e}")
        return False

def cleanup_on_exit():
    """Clean up any running processes when the script exits."""
    if running_processes:
        logger.info("Performing cleanup before exit...")
        for process_key, pid in list(running_processes.items()):
            try:
                if is_process_running(pid):
                    logger.info(f"Stopping {PROCESSES[process_key]['name']} (PID {pid})...")
                    if is_windows():
                        terminate_windows_process(pid)
                    else:
                        os.kill(pid, signal.SIGTERM)
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")

# Register the cleanup function to run on exit
atexit.register(cleanup_on_exit)

def load_port_config():
    """Load saved port configuration if available."""
    if os.path.exists(PORT_CONFIG_FILE):
        try:
            with open(PORT_CONFIG_FILE, 'r') as f:
                port_config = json.load(f)
            # Update process info with saved ports
            for key, info in PROCESSES.items():
                if key in port_config and "port" in info:
                    saved_port = port_config[key]
                    if saved_port != info["port"]:
                        logger.info(f"Using saved port {saved_port} for {info['name']} (default: {info['port']})")
                        # Only update the port if it's available and valid
                        if isinstance(saved_port, int) and saved_port > 0 and saved_port < 65536 and not is_port_in_use(saved_port):
                            info["port"] = saved_port
                            # Update URL with saved port
                            if "url" in info:
                                default_port = ANGULAR_PORT if key == "angular" else FLASK_PORT if key == "flask" else WEBSOCKET_PORT if key == "websocket" else info["port"]
                                info["url"] = info["url"].replace(f":{default_port}", f":{saved_port}")
                            # Update ready message with saved port
                            if "ready_message" in info:
                                default_port = ANGULAR_PORT if key == "angular" else FLASK_PORT if key == "flask" else WEBSOCKET_PORT if key == "websocket" else info["port"]
                                info["ready_message"] = info["ready_message"].replace(f":{default_port}", f":{saved_port}")
        except Exception as e:
            logger.warning(f"Error loading saved port configuration: {e}")
            # If the file is corrupted, remove it
            try:
                os.remove(PORT_CONFIG_FILE)
                logger.info("Removed corrupted port configuration file")
            except:
                pass

def save_port_config():
    """Save current port configuration."""
    port_config = {}
    for key, info in PROCESSES.items():
        if "port" in info:
            port_config[key] = info["port"]
    try:
        with open(PORT_CONFIG_FILE, 'w') as f:
            json.dump(port_config, f)
    except Exception as e:
        logger.warning(f"Error saving port configuration: {e}")

def start_process(process_key):
    """Start a process."""
    process_info = PROCESSES[process_key]
    name = process_info["name"]
    
    # Check if the process is already running
    pid = read_pid(process_info["pid_file"])
    if pid and is_process_running(pid):
        logger.info(f"{name} is already running with PID {pid}")
        return True
    
    # Clean up any stale PID file
    try:
        if pid and not is_process_running(pid):
            os.remove(process_info["pid_file"])
            logger.debug(f"Removed stale PID file for {name}")
    except:
        pass
        
    # Check if the port is in use (if applicable) and find an alternative
    original_port = None
    if "port" in process_info:
        original_port = process_info["port"]
        if is_port_in_use(original_port):
            new_port = find_available_port(original_port)
            if new_port is None:
                logger.error(f"Could not find an available port for {name}. All ports from {original_port} to {original_port+10} are in use.")
                return False
                
            if new_port != original_port:
                logger.warning(f"Port {original_port} is already in use for {name}. Using port {new_port} instead.")
                process_info["port"] = new_port
                
                # Update command with new port if applicable
                if "port_env_var" in process_info:
                    env = os.environ.copy()
                    env[process_info["port_env_var"]] = str(new_port)
                    process_info["env"] = env
                else:
                    # For Angular, update the port in the command
                    if process_key == "angular":
                        try:
                            port_index = process_info["cmd"].index(str(original_port))
                            process_info["cmd"][port_index] = str(new_port)
                        except ValueError:
                            logger.warning(f"Could not find port in command for {name}")
                
                # Update URL with new port
                if "url" in process_info:
                    process_info["url"] = process_info["url"].replace(f":{original_port}", f":{new_port}")
                    
                # Update ready message with new port
                if "ready_message" in process_info:
                    process_info["ready_message"] = process_info["ready_message"].replace(f":{original_port}", f":{new_port}")
                
                # Save the port configuration for future runs
                save_port_config()
    
    # Start the process
    logger.info(f"Starting {name}...")
    
    try:
        # Create a temporary config file for the process if needed
        temp_config = None
        if process_key == "websocket":
            # Create a temp config file for the WebSocket server to ensure it uses our port
            temp_config = os.path.join(ATTACHED_ASSETS, "websocket_config.json")
            try:
                with open(temp_config, 'w') as f:
                    json.dump({
                        "port": process_info["port"],
                        "host": "0.0.0.0"
                    }, f)
                logger.info(f"Temporary config file created for {name} at {temp_config}")
            except Exception as e:
                logger.warning(f"Failed to create temporary config for {name}: {e}")
        
        # Ensure log directory exists
        os.makedirs(LOG_DIR, exist_ok=True)
        
        # Create a log file path
        log_file_path = os.path.join(LOG_DIR, f"{process_key}.log")
        
        # Open a new process and redirect output to log files
        try:
            with open(log_file_path, 'w') as log_file:
                # Use environment variables if specified
                env = process_info.get("env", os.environ.copy())
                
                # Always set the port environment variable if defined
                if "port_env_var" in process_info:
                    env[process_info["port_env_var"]] = str(process_info["port"])
                
                # For websocket_server.py, pass the config file as an argument if created
                cmd = process_info["cmd"].copy()  # Make a copy to avoid modifying the original
                if process_key == "websocket" and temp_config:
                    cmd = cmd + ["--config", temp_config]
                    
                logger.info(f"Starting {name} with command: {' '.join(map(str, cmd))}")
                
                process = subprocess.Popen(
                    cmd,
                    cwd=process_info["cwd"],
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    env=env
                )
        except Exception as e:
            logger.error(f"Failed to start process or create log file: {e}")
            logger.error(traceback.format_exc())
            return False
            
        # Write PID to file
        write_pid(process_info["pid_file"], process.pid)
        # Register the process for cleanup on exit
        running_processes[process_key] = process.pid
        
        # Wait for confirmation that the process has started
        # For simplicity, we just wait a moment
        time.sleep(2)
        
        if is_process_running(process.pid):
            logger.info(f"{name} started with PID {process.pid}")
            logger.info(f"Log file: {log_file_path}")
            if "url" in process_info:
                logger.info(f"URL: {process_info['url']}")
            
            # If we used a different port, store the used port in a local variable,
            # but reset the original port in the process_info for future runs
            actual_port = process_info["port"]
            if original_port is not None and actual_port != original_port:
                process_info["port"] = original_port
            
            # Clean up temporary config file if it exists
            if temp_config:
                try:
                    os.remove(temp_config)
                    logger.info(f"Temporary config file deleted for {name} at {temp_config}")
                except Exception as e:
                    logger.warning(f"Failed to delete temporary config file: {e}")
            
            return True
        else:
            logger.error(f"Failed to start {name}. Check the log file: {log_file_path}")
            # Remove from running processes if failed
            if process_key in running_processes:
                del running_processes[process_key]
                
            # Also clean up the PID file
            try:
                os.remove(process_info["pid_file"])
            except:
                pass
                
            return False
    except Exception as e:
        logger.error(f"Error starting {name}: {e}")
        logger.error(traceback.format_exc())
        # Remove from running processes if error
        if process_key in running_processes:
            del running_processes[process_key]
        
        # If we used a different port, reset the original port value for future runs
        if original_port is not None and process_info["port"] != original_port:
            process_info["port"] = original_port
        return False

def stop_process(process_key):
    """Stop a process."""
    process_info = PROCESSES[process_key]
    name = process_info["name"]
    
    # Check if the process is running
    pid = read_pid(process_info["pid_file"])
    if not pid:
        logger.info(f"{name} is not running (no PID found)")
        return True
    if not is_process_running(pid):
        logger.info(f"{name} is not running (PID {pid} not found)")
        # Clean up the PID file
        try:
            os.remove(process_info["pid_file"])
        except FileNotFoundError:
            pass
        return True
    
    # Stop the process
    logger.info(f"Stopping {name} (PID {pid})...")
    try:
        # Use platform-specific termination signals
        if is_windows():
            # On Windows, use taskkill to terminate
            success = terminate_windows_process(pid)
            if not success:
                logger.warning(f"Failed to terminate {name} using taskkill, trying alternative methods")
                # Try to forcefully kill the process
                try:
                    os.kill(pid, signal.SIGTERM)
                except:
                    pass
        else:
            # On Unix-like systems, use signals
            os.kill(pid, signal.SIGTERM)
        
        # Give it a moment to terminate
        for _ in range(5):
            time.sleep(1)
            if not is_process_running(pid):
                logger.info(f"{name} stopped")
                # Clean up the PID file
                try:
                    os.remove(process_info["pid_file"])
                except FileNotFoundError:
                    pass
                # Remove from running processes list
                if process_key in running_processes:
                    del running_processes[process_key]
                return True
        
        # Force kill if it didn't terminate
        logger.warning(f"{name} didn't terminate gracefully, force killing...")
        if is_windows():
            # Try again with stronger force option
            for attempt in range(3):
                logger.info(f"Attempt {attempt + 1} to force kill {name} (PID {pid})")
                try:
                    subprocess_result = subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], check=False, 
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if subprocess_result.returncode == 0:
                        logger.info(f"{name} force killed successfully on attempt {attempt + 1}")
                        break
                    else:
                        logger.error(f"Force kill attempt {attempt + 1} failed: {subprocess_result.stderr.decode()}")
                except Exception as e:
                    logger.error(f"Force kill attempt {attempt + 1} failed with exception: {e}")
                time.sleep(1)
        else:
            try:
                os.kill(pid, signal.SIGKILL)
            except:
                pass
        
        # Wait a bit to ensure process is gone
        time.sleep(2)
        
        # Clean up the PID file
        try:
            os.remove(process_info["pid_file"])
        except FileNotFoundError:
            pass
        
        # Remove from running processes list
        if process_key in running_processes:
            del running_processes[process_key]
            
        if not is_process_running(pid):
            logger.info(f"{name} stopped (force killed)")
            return True
        else:
            logger.error(f"Failed to kill {name} (PID {pid})")
            return False
    except Exception as e:
        logger.error(f"Error stopping {name}: {e}")
        logger.error(traceback.format_exc())
        return False

def check_status():
    """Check the status of all processes."""
    statuses = {}
    for key, info in PROCESSES.items():
        pid = read_pid(info["pid_file"])
        running = pid is not None and is_process_running(pid)
        statuses[key] = {
            "name": info["name"],
            "running": running,
            "pid": pid
        }
        
        # Check if port is in use if specified
        if "port" in info:
            default_port = info["port"]
            statuses[key]["default_port"] = default_port
            statuses[key]["port_in_use"] = is_port_in_use(default_port)
            
            # For running processes, determine the actual port they're using
            if running and "port_env_var" in info:
                # Try to get actual port from process environment or log file
                log_file_path = os.path.join(APP_ROOT, "logs", f"{key}.log")
                if os.path.exists(log_file_path):
                    try:
                        with open(log_file_path, 'r') as f:
                            log_content = f.read()
                            
                            # Look for port indication in logs
                            if key == "flask":
                                # Flask log typically shows "Running on http://0.0.0.0:PORT"
                                import re
                                match = re.search(r'Running on http://0.0.0.0:(\d+)', log_content)
                                if match:
                                    statuses[key]["actual_port"] = int(match.group(1))
                            elif key == "websocket":
                                # WebSocket log shows "WebSocket server successfully started on 0.0.0.0:PORT"
                                match = re.search(r'WebSocket server successfully started on 0.0.0.0:(\d+)', log_content)
                                if match:
                                    statuses[key]["actual_port"] = int(match.group(1))
                    except:
                        # If we can't determine the actual port, don't set it
                        pass
                    
    return statuses

def display_status(statuses):
    """Display the status of all processes."""
    print("\n=== PyTrade Development Status ===\n")
    
    for key, status in statuses.items():
        status_text = "RUNNING" if status["running"] else "STOPPED"
        status_color = "\033[92m" if status["running"] else "\033[91m"  # Green or Red
        reset_color = "\033[0m"
        
        print(f"{status['name']}: {status_color}{status_text}{reset_color}")
        
        if status["running"]:
            print(f"  PID: {status['pid']}")
            if "port_in_use" in status:    
                # If we know the actual port being used, show it
                if "actual_port" in status and status["actual_port"] != status["default_port"]:
                    port_status = f"USING ALTERNATE PORT {status['actual_port']} (default: {status['default_port']})"
                    port_color = "\033[93m"  # Yellow for alternate port
                else:
                    port_status = f"OPEN on default port {status['default_port']}"
                    port_color = "\033[92m"  # Green
                
                print(f"  Port: {port_color}{port_status}{reset_color}")
                
                if "url" in PROCESSES[key]:
                    url = PROCESSES[key]["url"]
                    # If using an alternate port, adjust the URL shown
                    if "actual_port" in status:
                        default_port = status["default_port"]
                        actual_port = status["actual_port"]
                        if default_port != actual_port:
                            url = url.replace(f":{default_port}", f":{actual_port}")
                    print(f"  URL: {url}")
        
        print()

def start_all():
    """Start all processes."""
    ensure_pid_dir()
    
    # Load saved port configuration
    load_port_config()
    
    logger.info("Starting all PyTrade development services...")
    
    # Start backend services first
    backend_services = ["flask", "websocket", "swing_trading"]
    started_services = []
    
    for service in backend_services:    
        try:
            # If a service fails to start, continue with others
            if start_process(service):
                started_services.append(service)
            else:
                logger.warning(f"Failed to start {PROCESSES[service]['name']}, continuing with other services")
            time.sleep(2)  # Give each service a moment to initialize
        except KeyboardInterrupt:
            logger.info("Startup interrupted by user")
            # Clean up the services that did start
            for started_service in started_services:
                try:
                    stop_process(started_service)
                except:
                    pass
            display_status(check_status())
            return
        except Exception as e:
            logger.error(f"Error starting {service}: {e}")
            logger.error(traceback.format_exc())
    
    # Then start Angular (frontend)
    try:
        if start_process("angular"):
            started_services.append("angular")
            
            # Open the browser after a short delay
            time.sleep(5)
            try:
                logger.info("Opening browser to PyTrade application...")
                webbrowser.open(PROCESSES["angular"]["url"])
            except Exception as e:
                logger.error(f"Error opening browser: {e}")
        else:
            logger.warning("Failed to start Angular frontend")
    except KeyboardInterrupt:
        logger.info("Startup interrupted by user")
        # Clean up the services that did start
        for started_service in started_services:
            try:
                stop_process(started_service)
            except:
                pass
        display_status(check_status())
        return
    except Exception as e:
        logger.error(f"Error starting Angular: {e}")
        logger.error(traceback.format_exc())
    
    # Display current status
    display_status(check_status())

def stop_all():
    """Stop all processes."""
    logger.info("Stopping all PyTrade development services...")
    
    # Stop in reverse order (frontend first, then backends)
    stop_process("angular")
    stop_process("swing_trading")
    stop_process("websocket")
    stop_process("flask")
    
    # Display current status
    display_status(check_status())

def restart_all():
    """Restart all processes."""
    logger.info("Restarting all PyTrade development services...")
    stop_all()
    time.sleep(2)  # Give processes time to fully stop
    start_all()

def main():
    parser = argparse.ArgumentParser(description="PyTrade Development Manager")
    parser.add_argument("action", choices=["start", "stop", "restart", "status"], 
                        help="Action to perform")
    parser.add_argument("service", nargs="?", choices=list(PROCESSES.keys()) + ["all"],
                        default="all", help="Service to manage (default: all)")
    parser.add_argument("--reset-ports", action="store_true", 
                        help="Reset to default ports (ignore saved configuration)")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    args = parser.parse_args()
    
    # Set debug logging if requested
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Handle port reset if requested
    if args.reset_ports and os.path.exists(PORT_CONFIG_FILE):
        os.remove(PORT_CONFIG_FILE)
        logger.info("Port configuration reset to defaults")
    
    # Make sure PID directory exists
    ensure_pid_dir()
    
    try:
        if args.service == "all":
            if args.action == "start":
                start_all()
            elif args.action == "stop":
                stop_all()
            elif args.action == "restart":
                restart_all()
            elif args.action == "status":
                display_status(check_status())
        else:
            # Managing a single service
            if args.service not in PROCESSES:
                logger.error(f"Unknown service: {args.service}")
                print(f"Available services: {', '.join(PROCESSES.keys())}")
                sys.exit(1)
            if args.action == "start":
                logger.info(f"Starting {PROCESSES[args.service]['name']}...")
                if start_process(args.service):
                    logger.info(f"{PROCESSES[args.service]['name']} started successfully")
                else:
                    logger.error(f"Failed to start {PROCESSES[args.service]['name']}")
                    sys.exit(1)
            elif args.action == "stop":
                logger.info(f"Stopping {PROCESSES[args.service]['name']}...")
                if stop_process(args.service):
                    logger.info(f"{PROCESSES[args.service]['name']} stopped successfully")
                else:
                    logger.error(f"Failed to stop {PROCESSES[args.service]['name']}")
                    sys.exit(1)
            elif args.action == "restart":
                logger.info(f"Restarting {PROCESSES[args.service]['name']}...")
                stop_process(args.service)
                time.sleep(2)  # Give process time to fully stop
                if start_process(args.service):
                    logger.info(f"{PROCESSES[args.service]['name']} restarted successfully")
                else:
                    logger.error(f"Failed to restart {PROCESSES[args.service]['name']}")
                    sys.exit(1)
            elif args.action == "status":
                display_status(check_status())
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        # Let the atexit handler do the cleanup
        sys.exit(0)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()