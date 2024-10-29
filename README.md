
### **Network Performance Tester (NPT)**

**This is a network performance tester tool that collects the following metrics:**

 - **Latency:** This is the time it takes for a data packet to travel from its source to its destination. *High latency can lead to delays in applications, especially those that require real-time interaction like online gaming or video conferencing.*
 - **Packet Loss:** This occurs when data packets fail to reach their destination. *Packet loss can lead to interruptions in data
   transmission, causing issues like audio dropouts or video freezes.*
 - **Bandwidth Usage:** This refers to the amount of data that can be transferred over a network connection in a specific amount of time.  *Insufficient bandwidth can lead to slowdowns, especially when multiple devices are using the network simultaneously or when transferring large files.*
 - **Jitter:** Measures the variation in delay of data packets. *High jitter can lead to audio and video quality issues.*
 - **Throughput:** Measures the amount of data that can be transferred over a network in a given period. *It's important for applications that require high data transfer rates, such as file transfers and video streaming.*
 - **Packet Reordering:** Measures the number of packets that arrive out of order. *This can impact the performance of applications that rely on the order of packets, such as VoIP and video conferencing.*
 - **MTU (Maximum Transmission Unit):** The largest size of an IP packet that can be transmitted over a network. *A small MTU can limit the amount of data that can be transferred in a single packet, reducing network performance.*
 - **DNS Resolution Time:** The time it takes to resolve a domain name to an IP address. *Slow DNS resolution can impact website loading times and overall network performance.*

**After it has collected all the metrics it will generate a JSON file (`network_test_report.json`) with the results.**

**How to use:**
 - Run all tests: `python npt.py`

 - Run specific metrics: `python npt.py --metrics latency packet_loss`

 - Change target host and sample size: `python npt.py --target google.com --samples 20`

**Installation:**

 - **Windows:** 
 Npcap (https://npcap.com/) needs to be installed for Scapy to work

   ```bash
   pip install scapy speedtest-cli ping3 dnspython
   ```

 - **Debian:**

   ```bash
    sudo apt-get install python3-dev libpcap-dev
    pip install scapy speedtest-cli ping3 dnspython
   ```

 - **CentOS/RHEL:**

   ```bash
    sudo yum install python3-devel libpcap-devel
    pip install scapy speedtest-cli ping3 dnspython
   ```

 - **Additional requirements:**
   - Root/Administrator privileges may be required for some tests

**Example log:**


    python npt.py --target google.com --samples 20

    2024-10-29 11:42:48,048 - INFO - Initializing NetworkTester with target: google.com
    2024-10-29 11:42:48,049 - INFO - Starting latency measurement...
    2024-10-29 11:42:50,226 - INFO - Latency measurement completed: 2.55ms
    2024-10-29 11:42:50,227 - INFO - Starting packet loss measurement...
    2024-10-29 11:42:52,397 - INFO - Packet loss measurement completed: 0.00%
    2024-10-29 11:42:52,398 - INFO - Starting bandwidth measurement...
    2024-10-29 11:42:52,543 - INFO - Getting best server...
    2024-10-29 11:42:53,015 - INFO - Measuring download speed...
    2024-10-29 11:42:59,845 - INFO - Download speed: 479.55 Mbps
    2024-10-29 11:42:59,846 - INFO - Measuring upload speed...
    2024-10-29 11:43:01,821 - INFO - Upload speed: 690.2 Mbps
    2024-10-29 11:43:01,822 - INFO - Bandwidth measurement completed: Down: 479.55 Mbps, Up: 690.2 Mbps
    2024-10-29 11:43:01,823 - INFO - Starting jitter measurement...
    2024-10-29 11:43:03,993 - INFO - Jitter measurement completed: 1.77ms
    2024-10-29 11:43:03,994 - INFO - Starting MTU measurement...
    2024-10-29 11:43:04,003 - INFO - MTU measurement completed: 1500 bytes
    2024-10-29 11:43:04,004 - INFO - Starting DNS resolution time measurement...
    2024-10-29 11:43:04,519 - INFO - DNS resolution measurement completed: 2.07ms
