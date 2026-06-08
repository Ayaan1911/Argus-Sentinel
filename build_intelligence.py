import os
import json

base_dir = "argus-intelligence"
os.makedirs(f"{base_dir}/services", exist_ok=True)
os.makedirs(f"{base_dir}/technologies", exist_ok=True)
os.makedirs(f"{base_dir}/vulnerabilities", exist_ok=True)
os.makedirs("backend/app/intelligence", exist_ok=True)

schema = {
  "service": "",
  "port": 0,
  "protocol": "",
  "purpose": "",
  "risk_level": "",
  "description": "",
  "common_risks": [],
  "misconfigurations": [],
  "attack_patterns": [],
  "real_world_incidents": [],
  "recommended_actions": [],
  "audience_guidance": {
    "student": "",
    "developer": "",
    "bug_bounty_hunter": "",
    "pentester": "",
    "security_team": ""
  },
  "correlation_rules": {
    "amplifies": [],
    "requires": [],
    "mitigates": []
  },
  "learning_resources": [],
  "related_findings": [],
  "mitre_attack": [],
  "risk_weight": 0,
  "version": "1.0",
  "last_updated": "2026-06-08",
  "reviewed_by": "argus-team"
}

data = {}

# --- SERVICES ---
data["services/ssh.json"] = {
  **schema,
  "service": "SSH",
  "port": 22,
  "protocol": "TCP",
  "purpose": "Secure shell access for remote administration.",
  "risk_level": "High",
  "description": "Secure Shell (SSH) is a cryptographic network protocol for operating network services securely over an unsecured network.",
  "common_risks": ["brute force", "credential stuffing", "weak ciphers", "outdated versions"],
  "misconfigurations": ["password auth enabled", "root login permitted", "no IP restrictions", "default port"],
  "attack_patterns": ["brute force", "credential stuffing", "CVE exploitation on outdated OpenSSH"],
  "real_world_incidents": ["Numerous ransomware strains utilizing exposed SSH ports to pivot into internal networks."],
  "recommended_actions": ["Disable password authentication.", "Disable root login.", "Use Key-based auth only.", "Restrict IP access.", "Implement fail2ban."],
  "audience_guidance": {
    "student": "SSH is like a secure tunnel into a computer. If left wide open, anyone can try to guess the password to get in.",
    "developer": "Configure sshd_config with PasswordAuthentication no and PermitRootLogin no.",
    "bug_bounty_hunter": "Check for version CVEs, username enumeration capabilities, and if password auth is allowed.",
    "pentester": "Use Hydra to brute force passwords, search for Metasploit modules for older versions, perform banner grabbing.",
    "security_team": "Implement strict firewall rules, monitor for failed login spikes, enforce MFA for SSH access."
  },
  "correlation_rules": {
    "amplifies": ["password_auth_enabled", "internet_facing", "outdated_version"],
    "requires": ["network_exposure"],
    "mitigates": ["key_based_auth", "ip_restricted", "fail2ban", "mfa_enabled"]
  },
  "learning_resources": ["https://man.openbsd.org/sshd_config"],
  "related_findings": ["weak_credentials", "exposed_administrative_interface"],
  "mitre_attack": ["T1110", "T1021.004"],
  "risk_weight": 7
}

