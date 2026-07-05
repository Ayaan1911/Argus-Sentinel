import os
import json
from datetime import datetime

base_dir = r"d:\Projects\Argus-Sentinel\argus-intelligence"

def write_json(path, data):
    data['version'] = "1.0"
    data['last_updated'] = "2026-07-05"
    data['reviewed_by'] = "argus-team"
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def gen_services():
    services = {
        "ftp": {
            "service": "FTP", "port": 21, "protocol": "TCP",
            "purpose": "File Transfer Protocol for moving files between systems.",
            "risk_level": "Medium",
            "description": "FTP is an unencrypted file transfer protocol. Credentials and data are sent in plaintext unless FTPS is used.",
            "common_risks": ["plaintext credentials", "anonymous login", "unencrypted data"],
            "misconfigurations": ["anonymous access enabled", "weak passwords", "outdated vsftpd/proftpd"],
            "attack_patterns": ["credential sniffing", "brute force", "anonymous file upload/RCE"],
            "real_world_incidents": ["Data exfiltration via anonymous FTP access on misconfigured servers."],
            "recommended_actions": ["Disable FTP and use SFTP instead.", "Disable anonymous login.", "Enforce strong credentials.", "Restrict IP access."],
            "audience_guidance": {
                "student": "FTP sends passwords in clear text. Think of it like shouting a password across a crowded room.",
                "developer": "Migrate from FTP to SFTP (SSH File Transfer Protocol). Ensure your FTP daemon (e.g., vsftpd) has anonymous_enable=NO.",
                "bug_bounty_hunter": "Check for anonymous login using 'anonymous' / 'anonymous@example.com'. Look for sensitive files or write access.",
                "pentester": "Attempt anonymous login. Sniff traffic if on the same network. Look for exploit modules for the specific FTP daemon version.",
                "security_team": "Monitor for FTP cleartext authentications. Enforce SFTP globally. Restrict FTP ports at the firewall."
            },
            "correlation_rules": {"amplifies": ["anonymous_login", "internet_facing"], "requires": ["network_exposure"], "mitigates": ["sftp_used", "ip_restricted"]},
            "learning_resources": ["https://owasp.org/www-community/vulnerabilities/Cleartext_Transmission_of_Sensitive_Information"],
            "related_findings": ["weak_credentials"],
            "mitre_attack": ["T1040", "T1110"],
            "risk_weight": 5
        },
        "telnet": {
            "service": "Telnet", "port": 23, "protocol": "TCP",
            "purpose": "Unencrypted remote administration.",
            "risk_level": "Critical",
            "description": "Telnet provides a bidirectional interactive text-oriented communication facility using a virtual terminal connection.",
            "common_risks": ["plaintext credentials", "network sniffing"],
            "misconfigurations": ["exposed to internet", "default credentials"],
            "attack_patterns": ["credential sniffing", "brute force", "Mirai botnet targeting"],
            "real_world_incidents": ["IoT devices commonly compromised via exposed Telnet with default credentials (e.g., Mirai botnet)."],
            "recommended_actions": ["Disable Telnet completely.", "Replace with SSH.", "Block port 23 at edge firewall."],
            "audience_guidance": {
                "student": "Telnet is an ancient, completely insecure way to log into servers. It should never be used today.",
                "developer": "Disable the Telnet daemon immediately and configure SSH instead.",
                "bug_bounty_hunter": "Check for default credentials (admin/admin, root/root) if you find this on an IoT or legacy device.",
                "pentester": "Sniff traffic to capture cleartext passwords. Brute force default IoT credentials.",
                "security_team": "Create an alert for any Telnet traffic crossing the network boundary. Isolate legacy devices requiring Telnet."
            },
            "correlation_rules": {"amplifies": ["internet_facing", "default_credentials"], "requires": ["network_exposure"], "mitigates": []},
            "learning_resources": ["https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-1999-0619"],
            "related_findings": ["weak_credentials"],
            "mitre_attack": ["T1040"],
            "risk_weight": 9
        },
        "rdp": {
            "service": "RDP", "port": 3389, "protocol": "TCP",
            "purpose": "Remote Desktop Protocol for Windows GUI access.",
            "risk_level": "High",
            "description": "Proprietary protocol developed by Microsoft, which provides a user with a graphical interface to connect to another computer.",
            "common_risks": ["brute force", "BlueKeep", "credential theft"],
            "misconfigurations": ["internet facing", "NLA disabled", "weak passwords"],
            "attack_patterns": ["brute force", "ransomware deployment", "exploit public CVEs (e.g. BlueKeep)"],
            "real_world_incidents": ["Primary initial access vector for countless ransomware campaigns targeting Windows domains."],
            "recommended_actions": ["Enable Network Level Authentication (NLA).", "Place behind a VPN or RD Gateway.", "Enforce MFA.", "Restrict IP access.", "Lock out after failed attempts."],
            "audience_guidance": {
                "student": "RDP lets you control a Windows PC remotely. Leaving it open to the internet is a common way hackers spread ransomware.",
                "developer": "Ensure Network Level Authentication (NLA) is required. Never expose 3389 directly to the internet.",
                "bug_bounty_hunter": "Check for NLA status. If NLA is disabled, the server is much more vulnerable to exploitation.",
                "pentester": "Check for BlueKeep vulnerability. Brute force credentials. Use Nmap scripts to check supported encryption levels.",
                "security_team": "Block 3389 at the perimeter. Require VPN or Zero Trust Network Access (ZTNA) for RDP. Enforce MFA via Duo or similar."
            },
            "correlation_rules": {"amplifies": ["nla_disabled", "internet_facing"], "requires": ["network_exposure"], "mitigates": ["vpn_required", "nla_enabled", "mfa_enabled"]},
            "learning_resources": ["https://www.cisa.gov/news-events/alerts/2019/11/05/understanding-and-mitigating-russian-state-sponsored-cyber-threats"],
            "related_findings": ["weak_credentials"],
            "mitre_attack": ["T1133", "T1021.001"],
            "risk_weight": 8
        },
        "smb": {
            "service": "SMB", "port": 445, "protocol": "TCP",
            "purpose": "Server Message Block for file and printer sharing.",
            "risk_level": "Critical",
            "description": "SMB operates as an application-layer network protocol mainly used for providing shared access to files, printers, and serial ports.",
            "common_risks": ["EternalBlue", "null sessions", "SMB relay", "ransomware propagation"],
            "misconfigurations": ["internet facing", "SMBv1 enabled", "null sessions allowed", "message signing disabled"],
            "attack_patterns": ["EternalBlue (MS17-010)", "SMB Relay", "lateral movement", "data exfiltration"],
            "real_world_incidents": ["WannaCry and NotPetya ransomware spread globally using the EternalBlue SMBv1 exploit."],
            "recommended_actions": ["Disable SMBv1 completely.", "Block port 445 at edge firewalls.", "Require SMB signing.", "Disable null sessions.", "Patch Windows systems."],
            "audience_guidance": {
                "student": "SMB shares files on Windows. If exposed, hackers can use exploits like EternalBlue to take over the computer instantly.",
                "developer": "Ensure SMBv1 is disabled in the registry. Never expose port 445 to the WAN.",
                "bug_bounty_hunter": "Check for null sessions using smbclient or CrackMapExec. Check if SMBv1 is enabled.",
                "pentester": "Run MS17-010 checks. Attempt anonymous login to list shares. Perform SMB relay attacks if signing is disabled.",
                "security_team": "Monitor for lateral movement on port 445. Ensure SMB signing is enforced via GPO. Continuously audit for SMBv1."
            },
            "correlation_rules": {"amplifies": ["smbv1_enabled", "internet_facing", "null_sessions"], "requires": ["network_exposure"], "mitigates": ["smb_signing", "smbv3_only"]},
            "learning_resources": ["https://techcommunity.microsoft.com/t5/storage-at-microsoft/stop-using-smb1/ba-p/425858"],
            "related_findings": ["eternalblue", "null_session"],
            "mitre_attack": ["T1021.002", "T1569.002"],
            "risk_weight": 9
        },
        "postgresql": {
            "service": "PostgreSQL", "port": 5432, "protocol": "TCP",
            "purpose": "Open-source relational database.",
            "risk_level": "High",
            "description": "PostgreSQL is a powerful, open source object-relational database system.",
            "common_risks": ["brute force", "data exposure", "RCE via COPY FROM PROGRAM"],
            "misconfigurations": ["internet facing", "default credentials", "trust authentication enabled in pg_hba.conf"],
            "attack_patterns": ["brute force", "SQL injection pivot", "command execution via superuser"],
            "real_world_incidents": ["Databases held for ransom after attackers brute-forced exposed instances."],
            "recommended_actions": ["Restrict access to local network or specific IPs.", "Disable 'trust' authentication.", "Enforce strong passwords.", "Use SSL for connections."],
            "audience_guidance": {
                "student": "Databases hold all an app's sensitive info. They should never be directly accessible from the internet.",
                "developer": "Configure pg_hba.conf to only allow internal IPs. Require md5/scram-sha-256 auth, never 'trust'.",
                "bug_bounty_hunter": "Check for default postgres/postgres credentials. If connected, attempt to read files or execute commands using COPY.",
                "pentester": "Brute force credentials. If superuser, escalate to RCE using the COPY FROM PROGRAM feature.",
                "security_team": "Ensure databases are in private subnets. Monitor for repeated connection failures indicating brute force."
            },
            "correlation_rules": {"amplifies": ["internet_facing", "default_credentials"], "requires": ["network_exposure"], "mitigates": ["ip_restricted", "ssl_required"]},
            "learning_resources": ["https://www.postgresql.org/docs/current/auth-pg-hba-conf.html"],
            "related_findings": ["weak_credentials"],
            "mitre_attack": ["T1190", "T1059"],
            "risk_weight": 8
        },
        "mongodb": {
            "service": "MongoDB", "port": 27017, "protocol": "TCP",
            "purpose": "NoSQL document database.",
            "risk_level": "Critical",
            "description": "MongoDB is a source-available cross-platform document-oriented database program.",
            "common_risks": ["unauthenticated access", "data exfiltration", "ransom"],
            "misconfigurations": ["no authentication enabled (default in older versions)", "exposed to internet"],
            "attack_patterns": ["data wiping", "ransom note insertion", "data theft"],
            "real_world_incidents": ["Tens of thousands of exposed MongoDB databases wiped and held for ransom by automated scripts."],
            "recommended_actions": ["Enable authentication (--auth).", "Bind to localhost/private IP.", "Configure firewall rules."],
            "audience_guidance": {
                "student": "Older versions of MongoDB didn't require a password by default. Hackers love finding these to steal data and demand ransom.",
                "developer": "Always start mongod with --auth. Edit mongod.conf to bind_ip 127.0.0.1 or your private VPC IP.",
                "bug_bounty_hunter": "Attempt to connect without credentials. If successful, you have full access to dump the database.",
                "pentester": "Connect via mongo shell. Check for sensitive data. Do NOT modify data during testing.",
                "security_team": "Scan internal network for unauthenticated MongoDB instances. Ensure security groups block 27017 externally."
            },
            "correlation_rules": {"amplifies": ["unauthenticated", "internet_facing"], "requires": ["network_exposure"], "mitigates": ["auth_enabled", "ip_restricted"]},
            "learning_resources": ["https://www.mongodb.com/docs/manual/administration/security-checklist/"],
            "related_findings": ["unauthenticated_access"],
            "mitre_attack": ["T1190", "T1486"],
            "risk_weight": 9
        },
        "elasticsearch": {
            "service": "Elasticsearch", "port": 9200, "protocol": "TCP",
            "purpose": "Distributed search and analytics engine.",
            "risk_level": "Critical",
            "description": "Elasticsearch is a distributed, RESTful search and analytics engine capable of addressing a growing number of use cases.",
            "common_risks": ["unauthenticated data access", "data exfiltration", "RCE via scripting"],
            "misconfigurations": ["no authentication (X-Pack disabled)", "exposed to internet", "dynamic scripting enabled"],
            "attack_patterns": ["data theft", "ransom", "RCE via MVEL/Groovy (older versions)"],
            "real_world_incidents": ["Massive data leaks involving PII exposed via unsecured Elasticsearch clusters."],
            "recommended_actions": ["Enable Elastic Security (X-Pack).", "Require authentication for all REST endpoints.", "Restrict network access via firewall."],
            "audience_guidance": {
                "student": "Elasticsearch stores massive amounts of logs and data. Like MongoDB, if exposed without auth, it's a goldmine for attackers.",
                "developer": "Enable X-Pack security in elasticsearch.yml. Setup RBAC and require passwords for the elastic user.",
                "bug_bounty_hunter": "Access /_cat/indices to see all data. Access /_search to dump contents.",
                "pentester": "Check for unauthenticated access. On older versions (<1.2), check for RCE via dynamic scripting features.",
                "security_team": "Ensure clusters are not internet-facing. Audit for X-Pack enablement. Alert on large data extraction queries."
            },
            "correlation_rules": {"amplifies": ["unauthenticated", "internet_facing"], "requires": ["network_exposure"], "mitigates": ["xpack_enabled", "ip_restricted"]},
            "learning_resources": ["https://www.elastic.co/guide/en/elasticsearch/reference/current/security-minimal-setup.html"],
            "related_findings": ["unauthenticated_access", "information_disclosure"],
            "mitre_attack": ["T1190"],
            "risk_weight": 9
        },
        "dns": {
            "service": "DNS", "port": 53, "protocol": "UDP/TCP",
            "purpose": "Domain Name System resolution.",
            "risk_level": "Medium",
            "description": "The Domain Name System translates human-readable domain names to machine-readable IP addresses.",
            "common_risks": ["zone transfer", "cache poisoning", "DNS amplification"],
            "misconfigurations": ["AXFR enabled for anyone", "open resolver", "outdated BIND"],
            "attack_patterns": ["Zone Transfer (AXFR)", "DDoS amplification", "DNS spoofing"],
            "real_world_incidents": ["Open DNS resolvers abused for massive DDoS amplification attacks against internet infrastructure."],
            "recommended_actions": ["Restrict Zone Transfers (AXFR) to trusted IPs.", "Disable recursive queries for external clients (close the open resolver).", "Keep DNS software patched."],
            "audience_guidance": {
                "student": "DNS is the phonebook of the internet. If misconfigured, an attacker can ask for the 'whole phonebook' (zone transfer) and see all hidden servers.",
                "developer": "Ensure your DNS server (e.g., BIND) only allows AXFR transfers to secondary nameservers. Disable recursion for untrusted IPs.",
                "bug_bounty_hunter": "Attempt a zone transfer (dig axfr @server domain). Look for hidden subdomains and internal hostnames.",
                "pentester": "Test for AXFR. Check if the server acts as an open resolver for DDoS amplification.",
                "security_team": "Monitor for AXFR requests from untrusted IPs. Scan external footprint for open resolvers."
            },
            "correlation_rules": {"amplifies": ["axfr_enabled", "open_resolver"], "requires": ["network_exposure"], "mitigates": ["recursion_disabled"]},
            "learning_resources": ["https://owasp.org/www-community/attacks/DNS_Zone_Transfer"],
            "related_findings": ["zone_transfer_allowed"],
            "mitre_attack": ["T1590", "T1498"],
            "risk_weight": 5
        },
        "snmp": {
            "service": "SNMP", "port": 161, "protocol": "UDP",
            "purpose": "Simple Network Management Protocol for monitoring.",
            "risk_level": "High",
            "description": "SNMP is used for collecting information from, and configuring, network devices, such as servers, printers, hubs, switches, and routers.",
            "common_risks": ["information disclosure", "device configuration changes"],
            "misconfigurations": ["default community strings (public/private)", "SNMPv1 or v2c enabled (unencrypted)"],
            "attack_patterns": ["SNMP walking to extract routing tables, running processes, and OS info", "writing config changes via 'private' string"],
            "real_world_incidents": ["Attackers mapped internal networks and compromised routers by querying exposed SNMP services with default strings."],
            "recommended_actions": ["Use SNMPv3 with authentication and encryption.", "Change default community strings.", "Restrict SNMP access to management IPs via ACLs."],
            "audience_guidance": {
                "student": "SNMP manages devices. Older versions use a 'community string' like a password. If it's the default ('public'), attackers can read device info.",
                "developer": "Upgrade to SNMPv3. If v2c must be used, change community strings from 'public' and 'private' to strong, unique values.",
                "bug_bounty_hunter": "Use snmpwalk with community string 'public'. Look for sensitive internal IPs, running software versions, or usernames.",
                "pentester": "Extract MIB data. If 'private' string is found, attempt to modify device configuration or routing tables.",
                "security_team": "Audit network for SNMPv1/v2c. Enforce SNMPv3. Ensure SNMP traffic is isolated to management VLANs."
            },
            "correlation_rules": {"amplifies": ["default_community_string", "internet_facing"], "requires": ["network_exposure"], "mitigates": ["snmpv3_used"]},
            "learning_resources": ["https://csrc.nist.gov/glossary/term/simple_network_management_protocol"],
            "related_findings": ["default_credentials", "information_disclosure"],
            "mitre_attack": ["T1046", "T1082"],
            "risk_weight": 7
        },
        "vnc": {
            "service": "VNC", "port": 5900, "protocol": "TCP",
            "purpose": "Virtual Network Computing for graphical desktop sharing.",
            "risk_level": "High",
            "description": "VNC is a graphical desktop-sharing system that uses the Remote Frame Buffer protocol to remotely control another computer.",
            "common_risks": ["brute force", "unencrypted keystrokes", "unauthenticated access"],
            "misconfigurations": ["internet facing", "no password", "weak password (max 8 chars in standard VNC)"],
            "attack_patterns": ["brute force", "credential theft", "unauthenticated desktop takeover"],
            "real_world_incidents": ["Attackers frequently scan for open VNC ports without passwords to instantly compromise industrial control systems (ICS) and servers."],
            "recommended_actions": ["Require strong passwords.", "Tunnel VNC over SSH.", "Block port 5900 at edge firewalls."],
            "audience_guidance": {
                "student": "VNC shares a screen. If left open without a password, anyone can click around on the computer.",
                "developer": "Never expose VNC directly. Always tunnel it through SSH (e.g., ssh -L 5900:localhost:5900).",
                "bug_bounty_hunter": "Attempt to connect. Many VNC instances are misconfigured to require no password.",
                "pentester": "Check for unauthenticated access. Brute force passwords (note: standard VNC truncates passwords to 8 characters).",
                "security_team": "Block 5900-5910 at the perimeter. Monitor internal networks for unauthorized VNC servers."
            },
            "correlation_rules": {"amplifies": ["unauthenticated", "internet_facing"], "requires": ["network_exposure"], "mitigates": ["tunneled_via_ssh"]},
            "learning_resources": ["https://owasp.org/www-project-top-ten/"],
            "related_findings": ["unauthenticated_access"],
            "mitre_attack": ["T1021.005"],
            "risk_weight": 8
        }
    }
    for k, v in services.items():
        write_json(os.path.join(base_dir, "services", f"{k}.json"), v)

