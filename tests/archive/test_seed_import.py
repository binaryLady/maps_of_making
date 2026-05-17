#!/usr/bin/env python3

import json
import unittest
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock, patch

import seed_import


class TestSpaceId(unittest.TestCase):
    """Test ID generation stability and uniqueness."""

    def test_id_stability(self):
        """Same input produces same ID."""
        entry1 = {
            "schema:name": "FabLab",
            "schema:address": {"schema:addressLocality": "Paris"},
        }
        entry2 = {
            "schema:name": "FabLab",
            "schema:address": {"schema:addressLocality": "Paris"},
        }
        self.assertEqual(seed_import.space_id(entry1), seed_import.space_id(entry2))

    def test_id_uniqueness(self):
        """Different inputs produce different IDs."""
        entry1 = {
            "schema:name": "FabLab",
            "schema:address": {"schema:addressLocality": "Paris"},
        }
        entry2 = {
            "schema:name": "MakerSpace",
            "schema:address": {"schema:addressLocality": "Berlin"},
        }
        self.assertNotEqual(seed_import.space_id(entry1), seed_import.space_id(entry2))

    def test_id_case_insensitive(self):
        """Case differences don't matter for ID."""
        entry1 = {
            "schema:name": "FabLab",
            "schema:address": {"schema:addressLocality": "Paris"},
        }
        entry2 = {
            "schema:name": "fablab",
            "schema:address": {"schema:addressLocality": "paris"},
        }
        self.assertEqual(seed_import.space_id(entry1), seed_import.space_id(entry2))

    def test_id_length(self):
        """Generated ID is 12 characters."""
        entry = {
            "schema:name": "Test",
            "schema:address": {"schema:addressLocality": "City"},
        }
        self.assertEqual(len(seed_import.space_id(entry)), 12)


class TestSparqlStr(unittest.TestCase):
    """Test SPARQL string literal escaping."""

    def test_simple_string(self):
        """Simple strings are quoted."""
        self.assertEqual(seed_import.sparql_str("hello"), '"hello"')

    def test_quote_escaping(self):
        """Quotes are properly escaped."""
        result = seed_import.sparql_str('say "hi"')
        self.assertIn('\\"', result)

    def test_backslash_escaping(self):
        """Backslashes are properly escaped."""
        result = seed_import.sparql_str("path\\to\\file")
        self.assertIn("\\\\", result)

    def test_none_value(self):
        """None becomes empty string."""
        self.assertEqual(seed_import.sparql_str(None), '""')


class TestGraphExists(unittest.TestCase):
    """Test SPARQL ASK query for graph existence."""

    def test_graph_exists_true(self):
        """Returns True when ASK response is true."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"boolean": True}
        mock_client.post.return_value = mock_response

        result = seed_import.graph_exists(mock_client, "urn:test:graph")
        self.assertTrue(result)

    def test_graph_exists_false(self):
        """Returns False when ASK response is false."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"boolean": False}
        mock_client.post.return_value = mock_response

        result = seed_import.graph_exists(mock_client, "urn:test:graph")
        self.assertFalse(result)

    def test_graph_exists_raises_on_error(self):
        """Raises when HTTP request fails."""
        import httpx

        mock_client = MagicMock()
        mock_client.post.side_effect = httpx.HTTPError("Connection failed")

        with self.assertRaises(httpx.HTTPError):
            seed_import.graph_exists(mock_client, "urn:test:graph")


class TestBuildVowInsert(unittest.TestCase):
    """Test SPARQL INSERT generation for VOW entries."""

    def test_vow_entry_all_fields(self):
        """VOW entry with all fields produces correct SPARQL."""
        entry = {
            "schema:name": "FabLab",
            "schema:address": {
                "schema:addressLocality": "Paris",
                "schema:addressCountry": "France",
            },
            "schema:geo": {"schema:latitude": 48.8566, "schema:longitude": 2.3522},
            "schema:url": "https://fablab.paris",
            "mom:profileUrl": "https://example.com/fablab",
            "schema:knowsAbout": ["3D printing", "CNC"],
            "mom:source": "mak:scraped-vow",
            "mom:freshnessStatus": "mak:seeded",
            "mom:geolocationFidelity": "precise",
        }

        graph_uri, insert_query = seed_import.build_vow_insert(entry)

        # Check graph URI format
        self.assertTrue(graph_uri.startswith("urn:mak:space/"))
        self.assertEqual(len(graph_uri.split("/")[-1]), 12)

        # Check INSERT query contains expected elements
        self.assertIn("INSERT DATA", insert_query)
        self.assertIn("mom:MakerSpace", insert_query)
        self.assertIn("FabLab", insert_query)
        self.assertIn("Paris", insert_query)
        self.assertIn("France", insert_query)
        self.assertIn("48.8566", insert_query)
        self.assertIn("2.3522", insert_query)
        self.assertIn("3D printing", insert_query)

    def test_vow_entry_minimal_fields(self):
        """VOW entry with only required fields."""
        entry = {
            "schema:name": "Space",
            "schema:address": {"schema:addressLocality": "City"},
            "schema:geo": {"schema:latitude": 0.0, "schema:longitude": 0.0},
            "mom:source": "mak:scraped-vow",
            "mom:freshnessStatus": "mak:seeded",
            "mom:geolocationFidelity": "approximate",
        }

        graph_uri, insert_query = seed_import.build_vow_insert(entry)

        self.assertTrue(graph_uri.startswith("urn:mak:space/"))
        self.assertIn("INSERT DATA", insert_query)
        self.assertIn("Space", insert_query)