data["services/http.json"] = {
  **schema,
  "service": "HTTP",
  "port": 80,
  "protocol": "TCP",
  "purpose": "Unencrypted web traffic delivery.",
  "risk_level": "Medium",
  "description": "Hypertext Transfer Protocol (HTTP) is the foundation of data communication for the World Wide Web. On port 80, it is unencrypted.",
  "common_risks": ["man-in-the-middle attacks", "cleartext credential transmission", "session hijacking"],
  "misconfigurations": ["No redirection to HTTPS", "sensitive data exposed without TLS", "default welcome pages"],
  "attack_patterns": ["Packet sniffing", "Session hijacking", "Bypassing HSTS"],
  "real_world_incidents": ["Firesheep demonstrated the ease of session hijacking over open HTTP networks."],
  "recommended_actions": ["Redirect all HTTP traffic to HTTPS via 301.", "Enforce HSTS."],
  "audience_guidance": {
    "student": "HTTP sends data in plain text. Anyone on the same network can read it.",
    "developer": "Ensure all endpoints immediately redirect to port 443 with a 301 status.",
    "bug_bounty_hunter": "Check if sensitive functionality (like login) works over HTTP.",
    "pentester": "Sniff traffic on the network to capture credentials or session cookies.",
    "security_team": "Enforce strict transport security across the organization and monitor for unencrypted HTTP traffic."
  },
  "correlation_rules": {
    "amplifies": ["sensitive_data_transmission", "login_page"],
    "requires": [],
    "mitigates": ["http_to_https_redirect"]
  },
  "learning_resources": ["https://developer.mozilla.org/en-US/docs/Web/HTTP"],
  "related_findings": ["cleartext_transmission"],
  "mitre_attack": ["T1040", "T1557"],
  "risk_weight": 5
}

data["services/https.json"] = {
  **schema,
  "service": "HTTPS",
  "port": 443,
  "protocol": "TCP",
  "purpose": "Encrypted web traffic delivery.",
  "risk_level": "Low",
  "description": "HTTPS is an extension of HTTP used for secure communication over a computer network.",
  "common_risks": ["Weak TLS configurations", "Expired certificates", "Application layer vulnerabilities"],
  "misconfigurations": ["Supporting TLS 1.0/1.1", "Weak cipher suites", "Self-signed certificates in production"],
  "attack_patterns": ["POODLE", "BEAST", "Heartbleed (historic)", "Web app attacks (XSS, SQLi)"],
  "real_world_incidents": ["Heartbleed vulnerability exposed memory contents over HTTPS connections globally."],
  "recommended_actions": ["Enforce TLS 1.2 or 1.3.", "Disable weak ciphers.", "Use strong certificate authorities.", "Implement HSTS."],
  "audience_guidance": {
    "student": "HTTPS ensures your data is encrypted, but the website itself could still have flaws.",
    "developer": "Configure web servers to use modern TLS standards and strong cipher suites.",
    "bug_bounty_hunter": "Review certificate details, check for weak ciphers via SSLlabs/testssl.sh, then focus on app layer.",
    "pentester": "Test for downgrade attacks and weak encryption; focus primary efforts on web application vulnerabilities.",
    "security_team": "Automate certificate renewal and continuously scan for non-compliant TLS configurations."
  },
  "correlation_rules": {
    "amplifies": ["weak_ciphers", "expired_cert"],
    "requires": [],
    "mitigates": ["tls_1_3", "hsts"]
  },
  "learning_resources": ["https://www.ssllabs.com/"],
  "related_findings": ["weak_tls", "expired_certificate"],
  "mitre_attack": ["T1573.002", "T1190"],
  "risk_weight": 3
}

data["services/mysql.json"] = {
  **schema,
  "service": "MySQL",
  "port": 3306,
  "protocol": "TCP",
  "purpose": "Relational database management system.",
  "risk_level": "High",
  "description": "MySQL is an open-source relational database management system. Exposing it directly to the internet is highly discouraged.",
  "common_risks": ["Brute force", "Unauthorized data access", "SQL Injection pivoting"],
  "misconfigurations": ["Exposed to public internet", "Default root credentials", "Anonymous user accounts enabled"],
  "attack_patterns": ["Credential brute force", "Exploitation of CVEs", "UDF (User Defined Function) exploitation for RCE"],
  "real_world_incidents": ["Numerous database dumps resulting from misconfigured, internet-facing MySQL servers."],
  "recommended_actions": ["Bind to localhost or internal network only.", "Use strong passwords.", "Disable anonymous access.", "Require TLS for connections."],
  "audience_guidance": {
    "student": "A database stores all sensitive information. It should never be directly accessible from the internet.",
    "developer": "Ensure the database binds to 127.0.0.1 or an internal VPC IP, and enforce strong authentication.",
    "bug_bounty_hunter": "Attempt to connect using default credentials (root/blank) or perform a light brute force.",
    "pentester": "If access is gained, extract hashes, dump data, and attempt to write files or execute commands via UDF.",
    "security_team": "Alert on any external traffic destined for port 3306. Enforce least privilege access."
  },
  "correlation_rules": {
    "amplifies": ["default_credentials", "publicly_accessible"],
    "requires": ["network_exposure"],
    "mitigates": ["internal_network_only", "strong_auth"]
  },
  "learning_resources": ["https://dev.mysql.com/doc/refman/8.0/en/security-guidelines.html"],
  "related_findings": ["exposed_database", "weak_credentials"],
  "mitre_attack": ["T1190", "T1059"],
  "risk_weight": 8
}