def gen_tech():
    tech = {
        "nodejs": {
            "technology": "Node.js", "type": "Runtime",
            "purpose": "JavaScript runtime environment.",
            "description": "Node.js is an open-source, cross-platform, back-end JavaScript runtime environment.",
            "common_risks": ["RCE via deserialization", "prototype pollution", "DoS via event loop blocking"],
            "mitigations": ["Use up-to-date packages", "avoid eval()", "use strict mode"],
            "audience_guidance": {
                "student": "Node.js runs JavaScript on the server. If it trusts bad input, attackers can crash it or run malicious code.",
                "developer": "Audit dependencies using 'npm audit'. Avoid vulnerable patterns like prototype pollution or insecure deserialization.",
                "bug_bounty_hunter": "Look for stack traces disclosing Node.js paths. Test for Prototype Pollution in JSON bodies.",
                "pentester": "Check for Node.js specific vulnerabilities like Prototype Pollution or untrusted deserialization (e.g., node-serialize).",
                "security_team": "Ensure CI/CD pipelines include SCA (Software Composition Analysis) to catch vulnerable npm packages."
            },
            "learning_resources": ["https://cheatsheetseries.owasp.org/cheatsheets/Nodejs_Security_Cheat_Sheet.html"]
        },
        "django": {
            "technology": "Django", "type": "Framework",
            "purpose": "High-level Python web framework.",
            "description": "Django is a free and open-source web framework that follows the model-template-views architectural pattern.",
            "common_risks": ["DEBUG mode enabled", "misconfigured ALLOWED_HOSTS", "secret key exposure"],
            "mitigations": ["Set DEBUG=False in production", "Secure SECRET_KEY", "Configure ALLOWED_HOSTS"],
            "audience_guidance": {
                "student": "Django builds web apps quickly. If 'DEBUG' is left on, it shows attackers detailed error screens with sensitive info.",
                "developer": "Ensure DEBUG=False in production settings. Keep SECRET_KEY out of version control. Set SECURE_SSL_REDIRECT=True.",
                "bug_bounty_hunter": "Trigger a 404 or 500 error to see if Django's yellow debug page is enabled. This leaks settings and environment variables.",
                "pentester": "Look for exposed /admin panels. If DEBUG is True, exploit information disclosure.",
                "security_team": "Enforce automated checks that reject PRs with DEBUG=True in production settings."
            },
            "learning_resources": ["https://docs.djangoproject.com/en/stable/howto/deployment/checklist/"]
        },
        "php": {
            "technology": "PHP", "type": "Language",
            "purpose": "Server-side scripting language.",
            "description": "PHP is a popular general-purpose scripting language that is especially suited to web development.",
            "common_risks": ["LFI/RFI", "RCE via unsafe functions (exec, system)", "SQLi in legacy code"],
            "mitigations": ["Use prepared statements", "disable dangerous functions in php.ini", "keep PHP updated"],
            "audience_guidance": {
                "student": "PHP powers many websites. Older PHP code often mixes data and commands, leading to easily hackable sites.",
                "developer": "Always use PDO with prepared statements. Disable dangerous functions like exec() and passthru() in php.ini.",
                "bug_bounty_hunter": "Test for Local File Inclusion (LFI) in URL parameters (e.g., ?page=../../etc/passwd). Look for exposed phpinfo() pages.",
                "pentester": "Search for exposed phpinfo.php. Test file upload forms for unrestricted PHP script uploads (.php, .phtml).",
                "security_team": "Ensure servers are running supported PHP versions (8.x). Audit legacy codebases for unparameterized SQL queries."
            },
            "learning_resources": ["https://phptherightway.com/#security"]
        },
        "iis": {
            "technology": "IIS", "type": "Web Server",
            "purpose": "Microsoft web server.",
            "description": "Internet Information Services (IIS) is an extensible web server software created by Microsoft for use with the Windows NT family.",
            "common_risks": ["Tilde enumeration", "directory traversal", "misconfigured Web.config"],
            "mitigations": ["Disable short file names (8.3)", "restrict directory browsing", "keep patched"],
            "audience_guidance": {
                "student": "IIS is Microsoft's web server. Misconfigurations can allow attackers to guess hidden file names or access system files.",
                "developer": "Ensure custom error pages are configured to prevent stack trace leaks. Secure Web.config.",
                "bug_bounty_hunter": "Test for IIS tilde (~) short name enumeration to find hidden files and directories.",
                "pentester": "Check for IIS short name enumeration. Look for Web.config leaks or improper authorization via path traversal.",
                "security_team": "Disable 8.3 short names on IIS servers via registry. Ensure detailed errors are only sent to localhost."
            },
            "learning_resources": ["https://docs.microsoft.com/en-us/iis/manage/configuring-security/"]
        },
        "kubernetes": {
            "technology": "Kubernetes", "type": "Orchestrator",
            "purpose": "Container orchestration system.",
            "description": "Kubernetes is an open-source container orchestration system for automating software deployment, scaling, and management.",
            "common_risks": ["unauthenticated API server", "exposed Kubelet API", "overly permissive RBAC", "secrets in plaintext"],
            "mitigations": ["Enable RBAC", "disable anonymous auth", "use network policies", "secure etcd"],
            "audience_guidance": {
                "student": "Kubernetes manages containers. If its control panel is exposed, attackers can take over all the apps running inside.",
                "developer": "Do not hardcode secrets; use Kubernetes Secrets or Vault. Apply least privilege RBAC to ServiceAccounts.",
                "bug_bounty_hunter": "Look for exposed kube-apiserver on port 6443 or Kubelet on 10250. Test anonymous access.",
                "pentester": "Attempt unauthenticated Kubelet exec (port 10250). If you compromise a pod, check the mounted ServiceAccount token.",
                "security_team": "Ensure the API server is not exposed to the internet. Implement strict NetworkPolicies. Audit RBAC regularly."
            },
            "learning_resources": ["https://kubernetes.io/docs/concepts/security/"]
        },
        "docker": {
            "technology": "Docker", "type": "Container Runtime",
            "purpose": "Containerization platform.",
            "description": "Docker is a set of platform as a service products that use OS-level virtualization to deliver software in packages called containers.",
            "common_risks": ["exposed Docker daemon API", "running as root", "privileged containers"],
            "mitigations": ["Do not expose docker.sock", "use rootless mode", "drop capabilities"],
            "audience_guidance": {
                "student": "Docker runs apps in isolated boxes. If the Docker API is exposed, attackers can create their own boxes to take over the host.",
                "developer": "Use USER instructions in Dockerfile to avoid running as root. Never mount /var/run/docker.sock into a container if avoidable.",
                "bug_bounty_hunter": "Scan for port 2375 or 2376. An exposed unauthenticated Docker API means instant root on the host.",
                "pentester": "Exploit exposed Docker APIs to deploy a privileged container and mount the host filesystem for RCE.",
                "security_team": "Ensure Docker APIs are never exposed over TCP without mTLS. Audit images for vulnerabilities."
            },
            "learning_resources": ["https://docs.docker.com/engine/security/"]
        }
    }
    for k, v in tech.items():
        write_json(os.path.join(base_dir, "technologies", f"{k}.json"), v)

