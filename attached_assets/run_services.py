import subprocess

# Define the scripts to run
scripts = [
    "simplified_trade.py",
    "swing_trading_service.py",
    "websocket_server.py"
]

# Start each script in a separate process
processes = []
try:
    for script in scripts:
        process = subprocess.Popen(["python", script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        processes.append(process)
        print(f"Started {script} with PID {process.pid}")

    # Wait for all processes to complete
    for process in processes:
        process.wait()
except KeyboardInterrupt:
    print("Stopping all services...")
    for process in processes:
        process.terminate()
        process.wait()
