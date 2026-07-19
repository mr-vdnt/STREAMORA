import logging
import os
from datetime import datetime

# Ensure logs directory exists
log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))
os.makedirs(log_dir, exist_ok=True)
audit_log_path = os.path.join(log_dir, 'audit.log')

# Configure the Audit Logger
audit_logger = logging.getLogger("streamora_audit")
audit_logger.setLevel(logging.INFO)
audit_logger.propagate = False # Prevent duplicate logs

# Remove any existing handlers
if audit_logger.hasHandlers():
    audit_logger.handlers.clear()

# File handler for append-only logging (with utf-8 encoding to prevent Windows cp1252 errors)
fh = logging.FileHandler(audit_log_path, mode='a', encoding='utf-8')
fh.setLevel(logging.INFO)

# Formatting: WHO, WHAT, WHEN, WHERE
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s')
fh.setFormatter(formatter)
audit_logger.addHandler(fh)

def log_event(who: str, what: str, where: str, details: str = "", ip: str = "unknown", req_id: str = "N/A"):
    """
    Append-only immutable audit log format.
    who: User ID or IP
    what: Action performed (e.g. LOGIN_SUCCESS, UNAUTHORIZED_ACCESS)
    where: Endpoint or Service
    details: Any before/after values or extra context
    ip: Client IP
    req_id: Request ID
    """
    msg = f"REQ=[{req_id}] IP=[{ip}] WHO=[{who}] WHAT=[{what}] WHERE=[{where}] DETAILS=[{details}]"
    audit_logger.info(msg)

def get_recent_logs(limit: int = 100):
    """Retrieve the most recent audit logs for the Admin Dashboard."""
    if not os.path.exists(audit_log_path):
        return []
    with open(audit_log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    return lines[-limit:]
