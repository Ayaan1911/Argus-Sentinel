import time
import requests
import json
import base64
import logging
from sqlalchemy.orm import Session
from app.models import Secret, Scan

logger = logging.getLogger(__name__)

def validate_github_token(value: str) -> tuple[bool, str | None]:
    try:
        r = requests.get('https://api.github.com/user', headers={'Authorization': f'token {value}'}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return True, f"GitHub User: {data.get('login', 'unknown')}"
    except Exception:
        pass
    return False, None

def validate_slack_webhook(value: str) -> tuple[bool, str | None]:
    try:
        r = requests.post(value, json={'text': 'test'}, timeout=10)
        if r.status_code == 200 and r.text.strip() == 'ok':
            return True, "Webhook accepted test message"
    except Exception:
        pass
    return False, None

def validate_jwt_token(value: str) -> tuple[bool, str | None]:
    try:
        parts = value.split('.')
        if len(parts) != 3:
            return False, None
        payload_b64 = parts[1]
        payload_b64 += '=' * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode('utf-8'))
        
        # Check exp if present
        if 'exp' in payload:
            if time.time() > payload['exp']:
                return False, "Token expired"
        
        summary = {k: v for k, v in payload.items() if k in ['sub', 'iss', 'aud', 'email', 'name', 'role']}
        if not summary:
            summary = "Valid JWT format (no standard claims)"
        return True, json.dumps(summary)
    except Exception:
        pass
    return False, None

def validate_generic_api_key(value: str, url: str) -> tuple[bool, str | None]:
    try:
        # Extract base domain from the file URL where the secret was found
        # Example: file_url could be 'https://api.github.com/js/app.js'
        if url.startswith('http'):
            from urllib.parse import urlparse
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}/"
        else:
            base_url = f"https://{url}/" if url else None
            
        if not base_url:
            return False, None
            
        r = requests.get(base_url, headers={'Authorization': f'Bearer {value}'}, timeout=10)
        if r.status_code not in (401, 403):
            return True, f"Response: {r.status_code}"
    except Exception:
        pass
    return False, None


def run(scan_id: str, db: Session) -> None:
    print(f"[STAGE] secret_validator: Started for scan {scan_id}")
    
    secrets = db.query(Secret).filter(Secret.scan_id == scan_id).all()
    if not secrets:
        print(f"[STAGE] secret_validator: No secrets found for {scan_id}")
        return

    validated_count = 0
    for secret in secrets:
        is_valid = False
        proof = None
        
        secret_type = (secret.secret_type or '').lower()
        value = secret.matched_value
        
        if not value:
            continue
            
        try:
            if 'github personal access token' in secret_type or 'github oauth token' in secret_type:
                is_valid, proof = validate_github_token(value)
            elif 'slack webhook' in secret_type:
                is_valid, proof = validate_slack_webhook(value)
            elif 'jwt' in secret_type:
                is_valid, proof = validate_jwt_token(value)
            elif 'api key' in secret_type or 'secret' in secret_type or 'token' in secret_type:
                is_valid, proof = validate_generic_api_key(value, secret.file_url)
            
            if is_valid:
                secret.validated = True
                secret.validation_proof = proof
                validated_count += 1
                
        except Exception as e:
            logger.error(f"Error validating secret {secret.id}: {e}")
        
        # Rate limiting
        time.sleep(1)

    db.commit()
    print(f"[STAGE] secret_validator: {validated_count}/{len(secrets)} secrets validated")
    print(f"[DB] secret_validator committed for scan {scan_id}")
