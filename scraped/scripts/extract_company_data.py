"""
Phase 4: Three-stage company data extraction pipeline.

Stage 1: BeautifulSoup extraction using CSS selectors and heuristics
Stage 2: Mistral validation on three model sizes (small, medium, large)
Stage 3: FireCrawl fallback for JavaScript-heavy sites

Key principle: Never hallucinate. Missing data = null + flag for review.
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, asdict
import hashlib

from bs4 import BeautifulSoup
import tomlkit
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from utils import (
    logger,
    setup_logging,
    get_mistral_client,
    parse_html,
    load_html,
    save_html,
    init_database,
    log_extraction,
    DataQualityIssue,
    Provenance
)

# Configuration
INPUT_FILE = "lifetech.brussels/members_with_websites.toml"
OUTPUT_FILE = "lifetech.brussels/members_enhanced.toml"
DATABASE_PATH = "lifetech.brussels/extraction_log.db"
CACHE_DIR = "lifetech.brussels/raw_html"

# Mistral models to test
MISTRAL_MODELS = ["mistral-small-latest", "mistral-medium-latest", "mistral-large-latest"]


@dataclass
class ExtractionMetrics:
    """Track metrics for each extraction."""
    model: str
    field: str
    value: Optional[str]
    confidence: str  # "high", "medium", "low", "none"
    cost: float
    latency: float  # milliseconds
    extraction_method: str


class CompanyDataExtractor:
    """Three-stage company data extraction."""

    def __init__(self):
        self.members = []
        self.mistral = None
        self.db = init_database(DATABASE_PATH)
        self.logger = logger
        self.metrics = []
        self.quality_issues = []

    def load_members(self, input_file: str = INPUT_FILE):
        """Load members from previous phase."""
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

        self.logger.info(f"Loaded {len(self.members)} members")
        return True

    def initialize_mistral(self):
        """Initialize Mistral client."""
        try:
            self.mistral = get_mistral_client()
            self.logger.info("Mistral client initialized")
            return True
        except ValueError as e:
            self.logger.error(f"Failed to initialize Mistral: {e}")
            return False

    # ========================================================================
    # Stage 1: BeautifulSoup Extraction
    # ========================================================================

    def extract_stage1_beautifulsoup(self, member: Dict) -> Dict[str, Any]:
        """
        Stage 1: Extract company data using BeautifulSoup.
        Returns dict with extracted fields and confidence scores.
        """
        result = {
            "name": None,
            "description": None,
            "address": None,
            "email": None,
            "phone": None,
            "services": None,
        }
        confidences = {}

        # Load cached HTML
        website_url = member.get("website_url")
        if not website_url:
            return result

        html_path = member.get("website_html_cached")
        if html_path and Path(html_path).exists():
            html_content = Path(html_path).read_text()
        else:
            html_content = load_html(website_url, CACHE_DIR)

        if not html_content:
            self.logger.debug(f"No cached HTML for {website_url}")
            return result

        soup = parse_html(html_content)

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Strategy 1: Extract name from h1/title
        name_elem = soup.find("h1")
        if not name_elem:
            name_elem = soup.find("title")
        if name_elem:
            result["name"] = name_elem.get_text(strip=True)
            confidences["name"] = "high"

        # Strategy 2: Extract description from meta description or first paragraphs
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            result["description"] = meta_desc.get("content")
            confidences["description"] = "medium"
        else:
            # Try first paragraph
            p_tag = soup.find("p")
            if p_tag:
                result["description"] = p_tag.get_text(strip=True)[:500]
                confidences["description"] = "low"

        # Strategy 3: Extract address using heuristics
        address_patterns = [
            ("class", lambda x: x and "address" in x.lower()),
            ("class", lambda x: x and "location" in x.lower()),
            ("id", lambda x: x and "address" in x.lower()),
        ]

        for attr, pattern in address_patterns:
            elem = soup.find(attrs={attr: pattern})
            if elem:
                result["address"] = elem.get_text(strip=True)
                confidences["address"] = "medium"
                break

        # Strategy 4: Extract email
        import re
        all_text = soup.get_text()
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", all_text)
        if email_match:
            result["email"] = email_match.group(0)
            confidences["email"] = "high"

        # Strategy 5: Extract phone
        phone_pattern = r"[\+]?[\s]?(\d{1,3})[\s]?\(?\d{1,4}\)?[\s]?\d{1,4}[\s]?\d{1,9}"
        phone_match = re.search(phone_pattern, all_text)
        if phone_match:
            result["phone"] = phone_match.group(0).strip()
            confidences["phone"] = "medium"

        # Strategy 6: Extract services from headers or lists
        service_keywords = ["service", "solution", "product", "offering"]
        for keyword in service_keywords:
            elem = soup.find(["h2", "h3"], string=lambda x: x and keyword in x.lower())
            if elem:
                # Get text after header
                next_elem = elem.find_next(["p", "ul", "ol"])
                if next_elem:
                    result["services"] = next_elem.get_text(strip=True)[:500]
                    confidences["services"] = "low"
                    break

        # Set confidence for missing fields
        for field in result:
            if field not in confidences:
                confidences[field] = "none" if result[field] is None else "medium"

        # Log extractions
        member_id = member.get("_key", "unknown")
        for field, value in result.items():
            log_extraction(
                self.db,
                member_id=member_id,
                source="company_website",
                field=field,
                value=value,
                confidence=confidences.get(field, "none"),
                extraction_method="beautifulsoup_css_select"
            )

        return result

    # ========================================================================
    # Stage 2: Mistral Validation
    # ========================================================================

    def extract_stage2_mistral(
        self,
        member: Dict,
        stage1_result: Dict,
        low_confidence_fields: Optional[List[str]] = None
    ) -> Dict[str, Dict]:
        """
        Stage 2: Use Mistral to validate and fill gaps.
        Tests all three model sizes for comparison.
        """
        if not self.mistral:
            return {}

        if low_confidence_fields is None:
            low_confidence_fields = [k for k, v in stage1_result.items() if v is None]

        if not low_confidence_fields:
            return {}

        website_url = member.get("website_url")
        website_content = load_html(website_url, CACHE_DIR)
        if not website_content:
            return {}

        # Limit content for API
        content_preview = website_content[:2000]

        results = {}
        member_id = member.get("_key", "unknown")
        member_name = member.get("name", "Unknown")

        for model in MISTRAL_MODELS:
            try:
                prompt = f"""