def gen_vulns():
    vulns = {
        "exposed_admin_panel": {
            "vulnerability_class": "Exposed Admin Panel",
            "description": "Administrative interfaces accessible to unauthorized users or the public internet.",
            "severity": "High",
            "impact": "Attackers can brute-force credentials, exploit unpatched flaws, or leverage default passwords to gain full control.",
            "remediation": ["Restrict access via IP allowlisting.", "Place behind a VPN or Zero Trust proxy.", "Require MFA."],
            "audience_guidance": {
                "student": "Admin panels are the keys to the kingdom. If they are on the internet, attackers will try to guess the password.",
                "developer": "Move admin routes (e.g., /admin, /wp-admin) behind an authentication proxy or IP restriction. Enforce MFA.",
                "bug_bounty_hunter": "Check for default credentials (admin/admin). Look for authorization bypasses (e.g., forced browsing).",
                "pentester": "Attempt brute force. Exploit known vulnerabilities for the specific CMS/framework admin panel.",
                "security_team": "Scan external perimeter for admin interfaces. Ensure they are protected by WAF and access policies."
            },
            "learning_resources": ["https://cwe.mitre.org/data/definitions/284.html"]
        },
        "directory_listing": {
            "vulnerability_class": "Directory Listing Enabled",
            "description": "Web server is configured to list the contents of a directory when no index file is present.",
            "severity": "Low",
            "impact": "Information disclosure. Attackers can view hidden files, backups, configuration files, or source code.",
            "remediation": ["Disable directory browsing in web server configuration (e.g., Options -Indexes in Apache).", "Ensure index files (index.html, index.php) are present."],
            "audience_guidance": {
                "student": "Directory listing shows all files in a folder like a file browser. It helps attackers find files they shouldn't see.",
                "developer": "Configure your web server to deny directory listings. In Apache, remove the 'Indexes' directive.",
                "bug_bounty_hunter": "Browse the listed files for sensitive data: .env files, backup archives (.zip, .bak), or source code.",
                "pentester": "Automate downloading of all listed files. Search for hardcoded credentials or API keys.",
                "security_team": "Enforce secure defaults in web server base images that explicitly disable directory listing."
            },
            "learning_resources": ["https://cwe.mitre.org/data/definitions/548.html"]
        },
        "info_disclosure_debug": {
            "vulnerability_class": "Information Disclosure (Debug Endpoint)",
            "description": "Exposure of application debug, diagnostic, or status endpoints to unauthorized users.",
            "severity": "Medium",
            "impact": "Leaks sensitive environment variables, internal IP addresses, stack traces, and software versions.",
            "remediation": ["Disable debug mode in production.", "Restrict access to diagnostic endpoints (e.g., /actuator/env) to internal IPs or authenticated admins."],
            "audience_guidance": {
                "student": "Debug pages show how the app works behind the scenes. This gives hackers a blueprint to find deeper flaws.",
                "developer": "Turn off framework debug modes (e.g., Django DEBUG=False, Spring Boot Actuator security). Never expose /server-status.",
                "bug_bounty_hunter": "Look for Spring Boot Actuators, Django yellow screens, or PHP debug outputs. Extract secrets and API keys from the output.",
                "pentester": "Check if debug endpoints allow modification (e.g., Spring Boot /actuator/env allows changing properties leading to RCE).",
                "security_team": "Monitor for external access to known debug paths. Audit production configurations for debugging flags."
            },
            "learning_resources": ["https://cwe.mitre.org/data/definitions/200.html"]
        },
        "missing_security_headers": {
            "vulnerability_class": "Missing Security Headers",
            "description": "Web application does not implement standard HTTP security headers.",
            "severity": "Low",
            "impact": "Leaves users vulnerable to client-side attacks like Clickjacking, Cross-Site Scripting (XSS), and MIME-sniffing.",
            "remediation": ["Implement Content-Security-Policy (CSP).", "Set X-Frame-Options to DENY or SAMEORIGIN.", "Set Strict-Transport-Security (HSTS).", "Set X-Content-Type-Options to nosniff."],
            "audience_guidance": {
                "student": "Security headers are instructions to the browser to protect the user from certain types of attacks, like being tricked into clicking a hidden button.",
                "developer": "Add CSP, HSTS, X-Frame-Options, and X-Content-Type-Options headers to your web server or application middleware.",
                "bug_bounty_hunter": "Note the missing headers. Look for Clickjacking if X-Frame-Options is missing, or XSS if CSP is absent/weak.",
                "pentester": "Document missing headers. Prove impact by demonstrating Clickjacking or framing the application.",
                "security_team": "Enforce baseline security headers at the WAF or edge proxy layer (e.g., Cloudflare, AWS CloudFront) for all apps."
            },
            "learning_resources": ["https://owasp.org/www-project-secure-headers/"]
        },
        "exposed_api_docs": {
            "vulnerability_class": "Exposed API Documentation",
            "description": "API documentation (e.g., Swagger UI, OpenAPI JSON) is publicly accessible without authentication.",
            "severity": "Informational",
            "impact": "Provides attackers with a complete map of the API surface, making it easier to discover hidden endpoints and understand parameter structures.",
            "remediation": ["Require authentication to access API documentation in production.", "Disable Swagger/OpenAPI endpoints in production environments."],
            "audience_guidance": {
                "student": "API docs are the manual for the app. Giving attackers the manual makes their job much easier.",
                "developer": "Disable endpoints like /swagger-ui.html or /openapi.json in production, or place them behind authentication.",
                "bug_bounty_hunter": "Use the exposed docs to find undocumented endpoints, test for BOLA/IDOR, and understand required parameters.",
                "pentester": "Import the OpenAPI spec into Postman or Burp Suite to systematically test all API endpoints for vulnerabilities.",
                "security_team": "Ensure API documentation generation is conditionally disabled for production builds."
            },
            "learning_resources": ["https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html"]
        }
    }
    for k, v in vulns.items():
        write_json(os.path.join(base_dir, "vulnerabilities", f"{k}.json"), v)

if __name__ == "__main__":
    gen_services()
    gen_tech()
    gen_vulns()
    print("Intelligence Library expanded successfully.")
