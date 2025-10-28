import json
import csv
import time
import psutil
from datetime import datetime
from pathlib import Path

class JSONLogger:
    def __init__(self, filename='events.json'):
        self.filename = filename
    
    def log_event(self, event_type, message, metadata=None):
        """Save events as JSON with timestamps"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'message': message,
            'metadata': metadata or {}
        }
        
        with open(self.filename, 'a') as f:
            f.write(json.dumps(event) + '\n')
        
        return event
    
    def log_monitoring(self, service, status, response_time=None):
        """Log monitoring events"""
        return self.log_event(
            'monitoring',
            f'{service} health check',
            {'service': service, 'status': status, 'response_time': response_time}
        )
    
    def log_remediation(self, issue, action, success):
        """Log remediation actions"""
        return self.log_event(
            'remediation',
            f'Fix attempt for {issue}',
            {'issue': issue, 'action': action, 'success': success}
        )

class CSVMetricsLogger:
    def __init__(self, filename='metrics.csv'):
        self.filename = filename
        self.headers = ['timestamp', 'cpu_percent', 'memory_mb', 'disk_read_mb', 'disk_write_mb']
        self._init_file()
    
    def _init_file(self):
        """Create CSV with header row"""
        if not Path(self.filename).exists():
            with open(self.filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(self.headers)
    
    def log_metrics(self):
        """Save CPU, memory, disk readings over time"""
        cpu = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory().used / (1024**2)
        disk = psutil.disk_io_counters()
        disk_read = disk.read_bytes / (1024**2)
        disk_write = disk.write_bytes / (1024**2)
        
        row = [
            datetime.now().isoformat(),
            f'{cpu:.2f}',
            f'{memory:.2f}',
            f'{disk_read:.2f}',
            f'{disk_write:.2f}'
        ]
        
        with open(self.filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)
        
        return {'cpu': cpu, 'memory': memory}

def main():
    """Main script with both JSON and CSV logging"""
    json_log = JSONLogger('app_events.json')
    csv_log = CSVMetricsLogger('system_metrics.csv')
    
    print("=== Combined Logging System Started ===\n")
    
    # Log startup event
    json_log.log_event('system', 'Application started', {'version': '1.0'})
    
    try:
        for i in range(10):
            # Log system metrics to CSV
            metrics = csv_log.log_metrics()
            print(f"[Metrics] CPU: {metrics['cpu']:.1f}% | Memory: {metrics['memory']:.0f}MB")
            
            # Log monitoring events to JSON
            if metrics['cpu'] > 80:
                json_log.log_monitoring('cpu', 'critical', metrics['cpu'])
                json_log.log_remediation('high_cpu', 'alert_sent', True)
                print("High CPU detected - logged remediation")
            else:
                json_log.log_monitoring('system', 'healthy', metrics['cpu'])
            
            time.sleep(3)
            
    except KeyboardInterrupt:
        json_log.log_event('system', 'Application stopped', {'reason': 'user_interrupt'})
        print("\n\n=== Logging System Stopped ===")
        print(f"Events logged to: {json_log.filename}")
        print(f"Metrics logged to: {csv_log.filename}")

if __name__ == '__main__':
    main()
