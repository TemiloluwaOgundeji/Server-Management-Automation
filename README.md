# Server-Management-Automation

What it does: A production-ready bash script that monitors server health, auto-remediates common issues, and maintains detailed logs
Includes:
Real-time monitoring of CPU, memory, disk, network, and processes
Automatic remediation (kill zombie processes, clear temp files when disk >80%)
Pattern detection (identify repeated errors, alert on anomalies)
Structured JSON and CSV logging for analysis
Email/webhook alerts with escalation levels
Service health checks with auto-restart capabilities
Performance trending over time


Server Health Monitor:
Logs all reports with timestamps
Alerts if CPU, memory, or disk usage exceed set limits
Shows uptime, process count, and load averages

Requirements:
No external dependencies — just the default system tools:
bash
top
df
ps
awk

Installation
1. Clone or copy this project
2. Make the script executable: chmod +x monitor.sh
3. Run it: ./monitor.sh

   
Alert Thresholds
You can adjust alert thresholds at the top of the script:
ALERT_CPU=80
ALERT_MEM=85
ALERT_DISK=90


Logs
All reports are automatically saved in:
./logs/

Each log file is timestamped, e.g.:
Monitor-20251027-114552.log








Zombie Process Test & Killer (macOS / Linux)
Creates, detects, and removes zombie processes safely on your local machine.

zombie_test.py: Python script that creates a temporary zombie process for testing.
zombie_disk.sh: Bash script that finds and kills zombie parent processes.

Requirements:
macOS or Linux terminal
Python 3
Bash shell



Step-by-Step Usage:
1. Make scripts executable:
chmod +x zombie_test.py zombie.sh


2. Open two terminals
Terminal A → to run the zombie creator (zombie_test.py)
Terminal B → to check and kill zombies (zombie_disk.sh)

3. Create a zombie process
In Terminal A, run:
./zombie_test.py 10
(This will create a zombie process (a defunct child process)


Keep it alive for 10 seconds before automatic cleanup
You’ll see output like:
[CONTROLLER] Parent PID=4231. Zombie inspection window: 10s
[PARENT] PID=4232 spawned CHILD PID=4233. Sleeping to keep zombie alive.


4. Check for zombies
In Terminal B, run:
ps -eo pid,ppid,stat,comm | awk '$3 ~ /Z/ {print $0}'

You should see a line with Z in the STAT column — this indicates a zombie process:
PID   PPID  STAT  COMMAND
4233  4232  Z     python3


5. Run your killer script
While the zombie still exists, run:
./zombie.sh

6. Verify cleanup
After running your killer, check again:
ps -eo pid,ppid,stat,comm | awk '$3 ~ /Z/ {print $0}'







Combined Logging System: Logs application events as JSON and system metrics as CSV.

# Create virtual environment
python -m venv venv

# Activate environment
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install psutil

# Run
python JSON_CSV_logger.py
Press Ctrl+C to stop.

Output:
app_events.json - Application events with timestamps
system_metrics.csv - CPU, memory, disk metrics









Email + Slack Alert Script: sends alerts to both Email and Slack when a system check fails.


Setup:
1. Clone or copy the script

2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  

3. Install dependencies
pip install requests

4. Set environment variables
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="465"
export SMTP_USER="your_email@gmail.com"
export SMTP_PASS="your_app_password"
export EMAIL_FROM="your_email@gmail.com"
export EMAIL_TO="recipient1@gmail.com,recipient2@gmail.com"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/XXX/YYY/ZZZ"

5. Run the script
python alerts.py

You should see:
✅ Email alert sent
Slack alert sent

