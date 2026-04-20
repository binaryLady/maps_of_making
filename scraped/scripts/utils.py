"""
Shared utilities for LifeTech member extraction pipeline.
Includes API clients, logging, file operations, and retry logic.
"""

import os
import sys
import logging
import sqlite3
import hashlib
import time
from pathlib import Path
from typing import Optional, Dict, Any
from functools import wraps
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from mistralai import Mistral
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# Logging Configuration
# ============================================================================

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure logging for the pipeline."""
    logger = logging.getLogger("lifetech_extraction")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# Global logger
logger = setup_logging(os.getenv("LOG_LEVEL", "INFO"))

# ============================================================================
# API Clients
# ============================================================================

def get_mistral_client() -> Mistral:
    """Initialize and return Mistral API client."""
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY not found in environment variables")
    return Mistral(api_key=api_key)


def get_requests_session() -> requests.Session:
    """Create a requests session with retry logic."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    })
    return session


# ============================================================================
# Retry Logic
# ============================================================================

def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator for retrying failed function calls."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (requests.RequestException, ConnectionError) as e:
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Attempt {attempt + 1} failed: {e}. "
                            f"Retrying in {delay}s..."
                        )
                        time.sleep(delay * (2 ** attempt))
                    else:
                        logger.error(f"All {max_retries} attempts failed.")
                        raise
        return wrapper
    return decorator


# ============================================================================
# File Operations
# ============================================================================

def ensure_directory(path: str) -> Path:
    """Ensure directory exists and return Path object."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def save_html(url: str, content: str, base_dir: str = "lifetech.brussels/raw_html") -> str:
    """
    Save HTML content to file with URL-based filename.
    Returns the filepath.
    """
    ensure_directory(base_dir)
    # Create filename from URL hash
    url_hash = hashlib.md5(url.encode()).hexdigest()
    filename = f"{url_hash}.html"
    filepath = Path(base_dir) / filename
    filepath.write_text(content, encoding="utf-8")
    logger.debug(f"Saved HTML from {url} to {filepath}")
    return str(filepath)


def load_html(url: str, base_dir: str = "lifetech.brussels/raw_html") -> Optional[str]:
    """Load cached HTML if it exists."""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    filepath = Path(base_dir) / f"{url_hash}.html"
    if filepath.exists():
        logger.debug(f"Loading cached HTML for {url}")
        return filepath.read_text(encoding="utf-8")
    return None


# ============================================================================
# SQLite Operations
# ============================================================================

def init_database(db_path: str = "lifetech.brussels/extraction_log.db") -> sqlite3.Connection:
    """Initialize SQLite database with required tables."""
    ensure_directory(Path(db_path).parent)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create extractions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS extractions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            source TEXT NOT NULL,
            field TEXT NOT NULL,
            value TEXT,
            confidence TEXT,
            extraction_method TEXT
        )
    """)

    # Create website_checks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS website_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id TEXT NOT NULL,
            url_from_lifetech TEXT,
            url_actual TEXT,
            http_status INTEGER,
            redirect_detected BOOLEAN,
            html_hash TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create model_performance table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS model_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT NOT NULL,
            field TEXT NOT NULL,
            accuracy REAL,
            cost REAL,
            latency REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    logger.info(f"Database initialized at {db_path}")
    return conn


def log_extraction(
    conn: sqlite3.Connection,
    member_id: str,
    source: str,
    field: str,
    value: Optional[str],
    confidence: str = "none",
    extraction_method: str = "unknown"
):
    """Log an extraction to the database."""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO extractions
        (member_id, source, field, value, confidence, extraction_method)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (member_id, source, field, value, confidence, extraction_method))
    conn.commit()


def log_website_check(
    conn: sqlite3.Connection,
    member_id: str,
    url_from_lifetech: str,
    url_actual: str,
    http_status: int,
    redirect_detected: bool,
    html_hash: str = ""
):
    """Log a website check to the database."""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO website_checks
        (member_id, url_from_lifetech, url_actual, http_status, redirect_detected, html_hash)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (member_id, url_from_lifetech, url_actual, http_status, redirect_detected, html_hash))
    conn.commit()


# ============================================================================
# Data Quality Utilities
# ============================================================================

class DataQualityIssue:
    """Represents a data quality issue found during extraction."""
    SEVERITY_HIGH = "HIGH"
    SEVERITY_MEDIUM = "MEDIUM"
    SEVERITY_LOW = "LOW"

    def __init__(
        self,
        member_id: str,
        member_name: str,
        severity: str,
        issue_type: str,
        description: str,
        related_field: Optional[str] = None,
        remediation: Optional[str] = None
    ):
        self.member_id = member_id
        self.member_name = member_name
        self.severity = severity
        self.issue_type = issue_type
        self.description = description
        self.related_field = related_field
        self.remediation = remediation
        self.detected_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "member_id": self.member_id,
            "member_name": self.member_name,
            "severity": self.severity,
            "issue_type": self.issue_type,
            "description": self.description,
            "related_field": self.related_field,
            "remediation": self.remediation,
            "detected_at": self.detected_at
        }


# ============================================================================
# HTML Parsing Utilities
# ============================================================================

def parse_html(html_content: str) -> BeautifulSoup:
    """Parse HTML content using BeautifulSoup."""
    return BeautifulSoup(html_content, "lxml")


def extract_text_from_html(html_content: str, selector: str = "body") -> str:
    """Extract text from HTML using CSS selector."""
    soup = parse_html(html_content)
    element = soup.select_one(selector)
    if element:
        return element.get_text(strip=True)
    return ""


# ============================================================================
# Provenance Tracking
# ============================================================================

class Provenance:
    """Track data provenance with source, confidence, and timestamp."""

    def __init__(
        self,
        source: str,  # "lifetech_profile" or "company_website"
        confidence: str,  # "high", "medium", "low", "none"
        timestamp: Optional[str] = None,
        extraction_method: str = "unknown"
    ):
        self.source = source
        self.confidence = confidence
        self.timestamp = timestamp or datetime.now().isoformat()
        self.extraction_method = extraction_method

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for TOML serialization."""
        return {
            "source": self.source,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "extraction_method": self.extraction_method
        }


if __name__ == "__main__":
    # Test utilities
    logger.info("Utils module loaded successfully")
    print(f"Logger configured: {logger.name}")
    print(f"Mistral API key present: {'MISTRAL_API_KEY' in os.environ}")
