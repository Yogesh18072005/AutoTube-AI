from __future__ import annotations
import base64, hashlib, hmac, json, os, time
from fastapi import Header, HTTPException

def issue_access_token(user_id: str, expires_in: int=3600) -> str:
    secret=os.getenv("AUTOTUBE_SECRET_KEY")
    if not secret: raise RuntimeError("AUTOTUBE_SECRET_KEY is required")
    enc=lambda b:base64.urlsafe_b64encode(b).decode().rstrip("=")
    header=enc(b'{"alg":"HS256","typ":"JWT"}')
    payload=enc(json.dumps({"sub":user_id,"exp":int(time.time())+expires_in},separators=(",",":")).encode())
    signature=enc(hmac.new(secret.encode(),f"{header}.{payload}".encode(),hashlib.sha256).digest())
    return f"{header}.{payload}.{signature}"

def require_user(authorization: str|None=Header(default=None)) -> str:
    secret=os.getenv("AUTOTUBE_SECRET_KEY")
    if not secret or not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401,"A valid bearer token is required.")
    try:
        token=authorization[7:]
        header,payload,signature=token.split(".")
        expected=base64.urlsafe_b64encode(hmac.new(secret.encode(),f"{header}.{payload}".encode(),hashlib.sha256).digest()).decode().rstrip("=")
        if not hmac.compare_digest(signature,expected): raise ValueError()
        decoded=base64.urlsafe_b64decode(payload+"="*((4-len(payload)%4)%4))
        data=json.loads(decoded)
        if int(data["exp"])<int(time.time()): raise ValueError()
        return str(data["sub"])
    except Exception as exc:
        raise HTTPException(401,"Bearer token is invalid or expired.") from exc
