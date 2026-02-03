import os
import subprocess
import sys
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration: (name, app_module, port)
SERVICES = [
    ("Auth", "services.auth.main:app", 8005),
    ("Orders", "services.orders.main:app", 8001),
    ("Notification", "services.notification.main:app", 8004),
    ("Admin", "services.admin.main:app", 8006),
    ("AI", "services.ai.main:app", 8007),
    ("Frontend", "services.frontend.main:app", 8008),
    ("Gateway", "gateway.main:app", 8000),
]

def run_services():
    processes = []
    print("=" * 50)
    print("🚀 Starting all microservices...")
    print("=" * 50)

    try:
        for name, module, port in SERVICES:
            print(f"📦 Starting {name:12} on port {port}...")
            # We use sys.executable to ensure we use the same Python interpreter
            proc = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", module, "--host", "0.0.0.0", "--port", str(port)],
                stdout=None, # Inherit stdout for colors and ease of debugging
                stderr=None,
            )
            processes.append((name, proc))
            time.sleep(0.5) # Slight delay to avoid console output mess

        print("\n" + "=" * 50)
        print("✅ All services are running!")
        print("🔗 Gateway is available at: http://localhost:8000")
        print("⌨️  Press Ctrl+C to stop all services.")
        print("=" * 50 + "\n")

        while True:
            time.sleep(1)
            for name, proc in processes:
                if proc.poll() is not None:
                    print(f"❌ Service {name} stopped unexpectedly (exit code: {proc.returncode})")
                    raise KeyboardInterrupt

    except KeyboardInterrupt:
        print("\n🛑 Stopping all services...")
        for name, proc in processes:
            # On Windows, terminate() works well for uvicorn
            proc.terminate()
        
        for name, proc in processes:
            proc.wait()
        print("✅ All services stopped.")

if __name__ == "__main__":
    run_services()