data["services/redis.json"] = {
  **schema,
  "service": "Redis",
  "port": 6379,
  "protocol": "TCP",
  "purpose": "In-memory data structure store used as a database, cache, and message broker.",
  "risk_level": "Critical",
  "description": "Redis is extremely fast but historically lacked robust security features by default, making internet exposure catastrophic.",
  "common_risks": ["Unauthenticated access", "Data theft", "Remote Code Execution (RCE)"],
  "misconfigurations": ["No authentication (requirepass not set)", "Bound to 0.0.0.0", "Running as root"],
  "attack_patterns": ["Unauthenticated command execution", "Writing malicious SSH keys to ~/.ssh/authorized_keys", "Writing cron jobs"],
  "real_world_incidents": ["Massive cryptomining botnet campaigns leveraging open Redis instances to gain RCE via cron jobs."],
  "recommended_actions": ["Bind to localhost.", "Set a strong 'requirepass' password.", "Rename dangerous commands (CONFIG, FLUSHDB)."],
  "audience_guidance": {
    "student": "Redis trusts everyone by default. If it's on the internet, attackers can completely take over the server in seconds.",
    "developer": "Always configure a password and never expose Redis directly to the public internet.",
    "bug_bounty_hunter": "Connect using redis-cli. If it connects without auth, you have Critical impact.",
    "pentester": "Exploit unauthenticated Redis to gain a reverse shell by writing to crontab or authorized_keys.",
    "security_team": "Monitor for exposed 6379. Mandate Redis authentication across the organization."
  },
  "correlation_rules": {
    "amplifies": ["no_auth", "publicly_accessible", "running_as_root"],
    "requires": ["network_exposure"],
    "mitigates": ["auth_enabled", "internal_network_only", "renamed_commands"]
  },
  "learning_resources": ["https://redis.io/topics/security"],
  "related_findings": ["unauthenticated_access", "exposed_database"],
  "mitre_attack": ["T1190", "T1053.003"],
  "risk_weight": 9
}

# --- TECHNOLOGIES ---
data["technologies/apache.json"] = {
  **schema,
  "service": "Apache HTTP Server",
  "purpose": "Web Server",
  "risk_level": "Medium",
  "description": "Apache is a widely-used open-source cross-platform web server software.",
  "common_risks": ["Directory traversal", "Information disclosure via server status", "Misconfigured .htaccess"],
  "misconfigurations": ["mod_status enabled publicly", "Directory listing enabled", "Verbose server banners"],
  "attack_patterns": ["Path traversal attacks", "Exploiting vulnerable CGI scripts", "Information gathering via server headers"],
  "real_world_incidents": ["Exploitation of Apache Struts (related technology) led to massive data breaches (e.g., Equifax)."],
  "recommended_actions": ["Disable server signature and banners.", "Disable directory browsing.", "Restrict access to /server-status."],
  "audience_guidance": {
    "student": "Apache serves websites. If not configured correctly, it might show files it shouldn't.",
    "developer": "Use ServerTokens Prod and ServerSignature Off in the configuration.",
    "bug_bounty_hunter": "Check for /server-status, directory listings, and old CVEs based on the version header.",
    "pentester": "Look for misconfigured Alias directives, evaluate HTTP methods enabled (e.g., PUT).",
    "security_team": "Ensure standard secure baseline configs are deployed across all Apache instances."
  },
  "correlation_rules": {
    "amplifies": ["verbose_errors", "directory_listing"],
    "requires": [],
    "mitigates": ["secure_headers", "waf_enabled"]
  },
  "mitre_attack": ["T1190"],
  "risk_weight": 5
}

