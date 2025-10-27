#!/usr/bin/env python3
import json
import csv
import time
import psutil
import smtplib
import requests
import subprocess
import socket
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class Logger:
    def __init__(self):
        self.json_file = 'server_events.json'
        self.csv_file = 'server_metrics.csv'
        self.trend_file = 'performance_trends.csv'
        self._init_csv()
    
    def _init_csv(self):
        if not Path(self.csv_file).exists():
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'cpu', 'memory', 'disk', 'network_sent', 'network_recv'])
        
        if not Path(self.trend_file).exists():
            with open(self.trend_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'metric', 'value', 'trend'])
    
    def log_event(self, event_type, message, metadata=None):
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'message': message,
            'metadata': metadata or {}
        }
        with open(self.json_file, 'a') as f:
            f.write(json.dumps(event) + '\n')
        return event
    
    def log_metrics(self, metrics):
        with open(self.csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                metrics['cpu'],
                metrics['memory'],
                metrics['disk'],
                metrics['network_sent'],
                metrics['network_recv']
            ])
    
    def log_trend(self, metric, value, trend):
        with open(self.trend_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now().isoformat(), metric, value, trend])

class Alerter:
    def __init__(self, config):
        self.config = config
        self.alert_history = defaultdict(int)
    
    def send_email(self, subject, message, level='INFO'):
        if not self.config.get('email_enabled'):
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config['sender_email']
            msg['To'] = self.config['recipient_email']
            msg['Subject'] = f"[{level}] {subject}"
            
            body = f"Level: {level}\nTime: {datetime.now()}\n\n{message}"
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
                server.starttls()
                server.login(self.config['sender_email'], self.config['sender_password'])
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Email alert failed: {e}")
            return False
    
    def send_webhook(self, message, level='low'):
        if not self.config.get('webhook_url'):
            return False
        
        try:
            colors = {'low': '#36a64f', 'medium': '#ff9900', 'high': '#ff0000', 'critical': '#8b0000'}
            payload = {
                'attachments': [{
                    'color': colors.get(level, '#808080'),
                    'title': f'{level.upper()} Alert',
                    'text': message,
                    'ts': int(datetime.now().timestamp())
                }]
            }
            response = requests.post(self.config['webhook_url'], json=payload, timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Webhook alert failed: {e}")
            return False
    
    def escalate(self, issue, level):
        """Escalate alerts based on frequency"""
        self.alert_history[issue] += 1
        count = self.alert_history[issue]
        
        if count == 1:
            return level
        elif count == 3:
            return 'high'
        elif count >= 5:
            return 'critical'
        return level

class MonitoringSystem:
    def __init__(self, logger, alerter):
        self.logger = logger
        self.alerter = alerter
        self.baseline = {}
        self.error_patterns = defaultdict(list)
        self.net_baseline = psutil.net_io_counters()
    
    def collect_metrics(self):
        net = psutil.net_io_counters()
        return {
            'cpu': psutil.cpu_percent(interval=1),
            'memory': psutil.virtual_memory().percent,
            'disk': psutil.disk_usage('/').percent,
            'network_sent': net.bytes_sent - self.net_baseline.bytes_sent,
            'network_recv': net.bytes_recv - self.net_baseline.bytes_recv,
            'processes': len(psutil.pids())
        }
    
    def detect_zombie_processes(self):
        """Find and kill zombie processes"""
        zombies = []
        for proc in psutil.process_iter(['pid', 'status', 'name']):
            try:
                if proc.info['status'] == psutil.STATUS_ZOMBIE:
                    zombies.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return zombies
    
    def kill_zombies(self, zombies):
        """Kill zombie processes"""
        killed = []
        for zombie in zombies:
            try:
                proc = psutil.Process(zombie['pid'])
                proc.kill()
                killed.append(zombie['pid'])
                self.logger.log_event('remediation', f"Killed zombie process", {'pid': zombie['pid']})
            except Exception as e:
                print(f"Failed to kill {zombie['pid']}: {e}")
        return killed
    
    def clear_temp_files(self):
        """Clear temporary files when disk is full"""
        try:
            result = subprocess.run(['sudo', 'rm', '-rf', '/tmp/*'], capture_output=True, timeout=30)
            size_freed = subprocess.run(['du', '-sh', '/tmp'], capture_output=True, text=True)
            self.logger.log_event('remediation', 'Cleared temp files', {'output': size_freed.stdout})
            return True
        except Exception as e:
            print(f"Failed to clear temp: {e}")
            return False
    
    def check_service_health(self, service_name, port):
        """Check if service is running"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result == 0
        except:
            return False
    
    def restart_service(self, service_name, max_attempts=3):
        """Auto-restart failed service"""
        for attempt in range(1, max_attempts + 1):
            try:
                subprocess.run(['sudo', 'systemctl', 'restart', service_name], timeout=10, check=True)
                time.sleep(3)
                self.logger.log_event('remediation', f'Restarted {service_name}', {'attempt': attempt})
                return True
            except:
                if attempt < max_attempts:
                    time.sleep(5)
        return False
    
    def detect_anomalies(self, metrics):
        """Detect anomalies using simple baseline comparison"""
        anomalies = []
        
        if not self.baseline:
            self.baseline = metrics.copy()
            return anomalies
        
        for key in ['cpu', 'memory', 'disk']:
            if metrics[key] > self.baseline[key] * 1.5:  # 50% increase
                anomalies.append({
                    'metric': key,
                    'value': metrics[key],
                    'baseline': self.baseline[key],
                    'increase': f"{((metrics[key] / self.baseline[key]) - 1) * 100:.1f}%"
                })
        
        # Update baseline slowly
        for key in metrics:
            if key in self.baseline:
                self.baseline[key] = self.baseline[key] * 0.9 + metrics[key] * 0.1
        
        return anomalies
    
    def analyze_trends(self, metrics):
        """Analyze performance trends"""
        trends = {}
        
        for key in ['cpu', 'memory', 'disk']:
            if key in self.baseline:
                diff = metrics[key] - self.baseline[key]
                if diff > 10:
                    trends[key] = 'increasing'
                elif diff < -10:
                    trends[key] = 'decreasing'
                else:
                    trends[key] = 'stable'
                
                self.logger.log_trend(key, metrics[key], trends[key])
        
        return trends
    
    def detect_error_patterns(self, error_msg):
        """Detect repeated errors"""
        self.error_patterns[error_msg].append(datetime.now())
        recent = [t for t in self.error_patterns[error_msg] if (datetime.now() - t).seconds < 300]
        self.error_patterns[error_msg] = recent
        return len(recent)
    
    def remediate(self, metrics):
        """Automatic remediation based on metrics"""
        actions = []
        
        # High CPU - check for zombies
        if metrics['cpu'] > 80:
            zombies = self.detect_zombie_processes()
            if zombies:
                killed = self.kill_zombies(zombies)
                actions.append(f"Killed {len(killed)} zombie processes")
        
        # High disk - clear temp
        if metrics['disk'] > 80:
            if self.clear_temp_files():
                actions.append("Cleared temporary files")
        
        # High memory - log top processes
        if metrics['memory'] > 85:
            top_procs = sorted(psutil.process_iter(['pid', 'name', 'memory_percent']), 
                             key=lambda p: p.info['memory_percent'], reverse=True)[:5]
            actions.append(f"Top memory processes logged")
            self.logger.log_event('alert', 'High memory usage', {
                'processes': [p.info for p in top_procs]
            })
        
        return actions

class ServerAutomationSuite:
    def __init__(self, config):
        self.logger = Logger()
        self.alerter = Alerter(config)
        self.monitor = MonitoringSystem(self.logger, self.alerter)
        self.services = config.get('services', {})
    
    def run_cycle(self):
        """Run one monitoring cycle"""
        # Collect metrics
        metrics = self.monitor.collect_metrics()
        self.logger.log_metrics(metrics)
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Metrics: CPU={metrics['cpu']:.1f}% | "
              f"Memory={metrics['memory']:.1f}% | Disk={metrics['disk']:.1f}%")
        
        # Detect anomalies
        anomalies = self.monitor.detect_anomalies(metrics)
        if anomalies:
            print(f"  ⚠️  Anomalies detected: {len(anomalies)}")
            for a in anomalies:
                self.logger.log_event('anomaly', f"{a['metric']} spike", a)
        
        # Analyze trends
        trends = self.monitor.analyze_trends(metrics)
        
        # Auto-remediate
        actions = self.monitor.remediate(metrics)
        if actions:
            print(f"  🔧 Remediation: {', '.join(actions)}")
        
        # Check and restart services
        for service, port in self.services.items():
            if not self.monitor.check_service_health(service, port):
                print(f"  ✗ {service} is down - restarting...")
                if self.monitor.restart_service(service):
                    print(f"  ✓ {service} restarted")
        
        # Alert on critical issues
        if metrics['cpu'] > 90:
            level = self.alerter.escalate('high_cpu', 'high')
            self.alerter.send_email('Critical CPU Usage', f"CPU at {metrics['cpu']:.1f}%", level)
            self.alerter.send_webhook(f"CPU critical: {metrics['cpu']:.1f}%", level)
        
        if metrics['disk'] > 90:
            level = self.alerter.escalate('high_disk', 'critical')
            self.alerter.send_email('Critical Disk Usage', f"Disk at {metrics['disk']:.1f}%", level)
            self.alerter.send_webhook(f"Disk critical: {metrics['disk']:.1f}%", level)
    
    def run(self, interval=10, duration=None):
        """Run monitoring loop"""
        print("="*60)
        print("Intelligent Server Management Automation Suite")
        print("="*60)
        
        self.logger.log_event('system', 'Automation suite started')
        
        start = time.time()
        try:
            while True:
                self.run_cycle()
                
                if duration and (time.time() - start) > duration:
                    break
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n" + "="*60)
            print("Shutting down gracefully...")
            self.logger.log_event('system', 'Automation suite stopped')
            print(f"Logs: {self.logger.json_file}, {self.logger.csv_file}")
            print("="*60)

def main():
    config = {
        # Email config
        'email_enabled': False,
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'sender_email': 'zinaanjolaiya@gmail.com',
        'sender_password': 'raoo rjhr cbjp ngjy',
        'recipient_email': 'togundeji50@gmail.com',
        
        # Webhook config
        'webhook_url': '',  
        
        # Services to monitor (name: port)
        'services': {
            # 'nginx': 80,
            # 'postgresql': 5432,
        }
    }
    
    suite = ServerAutomationSuite(config)
    suite.run(interval=10)  # Check every 10 seconds

if __name__ == '__main__':
    main()