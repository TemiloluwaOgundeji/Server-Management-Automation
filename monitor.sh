#!/bin/bash
# Monitoring Script 

set -e

# Configuration
LOG_DIR="./logs"
REPORT_FILE="$LOG_DIR/monitor-$(date +%Y%m%d-%H%M%S).log"
ALERT_CPU=80
ALERT_MEM=85
ALERT_DISK=90

# Create log directory
mkdir -p "$LOG_DIR"

# Get CPU usage (macOS)
get_cpu() {
    top -l 1 | awk '/CPU usage/ {print int($3 + 0)}'
}

# Get memory usage (macOS)
get_mem() {
    vm_stat | awk 'BEGIN{FS=":"; total=0; used=0}
    /Pages free/ {free=$2}
    /Pages active/ {active=$2}
    /Pages inactive/ {inactive=$2}
    /Pages speculative/ {speculative=$2}
    /Pages wired down/ {wired=$2}
    END{
        total = active + inactive + speculative + wired + free
        used = active + inactive + speculative + wired
        printf "%.0f", (used / total) * 100
    }'
}

# Get disk usage
get_disk() {
    df -h / | awk 'NR==2{print $5}' | sed 's/%//'
}

echo " SERVER HEALTH MONITOR REPORT "
echo ""
echo "$(date '+%Y-%m-%d %H:%M:%S')"
echo "$(hostname)"
echo ""

# Get metrics
CPU=$(get_cpu)
MEM=$(get_mem)
DISK=$(get_disk)

echo "RESOURCE USAGE"
echo "CPU:    ${CPU}%"
echo "Memory: ${MEM}%"
echo "Disk:   ${DISK}%"
echo ""

# Check alerts
if [ "$CPU" -gt "$ALERT_CPU" ] || [ "$MEM" -gt "$ALERT_MEM" ] || [ "$DISK" -gt "$ALERT_DISK" ]; then
    echo "ALERTS"
    [ "$CPU" -gt "$ALERT_CPU" ] && echo " HIGH CPU: ${CPU}%"
    [ "$MEM" -gt "$ALERT_MEM" ] && echo " HIGH MEMORY: ${MEM}%"
    [ "$DISK" -gt "$ALERT_DISK" ] && echo " HIGH DISK: ${DISK}%"
    echo ""
fi

# Detailed metrics
echo "SYSTEM DETAILS"
echo "Uptime:    $(uptime)"
echo "Load Avg:  $(uptime | awk -F'averages:' '{print $2}')"
echo "Processes: $(ps aux | wc -l)"
echo ""

# Memory details
echo "Memory (Detailed): $(vm_stat | grep 'Pages' | awk '{sum += $3} END {printf "%d pages total", sum}')"
echo "Disk:   $(df -h / | awk 'NR==2{printf "%s used / %s total", $3, $2}')"
echo ""

# Save and display to log
{
    echo "SERVER HEALTH REPORT - $(date)"
    echo "CPU: ${CPU}% | Memory: ${MEM}% | Disk: ${DISK}%"
    echo "Uptime: $(uptime)"
    echo "Load: $(uptime | awk -F'averages:' '{print $2}')"
} | tee "$REPORT_FILE"

echo "Complete! Report saved to:"
echo "   $REPORT_FILE"