data["technologies/nginx.json"] = {
  **schema,
  "service": "Nginx",
  "purpose": "Web Server / Reverse Proxy",
  "risk_level": "Medium",
  "description": "Nginx is a web server that can also be used as a reverse proxy, load balancer, mail proxy and HTTP cache.",
  "common_risks": ["Alias traversal", "CRLF Injection", "Server-Side Request Forgery via proxy_pass"],
  "misconfigurations": ["Missing trailing slash in alias directives", "Verbose server tokens", "Insecure proxy_pass"],
  "attack_patterns": ["Off-by-slash alias traversal", "HTTP Request Smuggling", "SSRF"],
  "real_world_incidents": ["Numerous off-by-slash vulnerabilities allowing attackers to read source code outside the intended web root."],
  "recommended_actions": ["Ensure trailing slashes match in location and alias blocks.", "Set server_tokens off;"],
  "audience_guidance": {
    "student": "Nginx is fast and popular, but small typos in its config file can expose hidden files.",
    "developer": "Be extremely careful with location block matching and trailing slashes.",
    "bug_bounty_hunter": "Test for off-by-slash directory traversal by appending '../' to paths.",
    "pentester": "Evaluate reverse proxy configurations for SSRF and HTTP smuggling vulnerabilities.",
    "security_team": "Lint Nginx configurations automatically in CI/CD pipelines to catch misconfigurations."
  },
  "correlation_rules": {
    "amplifies": ["misconfigured_alias", "ssrf_vulnerable_proxy"],
    "requires": [],
    "mitigates": ["strict_routing", "server_tokens_off"]
  },
  "mitre_attack": ["T1190"],
  "risk_weight": 5
}

data["technologies/tomcat.json"] = {
  **schema,
  "service": "Apache Tomcat",
  "purpose": "Java Servlet Container",
  "risk_level": "High",
  "description": "Apache Tomcat is an open-source implementation of the Java Servlet, JavaServer Pages, Java Expression Language and WebSocket technologies.",
  "common_risks": ["Remote Code Execution via Manager application", "Ghostcat vulnerability", "Information disclosure"],
  "misconfigurations": ["Default manager credentials (tomcat:tomcat)", "AJP port (8009) exposed", "Verbose error pages"],
  "attack_patterns": ["Deploying malicious WAR files", "Brute forcing manager app", "Exploiting Ghostcat (CVE-2020-1938)"],
  "real_world_incidents": ["Widespread exploitation of default manager credentials to deploy web shells."],
  "recommended_actions": ["Change default manager passwords.", "Block public access to /manager.", "Disable or secure AJP connector."],
  "audience_guidance": {
    "student": "Tomcat runs Java web apps. If you leave the admin panel open with default passwords, anyone can upload a virus.",
    "developer": "Remove the default manager application if not needed in production. Secure the AJP connector.",
    "bug_bounty_hunter": "Check for /manager/html, try default credentials like tomcat:tomcat, admin:admin.",
    "pentester": "If manager access is achieved, generate a malicious WAR payload using msfvenom and deploy it for a reverse shell.",
    "security_team": "Monitor for WAR file deployments and enforce strong access controls on administrative interfaces."
  },
  "correlation_rules": {
    "amplifies": ["default_credentials", "exposed_manager_app"],
    "requires": [],
    "mitigates": ["ip_restricted_manager", "strong_passwords"]
  },
  "mitre_attack": ["T1190", "T1505.003"],
  "risk_weight": 8
}

