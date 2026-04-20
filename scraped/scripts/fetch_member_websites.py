"""
Phase 3: Fetch member websites from member profile pages.

This script:
1. Loads member profile URLs from extracted members data
2. Fetches each profile page to find the "Our website" URL
3. Fetches the actual website (handling redirects, 404s, etc.)
4. Caches raw HTML for later processing
5. Tracks data quality issues (missing URLs, dead links, redirects)
"""

import sys
import time
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
import hashlib

import requests
from bs4 import BeautifulSoup
import tomlkit
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from utils import (
    logger,
    retry_on_failure,
    save_html,
    load_html,
    setup_logging,
    init_database,
    log_website_check,
    DataQualityIssue,
    Provenance
)

# Configuration
BASE_URL = "https://lifetech.brussels"
INPUT_FILE = "lifetech.brussels/members_from_lifetech.toml"
OUTPUT_FILE = "lifetech.brussels/members_with_websites.toml"
DATABASE_PATH = "lifetech.brussels/extraction_log.db"
CACHE_DIR = "lifetech.brussels/raw_html"
REQUEST_DELAY = 0.3
MAX_CONTENT_SIZE = 5 * 1024 * 1024  # 5MB


class MemberWebsiteFetcher:
    """Fetch member websites and detect quality issues."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        })
        self.members = []
        self.quality_issues = []
        self.db = init_database(DATABASE_PATH)
        self.logger = logger

    def load_members(self, input_file: str = INPUT_FILE):
        """Load members from TOML file."""
        if not Path(input_file).exists():
            self.logger.error(f"Input file not found: {input_file}")
            return False

        with open(input_file) as f:
            doc = tomlkit.parse(f.read())

        members_table = doc.get("members", {})
        for key, member_data in members_table.items():
            if isinstance(member_data, dict):
                member_dict = dict(member_data)
                member_dict["_key"] = key
                self.members.append(member_dict)

        self.logger.info(f"Loaded {len(self.members)} members from {input_file}")
        return True

    @retry_on_failure(max_retries=2, delay=1.0)
    def fetch_profile_page(self, profile_url: str) -> Optional[str]:
        """Fetch member's profile page from LifeTech site."""
        if not profile_url:
            return None

        try:
            response = self.session.get(profile_url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            self.logger.warning(f"Failed to fetch profile {profile_url}: {e}")
            return None

    def extract_website_url_from_profile(
        self,
        profile_html: str,
        member_name: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract the company website URL from profile page.
        Returns (website_url, extraction_method)
        """
        if not profile_html:
            return None, None

        soup = BeautifulSoup(profile_html, "lxml")

        # Strategy 1: Look for link with text "Our website" or "Website"
        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True).lower()
            if any(keyword in text for keyword in ["website", "web", "visit", "homepage"]):
                href = link.get("href")
                if href and href.startswith("http"):
                    return href, "link_with_website_text"

        # Strategy 2: Look for links with specific patterns (http://, https://)
        # in profile sections (often in contact or info area)
        info_section = soup.find(["div", "section"], class_=lambda x: x and any(
            keyword in x.lower() for keyword in ["contact", "info", "details", "description"]
        ))

        if info_section:
            for link in info_section.find_all("a", href=True):
                href = link.get("href")
                if href and href.startswith("http") and "lifetech" not in href:
                    return href, "link_in_info_section"

        # Strategy 3: Find any external link (not to lifetech.brussels)
        for link in soup.find_all("a", href=True):
            href = link.get("href")
            if (href and href.startswith("http") and
                "lifetech.brussels" not in href and
                href.endswith((".com", ".org", ".net", ".be", ".eu", ".fr"))):
                return href, "external_link"

        # Strategy 4: Look for email with company domain
        for link in soup.find_all("a", href=True):
            href = link.get("href")
            if href.startswith("mailto:"):
                # Extract email and infer company domain
                email = href.replace("mailto:", "").strip()
                if "@" in email:
                    domain = email.split("@")[1]
                    return f"https://{domain}", "inferred_from_email"

        self.logger.debug(f"No website URL found for {member_name}")
        return None, None

    @retry_on_failure(max_retries=2, delay=1.0)
    def fetch_website(
        self,
        website_url: str,
        timeout: int = 10
    ) -> Tuple[int, str, bool]:
        """
        Fetch website URL and track redirects.
        Returns (http_status, content, redirect_detected)
        """
        if not website_url:
            return 0, "", False

        try:
            response = self.session.head(
                website_url,
                timeout=timeout,
                allow_redirects=True
            )

            # Check if redirect occurred
            redirect_detected = len(response.history) > 0
            final_url = response.url

            # If successful, get the full content
            if response.status_code == 200:
                response_full = self.session.get(
                    final_url,
                    timeout=timeout,
                    stream=True
                )

                # Limit content size
                content_size = int(response_full.headers.get("content-length", 0))
                if content_size > MAX_CONTENT_SIZE:
                    self.logger.warning(f"Content too large ({content_size} bytes): {website_url}")
                    return 200, "", redirect_detected

                content = response_full.text[:MAX_CONTENT_SIZE]
                return response.status_code, content, redirect_detected

            return response.status_code, "", redirect_detected

        except requests.Timeout:
            self.logger.warning(f"Timeout fetching: {website_url}")
            return 0, "", False
        except requests.RequestException as e:
            self.logger.warning(f"Error fetching {website_url}: {e}")
            return 0, "", False

    def process_members(self) -> int:
        """Process all members: fetch profile, find website, fetch website."""
        successful = 0
        failed = 0

        for member in tqdm(self.members, desc="Processing members"):
            profile_url = member.get("profile_url")
            member_name = member.get("name", "Unknown")
            member_id = member.get("_key", "unknown")

            if not profile_url:
                self.quality_issues.append(DataQualityIssue(
                    member_id=member_id,
                    member_name=member_name,
                    severity=DataQualityIssue.SEVERITY_HIGH,
                    issue_type="missing_profile_url",
                    description="Member has no profile URL",
                    related_field="profile_url",
                    remediation="Add profile URL to member record"
                ))
                failed += 1
                continue

            # Fetch profile page
            profile_html = self.fetch_profile_page(profile_url)
            if not profile_html:
                self.quality_issues.append(DataQualityIssue(
                    member_id=member_id,
                    member_name=member_name,
                    severity=DataQualityIssue.SEVERITY_MEDIUM,
                    issue_type="inaccessible_profile",
                    description=f"Cannot fetch profile page",
                    related_field="profile_url",
                    remediation="Check profile URL accessibility"
                ))
                member["website_status"] = "profile_unreachable"
                failed += 1
                continue

            # Extract website URL from profile
            website_url, extraction_method = self.extract_website_url_from_profile(
                profile_html,
                member_name
            )

            if not website_url:
                self.quality_issues.append(DataQualityIssue(
                    member_id=member_id,
                    member_name=member_name,
                    severity=DataQualityIssue.SEVERITY_MEDIUM,
                    issue_type="missing_website_url",
                    description="Cannot extract website URL from profile",
                    related_field="website",
                    remediation="Manually add website URL"
                ))
                member["website_url"] = None
                member["website_status"] = "not_found"
                failed += 1
                continue

            # Update member record
            member["website_url"] = website_url
            member["website_extraction_method"] = extraction_method

            # Fetch the actual website
            http_status, website_content, redirect_detected = self.fetch_website(website_url)

            # Track website check in database
            if http_status > 0:
                html_hash = hashlib.md5(website_content.encode()).hexdigest() if website_content else ""
                log_website_check(
                    self.db,
                    member_id=member_id,
                    url_from_lifetech=profile_url,
                    url_actual=website_url,
                    http_status=http_status,
                    redirect_detected=redirect_detected,
                    html_hash=html_hash
                )

            # Handle different response codes
            if http_status == 200:
                # Success
                member["website_status"] = "accessible"
                if website_content:
                    html_path = save_html(website_url, website_content, CACHE_DIR)
                    member["website_html_cached"] = html_path
                successful += 1

                if redirect_detected:
                    self.quality_issues.append(DataQualityIssue(
                        member_id=member_id,
                        member_name=member_name,
                        severity=DataQualityIssue.SEVERITY_LOW,
                        issue_type="website_redirect",
                        description=f"Website redirects (may indicate URL change)",
                        related_field="website",
                        remediation="Update to final URL if it changed"
                    ))

            elif http_status == 404:
                member["website_status"] = "not_found_404"
                self.quality_issues.append(DataQualityIssue(
                    member_id=member_id,
                    member_name=member_name,
                    severity=DataQualityIssue.SEVERITY_HIGH,
                    issue_type="dead_link",
                    description=f"Website URL returns 404",
                    related_field="website",
                    remediation="Update website URL"
                ))
                failed += 1

            elif http_status in [301, 302, 307, 308]:
                member["website_status"] = "redirect"
                failed += 1

            else:
                member["website_status"] = f"http_{http_status}"
                failed += 1

            time.sleep(REQUEST_DELAY)

        self.logger.info(f"Processing complete: {successful} successful, {failed} failed")
        return successful

    def save_results(self, output_file: str = OUTPUT_FILE):
        """Save results to TOML with provenance."""
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        doc = tomlkit.document()
        doc.add(tomlkit.comment("LifeTech Members with Website Information"))
        doc.add(tomlkit.comment(f"Total members: {len(self.members)}"))

        members_table = tomlkit.table()

        for member in self.members:
            member_key = member.get("_key", f"member_{len(members_table)}")
            member_table = tomlkit.table()

            # Copy original fields
            for key, value in member.items():
                if key != "_key":
                    member_table[key] = value

            # Add provenance for website URL
            if member.get("website_url"):
                provenance = Provenance(
                    source="company_website",
                    confidence="high" if member.get("website_status") == "accessible" else "low",
                    extraction_method=member.get("website_extraction_method", "unknown")
                )
                member_table["_website_provenance"] = provenance.to_dict()

            members_table[member_key] = member_table

        doc["members"] = members_table

        # Add quality issues summary
        if self.quality_issues:
            issues_table = tomlkit.table()
            for i, issue in enumerate(self.quality_issues, 1):
                issue_key = f"issue_{i:03d}"
                issue_dict = issue.to_dict()
                issues_table[issue_key] = issue_dict

            doc["quality_issues"] = issues_table

        with open(output_file, "w") as f:
            f.write(tomlkit.dumps(doc))

        self.logger.info(f"Saved {len(self.members)} members to {output_file}")
        self.logger.info(f"Found {len(self.quality_issues)} data quality issues")

    def generate_quality_report(self):
        """Generate a summary of data quality issues."""
        if not self.quality_issues:
            self.logger.info("No data quality issues found!")
            return

        severity_counts = {}
        issue_types = {}

        for issue in self.quality_issues:
            severity = issue.severity
            issue_type = issue.issue_type
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1

        self.logger.info("=" * 60)
        self.logger.info("Data Quality Report")
        self.logger.info("=" * 60)
        self.logger.info(f"Total issues: {len(self.quality_issues)}")
        self.logger.info("By severity:")
        for severity in ["HIGH", "MEDIUM", "LOW"]:
            count = severity_counts.get(severity, 0)
            self.logger.info(f"  {severity}: {count}")
        self.logger.info("By type:")
        for issue_type, count in sorted(issue_types.items(), key=lambda x: x[1], reverse=True):
            self.logger.info(f"  {issue_type}: {count}")


def main():
    """Main fetch pipeline."""
    setup_logging("INFO")
    logger.info("Starting member website fetching...")

    fetcher = MemberWebsiteFetcher()

    # Load members
    if not fetcher.load_members():
        return 1

    # Process members
    successful = fetcher.process_members()

    # Generate reports
    fetcher.generate_quality_report()

    # Save results
    fetcher.save_results()

    # Cleanup
    fetcher.db.close()

    logger.info("=" * 60)
    logger.info("Website Fetching Complete")
    logger.info(f"Successfully fetched: {successful} members")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
