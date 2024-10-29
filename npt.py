'''
Network Performance Tester

Required libraries:
- scapy: For low-level packet manipulation (pip install scapy)
- speedtest-cli: For bandwidth testing (pip install speedtest-cli)
- ping3: For ICMP ping testing (pip install ping3)
- dnspython: For DNS resolution testing (pip install dnspython)

Additional system requirements:
- Must be run with root/administrator privileges for some tests

# Run all tests
    python npt.py
# Run specific tests
    python npt.py --metrics latency packet_loss
# Change target host and sample size:
    python npt.py --target google.com --samples 20
'''

import argparse
import logging
import time
import statistics
import json
from datetime import datetime
import socket
import dns.resolver
from ping3 import ping
import speedtest
from scapy.all import IP, TCP, sr1, conf
import sys
import signal
from contextlib import contextmanager
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('network_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class TimeoutException(Exception):
    pass

@contextmanager
def timeout(seconds):
    """Context manager for timeout"""
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    
    # Set the signal handler and a timeout
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        # Disable the alarm
        signal.alarm(0)

class NetworkTester:
    def __init__(self, target_host="8.8.8.8", sample_size=10):
        self.target_host = target_host
        self.sample_size = sample_size
        self.results = {}
        logging.info(f"Initializing NPT with target: {target_host}")

    def measure_latency(self):
        """Measure round-trip latency using ICMP ping"""
        try:
            latencies = []
            logging.info("Starting latency measurement...")
            
            for _ in range(self.sample_size):
                result = ping(self.target_host)
                if result is not None:
                    latencies.append(result * 1000)  # Convert to ms
                time.sleep(0.1)
            
            if latencies:
                avg_latency = statistics.mean(latencies)
                self.results['latency'] = {
                    'average_ms': round(avg_latency, 2),
                    'min_ms': round(min(latencies), 2),
                    'max_ms': round(max(latencies), 2)
                }
                logging.info(f"Latency measurement completed: {avg_latency:.2f}ms")
            else:
                raise Exception("No valid latency measurements")
                
        except Exception as e:
            logging.error(f"Latency measurement failed: {str(e)}")
            self.results['latency'] = None

    def measure_packet_loss(self):
        """Measure packet loss rate"""
        try:
            logging.info("Starting packet loss measurement...")
            sent = self.sample_size
            received = 0
            
            for _ in range(sent):
                if ping(self.target_host) is not None:
                    received += 1
                time.sleep(0.1)
            
            loss_rate = ((sent - received) / sent) * 100
            self.results['packet_loss'] = {
                'loss_rate_percent': round(loss_rate, 2),
                'packets_sent': sent,
                'packets_received': received
            }
            logging.info(f"Packet loss measurement completed: {loss_rate:.2f}%")
            
        except Exception as e:
            logging.error(f"Packet loss measurement failed: {str(e)}")
            self.results['packet_loss'] = None

    def measure_bandwidth(self):
        """Measure upload and download bandwidth"""
        try:
            logging.info("Starting bandwidth measurement...")
            
            # Initialize speedtest with specific configurations
            st = speedtest.Speedtest(secure=True)
            logging.info("Getting best server...")
            try:
                st.get_best_server()
            except Exception as e:
                logging.error(f"Error getting server: {str(e)}")
                raise Exception("Failed to find speedtest server")

            # Download speed
            logging.info("Measuring download speed...")
            try:
                download_speed = st.download() / 1_000_000  # Convert to Mbps
                download_speed = round(download_speed, 2)
                logging.info(f"Download speed: {download_speed} Mbps")
            except Exception as e:
                logging.error(f"Download test failed: {str(e)}")
                download_speed = None
                logging.info("Download speed measurement failed")

            # Upload speed
            logging.info("Measuring upload speed...")
            try:
                upload_speed = st.upload() / 1_000_000  # Convert to Mbps
                upload_speed = round(upload_speed, 2)
                logging.info(f"Upload speed: {upload_speed} Mbps")
            except Exception as e:
                logging.error(f"Upload test failed: {str(e)}")
                upload_speed = None
                logging.info("Upload speed measurement failed")

            # Store results
            self.results['bandwidth'] = {
                'download_mbps': download_speed,
                'upload_mbps': upload_speed
            }
            
            # Log completion with proper None handling
            logging.info("Bandwidth measurement completed: "
                        f"Down: {download_speed if download_speed is not None else 'Failed'} Mbps, "
                        f"Up: {upload_speed if upload_speed is not None else 'Failed'} Mbps")
            
        except Exception as e:
            logging.error(f"Bandwidth measurement failed: {str(e)}")
            self.results['bandwidth'] = {
                'download_mbps': None,
                'upload_mbps': None
            }

    def measure_jitter(self):
        """Measure jitter (variation in latency)"""
        try:
            logging.info("Starting jitter measurement...")
            latencies = []
            
            for _ in range(self.sample_size):
                result = ping(self.target_host)
                if result is not None:
                    latencies.append(result * 1000)
                time.sleep(0.1)
            
            if len(latencies) >= 2:
                differences = []
                for i in range(1, len(latencies)):
                    differences.append(abs(latencies[i] - latencies[i-1]))
                
                jitter = statistics.mean(differences)
                self.results['jitter'] = {
                    'average_ms': round(jitter, 2),
                    'min_ms': round(min(differences), 2),
                    'max_ms': round(max(differences), 2)
                }
                logging.info(f"Jitter measurement completed: {jitter:.2f}ms")
            else:
                raise Exception("Insufficient samples for jitter calculation")
                
        except Exception as e:
            logging.error(f"Jitter measurement failed: {str(e)}")
            self.results['jitter'] = None

    def measure_mtu_with_timeout(self):
        """Helper function to measure MTU with timeout"""
        mtu_size = 1500
        conf.verb = 0
        start_time = time.time()
        timeout_seconds = 10

        while mtu_size > 0:
            # Check if we've exceeded the timeout
            if time.time() - start_time > timeout_seconds:
                raise TimeoutException("MTU measurement timed out")

            packet = IP(dst=self.target_host)/TCP(dport=80)
            packet.load = "X" * (mtu_size - 40)  # Subtract IP and TCP header sizes
            
            reply = sr1(packet, timeout=1)
            if reply is not None:
                return mtu_size
                
            mtu_size -= 10

        return mtu_size

    def measure_mtu(self):
        """Measure Maximum Transmission Unit with timeout"""
        try:
            logging.info("Starting MTU measurement...")
            
            # Create a thread for MTU measurement
            mtu_thread = threading.Thread(target=lambda: self._measure_mtu_thread())
            mtu_thread.daemon = True  # Daemon thread will be killed when main thread exits
            
            # Start the thread and wait for timeout
            mtu_thread.start()
            mtu_thread.join(timeout=10)  # Wait for 10 seconds
            
            if mtu_thread.is_alive():
                logging.error("MTU measurement timed out after 10 seconds")
                self.results['mtu'] = None
                return
            
            # If we got here, the measurement completed successfully
            if 'mtu' not in self.results:
                logging.error("MTU measurement failed without producing results")
                self.results['mtu'] = None
            
        except Exception as e:
            logging.error(f"MTU measurement failed: {str(e)}")
            self.results['mtu'] = None

    def _measure_mtu_thread(self):
        """Thread function for MTU measurement"""
        try:
            mtu_size = self.measure_mtu_with_timeout()
            self.results['mtu'] = {
                'size_bytes': mtu_size
            }
            logging.info(f"MTU measurement completed: {mtu_size} bytes")
        except Exception as e:
            logging.error(f"MTU thread measurement failed: {str(e)}")
            self.results['mtu'] = None

    def measure_dns_resolution(self):
        """Measure DNS resolution time"""
        try:
            logging.info("Starting DNS resolution time measurement...")
            resolver = dns.resolver.Resolver()
            domains = ['google.com', 'microsoft.com', 'amazon.com']
            resolution_times = []
            
            for domain in domains:
                start_time = time.time()
                resolver.resolve(domain)
                resolution_time = (time.time() - start_time) * 1000
                resolution_times.append(resolution_time)
            
            avg_resolution_time = statistics.mean(resolution_times)
            self.results['dns_resolution'] = {
                'average_ms': round(avg_resolution_time, 2),
                'min_ms': round(min(resolution_times), 2),
                'max_ms': round(max(resolution_times), 2)
            }
            logging.info(f"DNS resolution measurement completed: {avg_resolution_time:.2f}ms")
            
        except Exception as e:
            logging.error(f"DNS resolution measurement failed: {str(e)}")
            self.results['dns_resolution'] = None

    def save_report(self, filename=None):
        """Save the test results to a JSON file"""
        if filename is None:
            filename = f"network_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=4)
            logging.info(f"Report saved to {filename}")
        except Exception as e:
            logging.error(f"Failed to save report: {str(e)}")

    def print_report(self):
        """Print the test results in a readable format"""
        print("\n=== Network Performance Test Report ===")
        for metric, data in self.results.items():
            print(f"\n{metric.upper()}:")
            if data is not None:
                for key, value in data.items():
                    print(f"  {key}: {value}")
            else:
                print("  Test failed or not executed")
        print("\n=====================================")

def main():
    parser = argparse.ArgumentParser(description="Network Performance Tester")
    parser.add_argument("--target", default="8.8.8.8", help="Target host for testing")
    parser.add_argument("--samples", type=int, default=10, help="Number of samples for tests")
    parser.add_argument("--metrics", nargs='+', choices=[
        'latency', 'packet_loss', 'bandwidth', 'jitter', 'mtu', 'dns'
    ], help="Specific metrics to test")
    args = parser.parse_args()

    tester = NetworkTester(args.target, args.samples)
    
    # Map of metric names to their corresponding methods
    metric_methods = {
        'latency': tester.measure_latency,
        'packet_loss': tester.measure_packet_loss,
        'bandwidth': tester.measure_bandwidth,
        'jitter': tester.measure_jitter,
        'mtu': tester.measure_mtu,
        'dns': tester.measure_dns_resolution
    }

    # If specific metrics are requested, run only those
    if args.metrics:
        for metric in args.metrics:
            metric_methods[metric]()
    else:
        # Run all tests
        for method in metric_methods.values():
            method()

    tester.print_report()
    tester.save_report()

if __name__ == "__main__":
    main()