data["technologies/wordpress.json"] = {
  **schema,
  "service": "WordPress",
  "purpose": "Content Management System (CMS)",
  "risk_level": "High",
  "description": "WordPress is the world's most popular open-source CMS, making it a massive target for attackers.",
  "common_risks": ["Vulnerable plugins/themes", "XML-RPC attacks", "Brute force admin login", "User enumeration"],
  "misconfigurations": ["Exposed xmlrpc.php", "Default admin username", "Directory listing in wp-content"],
  "attack_patterns": ["Exploiting outdated plugins for RCE/SQLi", "Brute forcing wp-login.php", "XML-RPC pingback SSRF/Brute force"],
  "real_world_incidents": ["Countless mass-compromises of WordPress sites due to vulnerable third-party plugins (e.g., TimThumb, Revolution Slider)."],
  "recommended_actions": ["Keep core, plugins, and themes updated.", "Disable XML-RPC.", "Use strong passwords and MFA.", "Limit login attempts."],
  "audience_guidance": {
    "student": "WordPress powers much of the web. Because it's so popular, hackers constantly look for weaknesses in its plugins.",
    "developer": "Implement auto-updates, avoid abandoned plugins, and restrict access to the wp-admin directory.",
    "bug_bounty_hunter": "Use wpscan to enumerate plugins, check for exposed xmlrpc.php, and find CVEs for identified plugins.",
    "pentester": "Focus heavily on third-party plugin vulnerabilities rather than WordPress core. Exploit plugins for shell access.",
    "security_team": "Implement a WAF to block common WordPress attacks and strictly manage the plugin inventory."
  },
  "correlation_rules": {
    "amplifies": ["outdated_plugins", "xmlrpc_enabled"],
    "requires": [],
    "mitigates": ["waf_enabled", "auto_updates"]
  },
  "mitre_attack": ["T1190", "T1133"],
  "risk_weight": 7
}

# --- VULNERABILITIES ---
data["vulnerabilities/sql_injection.json"] = {
  **schema,
  "service": "SQL Injection (SQLi)",
  "purpose": "Vulnerability Class",
  "risk_level": "Critical",
  "description": "SQL Injection is a web security vulnerability that allows an attacker to interfere with the queries that an application makes to its database.",
  "common_risks": ["Data breach", "Authentication bypass", "Remote code execution"],
  "misconfigurations": ["Using string concatenation for SQL queries instead of prepared statements", "Insufficient input sanitization"],
  "attack_patterns": ["Union-based SQLi", "Error-based SQLi", "Blind SQLi (Boolean/Time-based)"],
  "real_world_incidents": ["TalkTalk data breach, numerous high-profile compromises of user databases."],
  "recommended_actions": ["Use prepared statements (parameterized queries).", "Use stored procedures.", "Enforce least privilege on the DB user."],
  "audience_guidance": {
    "student": "SQL injection happens when an app mistakes user input for a database command, letting hackers steal data.",
    "developer": "Never concatenate strings to build SQL. Always use ORMs or parameterized queries provided by your framework.",
    "bug_bounty_hunter": "Test all inputs (GET, POST, Headers) with single quotes, sleep() payloads, and logic operators.",
    "pentester": "Use sqlmap to automate extraction once confirmed, attempt to read local files or gain shell via xp_cmdshell/UDF.",
    "security_team": "Deploy WAFs with strict SQLi rules and mandate SAST/DAST scanning in the SDLC."
  },
  "correlation_rules": {
    "amplifies": ["db_running_as_root", "verbose_errors"],
    "requires": ["untrusted_input_in_query"],
    "mitigates": ["prepared_statements", "waf"]
  },
  "mitre_attack": ["T1190"],
  "risk_weight": 10
}

data["vulnerabilities/xss.json"] = {
  **schema,
  "service": "Cross-Site Scripting (XSS)",
  "purpose": "Vulnerability Class",
  "risk_level": "High",
  "description": "XSS allows attackers to inject malicious scripts into web pages viewed by other users.",
  "common_risks": ["Session hijacking", "Credential theft", "Defacement", "Phishing"],
  "misconfigurations": ["Reflecting user input without HTML encoding", "Improper use of dangerouslySetInnerHTML in React"],
  "attack_patterns": ["Stored XSS", "Reflected XSS", "DOM-based XSS"],
  "real_world_incidents": ["Samy worm on MySpace, which propagated via a Stored XSS vulnerability."],
  "recommended_actions": ["Context-aware output encoding.", "Implement Content Security Policy (CSP).", "Use HttpOnly flags for session cookies."],
  "audience_guidance": {
    "student": "XSS lets hackers run malicious JavaScript in another user's browser, stealing their session.",
    "developer": "Always encode user input before rendering it in the browser. Rely on modern frameworks (React, Angular) that escape by default.",
    "bug_bounty_hunter": "Inject payloads like <script>alert(1)</script> or javascript: URLs in all input fields and URL parameters.",
    "pentester": "Demonstrate impact by stealing cookies or exploiting administrative functionalities via the victim's session.",
    "security_team": "Enforce strong CSP headers and utilize automated DAST tools to catch reflected input."
  },
  "correlation_rules": {
    "amplifies": ["lack_of_httponly_cookies", "weak_csp"],
    "requires": ["untrusted_input_in_html"],
    "mitigates": ["context_aware_encoding", "csp", "httponly_cookies"]
  },
  "mitre_attack": ["T1190", "T1059.007"],
  "risk_weight": 7
}

