#!/usr/bin/env python3
"""
Comprehensive test suite for LifeTech extraction pipeline.
Tests module imports, data structures, and basic functionality.
"""

import sys
import unittest
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))


class TestImports(unittest.TestCase):
    """Test all modules import correctly."""

    def test_utils_import(self):
        """Test utils module imports."""
        from utils import (
            setup_logging,
            get_mistral_client,
            retry_on_failure,
            ensure_directory,
            save_html,
            load_html,
            init_database,
            Provenance,
            DataQualityIssue
        )
        self.assertIsNotNone(setup_logging)

    def test_extract_lifetech_import(self):
        """Test extract_lifetech_members module."""
        from extract_lifetech_members import LifeTechMemberExtractor
        self.assertIsNotNone(LifeTechMemberExtractor)

    def test_fetch_websites_import(self):
        """Test fetch_member_websites module."""
        from fetch_member_websites import MemberWebsiteFetcher
        self.assertIsNotNone(MemberWebsiteFetcher)

    def test_extraction_import(self):
        """Test extract_company_data module."""
        from extract_company_data import CompanyDataExtractor
        self.assertIsNotNone(CompanyDataExtractor)

    def test_export_import(self):
        """Test export_for_map module."""
        # Note: This may fail if geopy is not installed, which is OK
        try:
            from export_for_map import MapDataExporter
            self.assertIsNotNone(MapDataExporter)
        except ImportError as e:
            self.skipTest(f"Optional dependency not available: {e}")


class TestDataStructures(unittest.TestCase):
    """Test data structure classes."""

    def test_provenance_structure(self):
        """Test Provenance data class."""
        from utils import Provenance

        prov = Provenance(
            source="test_source",
            confidence="high",
            extraction_method="test_method"
        )

        prov_dict = prov.to_dict()
        self.assertIn("source", prov_dict)
        self.assertIn("confidence", prov_dict)
        self.assertIn("timestamp", prov_dict)
        self.assertEqual(prov_dict["source"], "test_source")

    def test_data_quality_issue_structure(self):
        """Test DataQualityIssue class."""
        from utils import DataQualityIssue

        issue = DataQualityIssue(
            member_id="test_001",
            member_name="Test Corp",
            severity="HIGH",
            issue_type="missing_website",
            description="No website URL found",
            remediation="Add website URL manually"
        )

        issue_dict = issue.to_dict()
        self.assertIn("member_id", issue_dict)
        self.assertIn("severity", issue_dict)
        self.assertEqual(issue_dict["severity"], "HIGH")


class TestUtilities(unittest.TestCase):
    """Test utility functions."""

    def test_logging_setup(self):
        """Test logging setup."""
        from utils import setup_logging
        logger = setup_logging("DEBUG")
        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, "lifetech_extraction")

    def test_directory_creation(self):
        """Test ensure_directory utility."""
        from utils import ensure_directory
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir) / "test" / "nested" / "path"
            result = ensure_directory(str(test_path))
            self.assertTrue(result.exists())
            self.assertTrue(result.is_dir())

    def test_html_parsing(self):
        """Test HTML parsing utility."""
        from utils import parse_html

        html = "<html><body><h1>Test</h1><p>Content</p></body></html>"
        soup = parse_html(html)
        self.assertIsNotNone(soup)
        h1 = soup.find("h1")
        self.assertEqual(h1.get_text(strip=True), "Test")

    def test_database_initialization(self):
        """Test database initialization."""
        from utils import init_database
        import tempfile
        import sqlite3

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            conn = init_database(str(db_path))
            self.assertTrue(db_path.exists())

            # Verify tables exist
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in cursor.fetchall()]
            self.assertIn("extractions", tables)
            self.assertIn("website_checks", tables)
            conn.close()


class TestFileStructure(unittest.TestCase):
    """Test project file structure."""

    def test_scripts_exist(self):
        """Test all required scripts exist."""
        scripts_dir = Path(__file__).parent
        required_scripts = [
            "utils.py",
            "extract_lifetech_members.py",
            "fetch_member_websites.py",
            "extract_company_data.py",
            "export_for_map.py",
            "model_comparison_report.py",
            "run_full_pipeline.py",
        ]

        for script in required_scripts:
            script_path = scripts_dir / script
            self.assertTrue(
                script_path.exists(),
                f"Missing script: {script}"
            )

    def test_config_files_exist(self):
        """Test required config files exist."""
        project_root = Path(__file__).parent.parent
        required_files = [
            "requirements.txt",
            ".env.template",
            "lifetech.brussels/map.html",
        ]

        for file_path in required_files:
            full_path = project_root / file_path
            self.assertTrue(
                full_path.exists(),
                f"Missing file: {file_path}"
            )


class TestIntegration(unittest.TestCase):
    """Integration tests."""

    def test_member_extractor_initialization(self):
        """Test LifeTechMemberExtractor can be initialized."""
        from extract_lifetech_members import LifeTechMemberExtractor

        extractor = LifeTechMemberExtractor()
        self.assertIsNotNone(extractor.session)
        self.assertEqual(len(extractor.members), 0)

    def test_website_fetcher_initialization(self):
        """Test MemberWebsiteFetcher can be initialized."""
        from fetch_member_websites import MemberWebsiteFetcher

        fetcher = MemberWebsiteFetcher()
        self.assertIsNotNone(fetcher.session)
        self.assertIsNotNone(fetcher.db)

    def test_company_data_extractor_initialization(self):
        """Test CompanyDataExtractor can be initialized."""
        from extract_company_data import CompanyDataExtractor

        extractor = CompanyDataExtractor()
        self.assertIsNotNone(extractor.db)
        self.assertEqual(len(extractor.members), 0)


def run_tests(verbosity: int = 2) -> int:
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestImports))
    suite.addTests(loader.loadTestsFromTestCase(TestDataStructures))
    suite.addTests(loader.loadTestsFromTestCase(TestUtilities))
    suite.addTests(loader.loadTestsFromTestCase(TestFileStructure))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
