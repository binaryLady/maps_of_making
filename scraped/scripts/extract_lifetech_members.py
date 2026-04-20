"""
Phase 2: Extract member information from LifeTech Brussels members directory.

This script:
1. Fetches all pages of the LifeTech members directory (paginated)
2. Extracts member names, profile URLs, and any visible contact info
3. Outputs structured data to TOML format
4. Validates all profile URLs are accessible
"""

import sys
import time
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
import tomlkit

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from utils import logger, retry_on_failure, save_html, setup_logging, Provenance

# Configuration
BASE_URL = "https://lifetech.brussels"
MEMBERS_PAGE_URL = f"{BASE_URL}/en/members-2/"
OUTPUT_FILE = "lifetech.brussels/members_from_lifetech.toml"
MAX_PAGES = 10  # Safety limit to detect pagination issues
REQUEST_DELAY = 0.5  # Delay between requests (seconds)


class LifeTechMemberExtractor:
    """Extract members from LifeTech Brussels website."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        })
        self.members = []
        self.logger = logger

    @retry_on_failure(max_retries=3, delay=2.0)
    def fetch_page(self, url: str) -> str:
        """Fetch a page with retry logic."""
        self.logger.info(f"Fetching: {url}")
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        return response.text

    def extract_members_from_page(self, html: str, page_num: int) -> List[Dict]:
        """Extract member information from a single page."""
        soup = BeautifulSoup(html, "lxml")
        members_on_page = []

        # Look for member cards/entries
        # LifeTech typically uses div containers with specific classes
        member_containers = soup.find_all(
            ["div", "article"],
            class_=lambda x: x and ("member" in x.lower() or "organization" in x.lower())
        )

        # If no member-specific containers, try a broader approach
        if not member_containers:
            self.logger.warning(
                f"Page {page_num}: No member containers found, "
                "trying alternative selectors"
            )
            member_containers = soup.find_all("div", class_="card")

        for container in member_containers:
            member_data = self._extract_member_from_container(container)
            if member_data and member_data.get("name"):
                members_on_page.append(member_data)

        self.logger.info(
            f"Page {page_num}: Extracted {len(members_on_page)} members"
        )
        return members_on_page

    def _extract_member_from_container(self, container) -> Optional[Dict]:
        """Extract a single member's data from a container."""
        member_data = {
            "name": None,
            "profile_url": None,
            "website": None,
            "email": None,
            "phone": None,
            "description": None,
            "location": None,
        }

        # Extract name (usually in h2, h3, or heading)
        name_elem = container.find(["h2", "h3", "h4", "h5"])
        if name_elem:
            member_data["name"] = name_elem.get_text(strip=True)

        # Extract profile URL (usually a link in the container)
        profile_link = container.find("a", href=True)
        if profile_link and profile_link.get("href"):
            href = profile_link.get("href")
            if not href.startswith("http"):
                href = urljoin(BASE_URL, href)
            member_data["profile_url"] = href

        # Extract description (usually in p tag)
        desc_elem = container.find("p")
        if desc_elem:
            member_data["description"] = desc_elem.get_text(strip=True)

        # Look for contact information
        text = container.get_text()

        # Simple email extraction (basic pattern)
        import re
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
        if email_match:
            member_data["email"] = email_match.group(0)

        # Phone extraction (Belgian phone pattern)
        phone_match = re.search(r"[\+]?[\s]?(\d{1,3})[\s]?\(?\d{1,4}\)?[\s]?\d{1,4}[\s]?\d{1,9}", text)
        if phone_match:
            member_data["phone"] = phone_match.group(0).strip()

        return member_data

    def get_next_page_url(self, current_page: str, page_num: int) -> Optional[str]:
        """Find the URL for the next page."""
        soup = BeautifulSoup(current_page, "lxml")

        # Look for "next" link in pagination
        next_link = soup.find("a", class_=lambda x: x and "next" in x.lower())
        if next_link and next_link.get("href"):
            href = next_link.get("href")
            if not href.startswith("http"):
                href = urljoin(BASE_URL, href)
            return href

        # Alternative: look for page numbers
        pagination = soup.find("nav", class_="pagination")
        if pagination:
            links = pagination.find_all("a")
            for link in links:
                link_text = link.get_text(strip=True)
                if link_text == str(page_num + 1):
                    href = link.get("href")
                    if not href.startswith("http"):
                        href = urljoin(BASE_URL, href)
                    return href

        # Alternative: try common pagination patterns
        # Many sites use ?page=X or /page/X
        if "?" in current_page:
            # Has query string
            next_url = f"{current_page}&page={page_num + 1}"
        elif "/page/" in current_page:
            # Has /page/X pattern
            next_url = current_page.replace(f"/page/{page_num}/", f"/page/{page_num + 1}/")
        else:
            next_url = None

        return next_url if next_url != current_page else None

    def crawl_all_pages(self) -> List[Dict]:
        """Crawl all pages of the members directory."""
        current_url = MEMBERS_PAGE_URL
        page_num = 1

        while current_url and page_num <= MAX_PAGES:
            try:
                html = self.fetch_page(current_url)
                save_html(current_url, html)

                page_members = self.extract_members_from_page(html, page_num)
                self.members.extend(page_members)

                # Get next page URL
                next_url = self.get_next_page_url(html, page_num)
                if not next_url or next_url == current_url:
                    self.logger.info("Reached last page")
                    break

                current_url = next_url
                page_num += 1
                time.sleep(REQUEST_DELAY)

            except requests.RequestException as e:
                self.logger.error(f"Error fetching page {page_num}: {e}")
                break

        return self.members

    def validate_urls(self) -> int:
        """Validate that profile URLs are accessible."""
        valid_count = 0
        invalid_count = 0

        for member in self.members:
            if not member.get("profile_url"):
                continue

            try:
                response = self.session.head(
                    member["profile_url"],
                    timeout=5,
                    allow_redirects=True
                )
                if response.status_code == 200:
                    valid_count += 1
                    member["url_validation_status"] = "valid"
                else:
                    invalid_count += 1
                    member["url_validation_status"] = f"http_{response.status_code}"
                    self.logger.warning(
                        f"Invalid status for {member['name']}: "
                        f"{response.status_code}"
                    )
            except requests.RequestException as e:
                invalid_count += 1
                member["url_validation_status"] = "unreachable"
                self.logger.warning(
                    f"Cannot validate URL for {member['name']}: {e}"
                )

        self.logger.info(
            f"URL validation: {valid_count} valid, {invalid_count} invalid"
        )
        return valid_count

    def save_to_toml(self, output_path: str = OUTPUT_FILE):
        """Save members to TOML file with provenance metadata."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        doc = tomlkit.document()
        doc.add(tomlkit.comment("LifeTech Brussels Member Directory"))
        doc.add(tomlkit.comment("Extracted from: https://lifetech.brussels/en/members-2/"))
        doc.add(tomlkit.comment(f"Total members: {len(self.members)}"))

        members_table = tomlkit.table()
        members_table.add(
            tomlkit.comment("Extraction metadata"),
        )

        for i, member in enumerate(self.members, 1):
            member_key = f"member_{i:03d}"
            member_table = tomlkit.table()

            # Basic info
            member_table["name"] = member.get("name") or ""
            member_table["profile_url"] = member.get("profile_url") or ""
            member_table["website"] = member.get("website") or ""
            member_table["email"] = member.get("email") or ""
            member_table["phone"] = member.get("phone") or ""
            member_table["description"] = member.get("description") or ""
            member_table["location"] = member.get("location") or ""

            # Validation info
            member_table["url_validation_status"] = member.get(
                "url_validation_status",
                "not_checked"
            )

            # Provenance
            provenance = Provenance(
                source="lifetech_profile",
                confidence="high",
                extraction_method="beautifulsoup_css_select"
            )
            member_table["_provenance"] = provenance.to_dict()

            members_table[member_key] = member_table

        doc["members"] = members_table

        # Write to file
        with open(output_path, "w") as f:
            f.write(tomlkit.dumps(doc))

        self.logger.info(f"Saved {len(self.members)} members to {output_path}")
        return output_path


def main():
    """Main extraction pipeline."""
    setup_logging("INFO")
    logger.info("Starting LifeTech member extraction...")

    extractor = LifeTechMemberExtractor()

    # Crawl all pages
    logger.info(f"Crawling members directory from {MEMBERS_PAGE_URL}")
    extractor.crawl_all_pages()

    if not extractor.members:
        logger.error("No members extracted. Aborting.")
        return 1

    logger.info(f"Extracted {len(extractor.members)} members")

    # Validate URLs
    valid_count = extractor.validate_urls()

    # Save results
    output_file = extractor.save_to_toml()

    # Summary
    logger.info("=" * 60)
    logger.info("Extraction Complete")
    logger.info(f"Total members: {len(extractor.members)}")
    logger.info(f"Valid profile URLs: {valid_count}")
    logger.info(f"Output file: {output_file}")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