data["vulnerabilities/ssrf.json"] = {
  **schema,
  "service": "Server-Side Request Forgery (SSRF)",
  "purpose": "Vulnerability Class",
  "risk_level": "Critical",
  "description": "SSRF allows an attacker to induce the server-side application to make HTTP requests to an arbitrary domain of the attacker's choosing.",
  "common_risks": ["Access to internal APIs", "Cloud metadata exfiltration (AWS IAM credentials)", "Internal port scanning"],
  "misconfigurations": ["Accepting URLs from users and fetching them without validation", "Lack of network segmentation"],
  "attack_patterns": ["Accessing 169.254.169.254 (Cloud Metadata)", "Accessing localhost administrative interfaces"],
  "real_world_incidents": ["Capital One breach where an SSRF vulnerability was used to extract AWS IAM credentials from the metadata service."],
  "recommended_actions": ["Validate and sanitize URLs.", "Use allowlists for domains/IPs.", "Disable HTTP redirections.", "Implement network segmentation."],
  "audience_guidance": {
    "student": "SSRF tricks a server into making web requests on the hacker's behalf, often to access internal, hidden systems.",
    "developer": "Never fetch URLs provided by users directly. If necessary, strictly validate against an allowlist and resolve IPs to block private ranges.",
    "bug_bounty_hunter": "Test webhooks, image uploaders, and PDF generators with internal IPs or cloud metadata endpoints.",
    "pentester": "If SSRF is found, attempt to retrieve cloud IAM keys, access internal Redis/Memcached, or scan the internal network.",
    "security_team": "Enforce IMDSv2 in AWS, segment application networks to prevent lateral movement from SSRF."
  },
  "correlation_rules": {
    "amplifies": ["cloud_environment", "internal_services_without_auth"],
    "requires": ["server_fetches_user_url"],
    "mitigates": ["imdsv2", "network_segmentation", "url_allowlist"]
  },
  "mitre_attack": ["T1190"],
  "risk_weight": 9
}

data["vulnerabilities/idor.json"] = {
  **schema,
  "service": "Insecure Direct Object Reference (IDOR)",
  "purpose": "Vulnerability Class",
  "risk_level": "High",
  "description": "IDOR occurs when an application provides direct access to objects based on user-supplied input without proper authorization checks.",
  "common_risks": ["Horizontal privilege escalation", "Vertical privilege escalation", "Mass data exposure"],
  "misconfigurations": ["Using predictable sequential IDs without access control checks"],
  "attack_patterns": ["Changing user_id=1000 to user_id=1001 to view another user's data"],
  "real_world_incidents": ["Numerous APIs exposing PII when attackers iterate through sequential customer IDs."],
  "recommended_actions": ["Implement robust access control checks for every object request.", "Use unpredictable GUIDs/UUIDs instead of sequential integers."],
  "audience_guidance": {
    "student": "IDOR is like changing the room number on a hotel key card to open someone else's door.",
    "developer": "Always verify that the currently authenticated user owns or has permission to access the requested resource ID.",
    "bug_bounty_hunter": "Create two accounts. Access an object owned by account A, then swap the session token to account B and try to access it again.",
    "pentester": "Automate the manipulation of ID parameters in API requests (using tools like Autorize) to identify access control flaws.",
    "security_team": "Ensure authorization logic is centralized and consistently applied across all endpoints."
  },
  "correlation_rules": {
    "amplifies": ["sequential_ids"],
    "requires": ["missing_authorization_check"],
    "mitigates": ["uuid_usage", "strict_acls"]
  },
  "mitre_attack": ["T1190"],
  "risk_weight": 8
}

