import importlib.util
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "scripts"
    / "release_documentation.py"
)
SPEC = importlib.util.spec_from_file_location("release_documentation", SCRIPT)
release_documentation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release_documentation)


class SelectReleaseTests(unittest.TestCase):
    def setUp(self):
        self.releases = [
            {"tag_name": "v2.8.2", "prerelease": False},
            {"tag_name": "v2.8.10", "prerelease": False},
            {"tag_name": "v2.8.11", "prerelease": True},
            {"tag_name": "v2.9.0", "prerelease": False},
            {"tag_name": "v3.8.0", "prerelease": False},
            {"tag_name": "not-a-version", "prerelease": False},
        ]

    def test_selects_highest_production_patch_for_same_major_and_minor(self):
        selected = release_documentation.select_release(
            self.releases, "v2.8.12", False
        )
        self.assertEqual(selected["tag_name"], "v2.8.10")

    def test_selects_matching_prerelease_only(self):
        selected = release_documentation.select_release(
            self.releases, "v2.8.12", True
        )
        self.assertEqual(selected["tag_name"], "v2.8.11")

    def test_returns_none_when_no_release_matches(self):
        self.assertIsNone(
            release_documentation.select_release(self.releases, "v2.7.1", False)
        )

    def test_rejects_non_semver_release_tag(self):
        with self.assertRaises(ValueError):
            release_documentation.select_release(self.releases, "v2.8-beta", False)

    def test_selects_latest_by_numeric_patch_version(self):
        releases = [
            {"tag_name": "v2.8.9", "prerelease": False},
            {"tag_name": "v2.8.10", "prerelease": False},
        ]
        selected = release_documentation.select_release(releases, "v2.8.11", False)
        self.assertEqual(selected["tag_name"], "v2.8.10")

    def test_requires_release_links_in_generated_document(self):
        components = [
            {
                "html_url": "https://github.com/studio27se/ehub-backend-api/releases/tag/v2.8.10"
            },
            {"html_url": None},
        ]
        document = """# **Release Dokumentation – Version 2.8.12**
**Datum:** 2026-10-09
## **Summering**
## **Nyheter och Förbättringar**
### **Backend (Version 2.8.10)**
### **Webbapp (Version 2.8.12)**
### **Mobilapp (Version 2.8.12)**
"""
        with self.assertRaisesRegex(RuntimeError, "omitted changelog links"):
            release_documentation.validate_document(
                document, "2.8.12", "2026-10-09", components
            )


if __name__ == "__main__":
    unittest.main()
