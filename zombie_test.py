#!/usr/bin/env python3
# zombie_test.py — creates a single zombie for a short window (default 10s)
import os, time, sys

window = int(sys.argv[1]) if len(sys.argv) > 1 else 10

pid = os.fork()
if pid == 0:
    # child of controller: become a parent that spawns an immediate-exit child
    child = os.fork()
    if child == 0:
        os._exit(0)           # actual child exits -> becomes zombie
    else:
        print(f"[PARENT] PID={os.getpid()} spawned CHILD PID={child}. Sleeping to keep zombie alive.")
        time.sleep(window*2)  # keep parent alive longer than controller window
        print(f"[PARENT] exiting (PID={os.getpid()})")
        sys.exit(0)
else:
    # controller: allow inspection window, then kill parent to auto-clean
    print(f"[CONTROLLER] Parent PID={pid}. Zombie inspection window: {window}s")
    print("Run in another terminal: ps -eo pid,ppid,stat,comm | awk '$3 ~ /Z/ {print $0}'")
    for i in range(window, 0, -1):
        print(f"[CONTROLLER] cleaning parent in {i}s...", end="\r")
        time.sleep(1)
    try:
        os.kill(pid, 9)
        print(f"\n[CONTROLLER] Killed parent PID={pid}. Zombie should be reaped.")
    except Exception as e:
        print(f"\n[CONTROLLER] Could not kill parent: {e}")
    sys.exit(0)