data["vulnerabilities/rce.json"] = {
  **schema,
  "service": "Remote Code Execution (RCE)",
  "purpose": "Vulnerability Class",
  "risk_level": "Critical",
  "description": "RCE allows an attacker to execute arbitrary commands or code on a target machine over a network.",
  "common_risks": ["Complete system compromise", "Data exfiltration", "Lateral movement", "Ransomware deployment"],
  "misconfigurations": ["Using insecure deserialization", "Passing user input to os.system() or eval()", "Unrestricted file uploads"],
  "attack_patterns": ["OS Command Injection", "Insecure Deserialization", "File Upload to Web Shell"],
  "real_world_incidents": ["Log4Shell (CVE-2021-44228), WannaCry (EternalBlue)."],
  "recommended_actions": ["Never pass untrusted data to system shells or eval functions.", "Use language-safe APIs.", "Run applications with least privilege."],
  "audience_guidance": {
    "student": "RCE is the holy grail for hackers. It means they can run any command on your computer as if they were sitting in front of it.",
    "developer": "Avoid system calls. If necessary, strictly validate input and do not use a shell wrapper. Avoid insecure deserialization formats.",
    "bug_bounty_hunter": "Look for input fields that interact with the OS, test deserialization endpoints with payloads from Ysoserial, test file uploads.",
    "pentester": "Obtain a reverse shell, escalate privileges, and pivot into the internal network.",
    "security_team": "Run applications in highly restricted containers (e.g., read-only filesystems, dropped capabilities) to limit post-exploitation impact."
  },
  "correlation_rules": {
    "amplifies": ["running_as_root", "outdated_dependencies"],
    "requires": ["insecure_code_execution_path"],
    "mitigates": ["least_privilege", "container_sandboxing"]
  },
  "mitre_attack": ["T1190", "T1059"],
  "risk_weight": 10
}

for path, content in data.items():
    with open(f"{base_dir}/{path}", "w") as f:
        json.dump(content, f, indent=2)

loader_code = '''import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class IntelligenceLoader:
    def __init__(self):
        self.data = {
            "services": {},
            "technologies": {},
            "vulnerabilities": {}
        }
        self._load_all()

    def _load_all(self):
        base_path = Path(__file__).resolve().parent.parent.parent.parent / "argus-intelligence"
        
        if not base_path.exists():
            logger.warning(f"Intelligence base path not found at {base_path}")
            return

        for category in ["services", "technologies", "vulnerabilities"]:
            cat_path = base_path / category
            if not cat_path.exists():
                continue
                
            for json_file in cat_path.glob("*.json"):
                try:
                    with open(json_file, 'r') as f:
                        content = json.load(f)
                        # Use the filename without extension as the key
                        key = json_file.stem.lower()
                        self.data[category][key] = content
                except Exception as e:
                    logger.error(f"Failed to load {json_file}: {e}")

    def load_all(self):
        return self.data

    def get_service(self, name: str):
        return self.data["services"].get(name.lower())

    def get_technology(self, name: str):
        return self.data["technologies"].get(name.lower())

    def get_vulnerability(self, name: str):
        return self.data["vulnerabilities"].get(name.lower())

# Singleton instance for caching
loader_instance = IntelligenceLoader()

def load_all():
    return loader_instance.load_all()

def get_service(name: str):
    return loader_instance.get_service(name)

def get_technology(name: str):
    return loader_instance.get_technology(name)

def get_vulnerability(name: str):
    return loader_instance.get_vulnerability(name)
'''

with open("backend/app/intelligence/loader.py", "w") as f:
    f.write(loader_code)

# Ensure __init__.py exists
with open("backend/app/intelligence/__init__.py", "w") as f:
    f.write("from .loader import load_all, get_service, get_technology, get_vulnerability\n")

print("Intelligence building complete.")
