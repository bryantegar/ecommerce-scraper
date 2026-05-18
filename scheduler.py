import time
import subprocess
import sys
from datetime import datetime

INTERVAL = 60 * 60  # 1 jam

while True:

    print(f"[{datetime.now()}] Running push_jobs.py")

    subprocess.run([
        sys.executable,
        "push_jobs.py"
    ])

    print(f"[{datetime.now()}] Sleeping...")

    time.sleep(INTERVAL)