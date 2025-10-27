#!/bin/bash
#  Zombie Process Finder & Killer for macOS


echo "ZOMBIE PROCESS FINDER & KILLER"
echo ""

# Find zombie processes
ZOMBIES=$(ps aux | awk '$8 ~ /Z/ {print $2, $11}')

if [ -z "$ZOMBIES" ]; then
    echo "No zombie processes found!"
    echo ""
else
    echo "Found zombie processes:"
    echo "$ZOMBIES"
    echo ""

    echo " Checking parent processes..."
    ps aux | awk '$8 ~ /Z/ {print $2}' | while read zpid; do
        ppid=$(ps -o ppid= -p "$zpid" 2>/dev/null | tr -d ' ')
        if [ -n "$ppid" ]; then
            pname=$(ps -p "$ppid" -o comm= 2>/dev/null)
            echo "  Zombie PID: $zpid | Parent PID: $ppid ($pname)"
            echo "  Killing parent $ppid..."
            kill -9 "$ppid" 2>/dev/null && echo "     Killed!" || echo "     Failed"
        fi
    done
fi

echo ""
echo " Summary:"
echo "  Total processes: $(ps aux | wc -l | tr -d ' ')"
echo "  Zombie processes: $(ps aux | awk '$8 ~ /Z/' | wc -l | tr -d ' ')"
echo ""
echo " Zombie killer complete!"
