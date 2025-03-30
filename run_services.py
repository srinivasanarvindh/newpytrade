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
        log_file = open(f"{script}.log", "w")  # Log output to a file
        process = subprocess.Popen(
            ["python", script],
            stdout=log_file,
            stderr=subprocess.STDOUT
        )
        processes.append((process, log_file))
        print(f"Started {script} with PID {process.pid}")

    # Wait for all processes to complete
    for process, log_file in processes:
        process.wait()
        log_file.close()
except KeyboardInterrupt:
    print("Stopping all services...")
    for process, log_file in processes:
        process.terminate()
        process.wait()
        log_file.close()