class TestBuildRffInsert(unittest.TestCase):
    """Test SPARQL INSERT generation for RFF entries."""

    def test_rff_entries_single_graph(self):
        """All RFF entries go into shared named graph."""
        entries = [
            {
                "@id": "rff-001",
                "schema:name": "Maison A",
                "schema:address": {"schema:addressLocality": "Lyon"},
                "schema:geo": {"schema:latitude": 45.75, "schema:longitude": 4.84},
                "mom:source": "mak:rff-mockup",
                "mom:freshnessStatus": "mak:seeded",
                "mom:healthState": "mak:seeded",
            }
        ]

        graph_uri, insert_query = seed_import.build_rff_insert(entries)

        self.assertEqual(graph_uri, "urn:mak:mock/rff-health")
        self.assertIn("INSERT DATA", insert_query)
        self.assertIn("Maison A", insert_query)

    def test_rff_entries_with_health_state(self):
        """RFF entries preserve health state triples."""
        entries = [
            {
                "@id": "rff-002",
                "schema:name": "Healthy Space",
                "schema:address": {"schema:addressLocality": "Paris"},
                "schema:geo": {"schema:latitude": 48.8, "schema:longitude": 2.35},
                "mom:source": "mak:rff-mockup",
                "mom:freshnessStatus": "mak:confirmed",
                "mom:healthState": "mak:confirmed",
                "mom:lastFetched": "2026-04-24T12:00:00Z",
            }
        ]

        graph_uri, insert_query = seed_import.build_rff_insert(entries)

        self.assertEqual(graph_uri, "urn:mak:mock/rff-health")
        self.assertIn("mom:healthState", insert_query)
        self.assertIn("mom:lastFetched", insert_query)

    def test_rff_entries_with_error(self):
        """RFF error entries include lastFetchError."""
        entries = [
            {
                "@id": "rff-error",
                "schema:name": "Broken Space",
                "schema:address": {"schema:addressLocality": "Berlin"},
                "schema:geo": {"schema:latitude": 52.5, "schema:longitude": 13.4},
                "mom:source": "mak:rff-mockup",
                "mom:freshnessStatus": "mak:error",
                "mom:healthState": "mak:error",
                "mom:lastFetchError": "Connection timeout",
            }
        ]

        graph_uri, insert_query = seed_import.build_rff_insert(entries)

        self.assertIn("mom:lastFetchError", insert_query)
        self.assertIn("Connection timeout", insert_query)


class TestInsertVowData(unittest.TestCase):
    """Test VOW data insertion logic."""

    @patch("seed_import.graph_exists")
    @patch("seed_import.load_vow_data")
    def test_vow_insertion_success(self, mock_load, mock_graph_exists):
        """Successful VOW insertion returns correct counts."""
        mock_load.return_value = [
            {
                "schema:name": "Space1",
                "schema:address": {"schema:addressLocality": "City1"},
                "schema:geo": {"schema:latitude": 0.0, "schema:longitude": 0.0},
                "mom:source": "mak:scraped-vow",
                "mom:freshnessStatus": "mak:seeded",
                "mom:geolocationFidelity": "precise",
            }
        ]
        mock_graph_exists.return_value = False

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        loaded, skipped, corrupt, failed = seed_import.insert_vow_data(mock_client)

        self.assertEqual(loaded, 1)
        self.assertEqual(skipped, 0)
        self.assertEqual(failed, 0)

    @patch("seed_import.graph_exists")
    @patch("seed_import.load_vow_data")
    def test_vow_counts_corrupt_not_skipped_when_no_geocode(self, mock_load, mock_graph_exists):
        """VOW entries missing schema:geo go into corrupt counter, not skipped — Story 0.1 contract violation."""
        mock_load.return_value = [
            {
                "schema:name": "NoGeoSpace",
                "schema:address": {"schema:addressLocality": "City"},
                "mom:source": "mak:scraped-vow",
                "mom:freshnessStatus": "mak:seeded",
                "mom:geolocationFidelity": "none",
            }
        ]

        mock_client = MagicMock()

        loaded, skipped, corrupt, failed = seed_import.insert_vow_data(mock_client)

        self.assertEqual(loaded, 0)
        self.assertEqual(skipped, 0)
        self.assertEqual(corrupt, 1)  # goes to corrupt, NOT skipped
        self.assertEqual(failed, 0)

    @patch("seed_import.graph_exists")
    @patch("seed_import.load_vow_data")
    def test_vow_skips_existing_graph(self, mock_load, mock_graph_exists):
        """VOW entries in existing graph are skipped."""
        mock_load.return_value = [
            {
                "schema:name": "ExistingSpace",
                "schema:address": {"schema:addressLocality": "City"},
                "schema:geo": {"schema:latitude": 0.0, "schema:longitude": 0.0},
                "mom:source": "mak:scraped-vow",
                "mom:freshnessStatus": "mak:seeded",
                "mom:geolocationFidelity": "precise",
            }
        ]
        mock_graph_exists.return_value = True

        mock_client = MagicMock()

        loaded, skipped, corrupt, failed = seed_import.insert_vow_data(mock_client)

        self.assertEqual(loaded, 0)
        self.assertEqual(skipped, 1)
        self.assertEqual(failed, 0)