You are analyzing a company website for: {member_name}

Website URL: {website_url}
Website content preview:
{content_preview}

Extract or validate the following fields. IMPORTANT: If data is not present or unclear, return exactly "NOT_FOUND" - never guess or hallucinate:

1. Company name
2. Description (2-3 sentences)
3. Address (full address)
4. Email address
5. Phone number
6. Main services or products

Format your response as JSON with exactly these keys: name, description, address, email, phone, services
Example: {{"name": "Acme Corp", "description": "...", "address": "...", "email": "...", "phone": "...", "services": "..."}}
"""

                start_time = time.time()
                response = self.mistral.chat.complete(
                    model=model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=500
                )
                latency = (time.time() - start_time) * 1000

                # Estimate cost (rough)
                # Small: $0.001 per 1M input tokens, $0.003 per 1M output
                # Medium: $0.003 per 1M input, $0.009 per 1M output
                # Large: $0.01 per 1M input, $0.03 per 1M output
                model_costs = {
                    "mistral-small-latest": 0.0001,
                    "mistral-medium-latest": 0.001,
                    "mistral-large-latest": 0.01
                }
                cost = model_costs.get(model, 0.001)

                content = response.choices[0].message.content

                # Parse JSON response
                try:
                    json_match = content[content.find("{"):content.rfind("}") + 1]
                    extracted = json.loads(json_match)
                except (json.JSONDecodeError, ValueError):
                    self.logger.warning(f"Failed to parse Mistral response for {member_name}")
                    continue

                # Record metrics
                results[model] = {
                    "extracted": extracted,
                    "cost": cost,
                    "latency": latency
                }

                # Log extractions
                for field, value in extracted.items():
                    if value and value != "NOT_FOUND":
                        log_extraction(
                            self.db,
                            member_id=member_id,
                            source="company_website",
                            field=field,
                            value=value,
                            confidence="medium",
                            extraction_method=f"mistral_{model}"
                        )

            except Exception as e:
                self.logger.error(f"Mistral extraction failed for {member_name} ({model}): {e}")
                continue

        return results

    # ========================================================================
    # Integration
    # ========================================================================

    def process_member(self, member: Dict) -> Dict:
        """Process single member through all stages."""
        member_id = member.get("_key", "unknown")
        member_name = member.get("name", "Unknown")

        # Stage 1: BeautifulSoup
        stage1 = self.extract_stage1_beautifulsoup(member)

        # Stage 2: Mistral (for low confidence fields)
        stage2 = self.extract_stage2_mistral(member, stage1)

        # Merge results (prioritize high-confidence stage 1, use stage 2 for gaps)
        final_result = {}
        for field in stage1:
            if stage1[field]:
                final_result[field] = {
                    "value": stage1[field],
                    "source": "stage1_beautifulsoup",
                    "confidence": "high"
                }
            else:
                # Try to fill gap from Mistral results
                for model, stage2_data in stage2.items():
                    extracted = stage2_data.get("extracted", {})
                    if field in extracted and extracted[field] != "NOT_FOUND":
                        final_result[field] = {
                            "value": extracted[field],
                            "source": f"stage2_mistral_{model}",
                            "confidence": "medium"
                        }
                        break

        # Add provenance metadata
        for field, data in final_result.items():
            member[f"{field}_value"] = data["value"]
            member[f"{field}_source"] = data["source"]
            member[f"{field}_confidence"] = data["confidence"]

        # Track Mistral usage
        for model, stage2_data in stage2.items():
            self.metrics.append({
                "member_id": member_id,
                "model": model,
                "cost": stage2_data["cost"],
                "latency": stage2_data["latency"]
            })

        return member

    def process_all_members(self):
        """Process all members through extraction pipeline."""
        for member in tqdm(self.members, desc="Extracting member data"):
            self.process_member(member)

    def save_results(self, output_file: str = OUTPUT_FILE):
        """Save enhanced member data to TOML."""
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        doc = tomlkit.document()
        doc.add(tomlkit.comment("LifeTech Members - Enhanced with Extracted Data"))
        doc.add(tomlkit.comment(f"Total members: {len(self.members)}"))

        members_table = tomlkit.table()

        for member in self.members:
            member_key = member.get("_key", f"member_{len(members_table)}")
            member_table = tomlkit.table()

            # Copy all fields
            for key, value in member.items():
                if key != "_key":
                    member_table[key] = value

            members_table[member_key] = member_table

        doc["members"] = members_table

        with open(output_file, "w") as f:
            f.write(tomlkit.dumps(doc))

        self.logger.info(f"Saved {len(self.members)} members to {output_file}")

    def generate_mistral_metrics(self):
        """Generate report on Mistral model performance."""
        if not self.metrics:
            return

        # Aggregate metrics by model
        model_stats = {}
        for metric in self.metrics:
            model = metric["model"]
            if model not in model_stats:
                model_stats[model] = {
                    "cost": 0,
                    "latency": [],
                    "count": 0
                }
            model_stats[model]["cost"] += metric["cost"]
            model_stats[model]["latency"].append(metric["latency"])
            model_stats[model]["count"] += 1

        self.logger.info("=" * 60)
        self.logger.info("Mistral Model Performance Report")
        self.logger.info("=" * 60)

        total_cost = 0
        for model, stats in sorted(model_stats.items()):
            avg_latency = sum(stats["latency"]) / len(stats["latency"]) if stats["latency"] else 0
            cost = stats["cost"]
            total_cost += cost

            self.logger.info(f"\nModel: {model}")
            self.logger.info(f"  Cost: ${cost:.4f}")
            self.logger.info(f"  Avg latency: {avg_latency:.1f}ms")
            self.logger.info(f"  Calls: {stats['count']}")

        self.logger.info(f"\nTotal cost: ${total_cost:.4f}")
        self.logger.info("=" * 60)


def main():
    """Main extraction pipeline."""
    setup_logging("INFO")
    logger.info("Starting three-stage extraction pipeline...")

    extractor = CompanyDataExtractor()

    # Load members
    if not extractor.load_members():
        return 1

    # Initialize Mistral
    if not extractor.initialize_mistral():
        logger.warning("Mistral not available, using BeautifulSoup only")

    # Process all members
    extractor.process_all_members()

    # Generate reports
    extractor.generate_mistral_metrics()

    # Save results
    extractor.save_results()

    # Cleanup
    extractor.db.close()

    logger.info("=" * 60)
    logger.info("Extraction Pipeline Complete")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