class TestInsertRffData(unittest.TestCase):
    """Test RFF data insertion logic."""

    @patch("seed_import.graph_exists")
    @patch("seed_import.load_rff_data")
    def test_rff_insertion_success(self, mock_load, mock_graph_exists):
        """Successful RFF insertion returns correct counts."""
        mock_load.return_value = [
            {
                "@id": "rff-001",
                "schema:name": "Space",
                "schema:address": {"schema:addressLocality": "City"},
                "schema:geo": {"schema:latitude": 0.0, "schema:longitude": 0.0},
                "mom:source": "mak:rff-mockup",
                "mom:freshnessStatus": "mak:seeded",
            }
        ]
        mock_graph_exists.return_value = False

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        loaded, skipped = seed_import.insert_rff_data(mock_client)

        self.assertEqual(loaded, 1)
        self.assertEqual(skipped, 0)

    @patch("seed_import.graph_exists")
    @patch("seed_import.load_rff_data")
    def test_rff_skipped_when_exists(self, mock_load, mock_graph_exists):
        """RFF graph skipped when exists and no --force."""
        mock_load.return_value = [
            {
                "@id": "rff-001",
                "schema:name": "Space",
                "schema:address": {"schema:addressLocality": "City"},
                "schema:geo": {"schema:latitude": 0.0, "schema:longitude": 0.0},
                "mom:source": "mak:rff-mockup",
                "mom:freshnessStatus": "mak:seeded",
            }
        ]
        mock_graph_exists.return_value = True

        mock_client = MagicMock()

        loaded, skipped = seed_import.insert_rff_data(mock_client, force=False)

        self.assertEqual(loaded, 0)
        self.assertEqual(skipped, 1)

    @patch("seed_import.graph_exists")
    @patch("seed_import.load_rff_data")
    def test_rff_reloaded_with_force(self, mock_load, mock_graph_exists):
        """RFF graph reloaded when --force given: CLEAR issued before INSERT."""
        mock_load.return_value = [
            {
                "@id": "rff-001",
                "schema:name": "Space",
                "schema:address": {"schema:addressLocality": "City"},
                "schema:geo": {"schema:latitude": 0.0, "schema:longitude": 0.0},
                "mom:source": "mak:rff-mockup",
                "mom:freshnessStatus": "mak:seeded",
            }
        ]
        mock_graph_exists.return_value = True

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        loaded, skipped = seed_import.insert_rff_data(mock_client, force=True)

        self.assertEqual(loaded, 1)
        self.assertEqual(skipped, 0)
        # Verify CLEAR was the first POST, INSERT DATA was the second
        self.assertEqual(mock_client.post.call_count, 2)
        first_call_data = mock_client.post.call_args_list[0][1]["data"]
        self.assertIn("CLEAR GRAPH", first_call_data)
        second_call_data = mock_client.post.call_args_list[1][1]["data"]
        self.assertIn("INSERT DATA", second_call_data)


class TestMainFunction(unittest.TestCase):
    """Test main script logic."""

    @patch("seed_import.insert_rff_data")
    @patch("seed_import.insert_vow_data")
    @patch("httpx.Client")
    def test_main_success(self, mock_client_class, mock_insert_vow, mock_insert_rff):
        """Main function returns 0 on success."""
        mock_insert_vow.return_value = (10, 2, 0, 0)
        mock_insert_rff.return_value = (29, 0)

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_class.return_value.__exit__ = MagicMock(return_value=False)

        with patch("sys.argv", ["seed_import.py"]):
            result = seed_import.main()

        self.assertEqual(result, 0)

    @patch("seed_import.insert_vow_data")
    @patch("httpx.Client")
    def test_main_failure_on_vow_error(self, mock_client_class, mock_insert_vow):
        """Main function returns 1 on VOW insertion failure."""
        mock_insert_vow.return_value = (10, 2, 0, 1)

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_class.return_value.__exit__ = MagicMock(return_value=False)

        with patch("sys.argv", ["seed_import.py"]):
            result = seed_import.main()

        self.assertEqual(result, 1)

    @patch("httpx.Client")
    def test_main_failure_on_connection_error(self, mock_client_class):
        """Main function returns 1 on connection failure."""
        import httpx

        mock_client_class.side_effect = httpx.ConnectError("Connection failed")

        with patch("sys.argv", ["seed_import.py"]):
            result = seed_import.main()

        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
