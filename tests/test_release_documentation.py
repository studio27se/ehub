import importlib.util
import io
import os
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError


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


class GetReleasesTests(unittest.TestCase):
    def test_reads_public_and_authenticated_releases(self):
        for token in (None, "", "read-only-token"):
            with self.subTest(token=token), patch.object(
                release_documentation,
                "urlopen",
                side_effect=[
                    io.StringIO('[{"tag_name": "v2.30.0"}]'),
                    io.StringIO("[]"),
                ],
            ) as urlopen:
                releases = release_documentation.get_releases(
                    "studio27se/ehub-backend-api", token
                )

                self.assertEqual(releases, [{"tag_name": "v2.30.0"}])
                self.assertEqual(urlopen.call_count, 2)
                for page, call in enumerate(urlopen.call_args_list, start=1):
                    request = call.args[0]
                    self.assertIn(f"page={page}", request.full_url)
                    self.assertEqual(
                        request.get_header("Authorization"),
                        "Bearer " + token if token else None,
                    )

    def test_explains_missing_token_on_not_found(self):
        for token in (None, ""):
            with self.subTest(token=token), patch.object(
                release_documentation,
                "urlopen",
                side_effect=HTTPError("url", 404, "Not Found", {}, None),
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    r"studio27se/ehub-backend-api \(HTTP 404\).*"
                    r"Configure the SUBREPO_READ_TOKEN Actions secret with Contents: read",
                ):
                    release_documentation.get_releases(
                        "studio27se/ehub-backend-api", token
                    )

    def test_explains_insufficient_token_access_on_not_found(self):
        with patch.object(
            release_documentation,
            "urlopen",
            side_effect=HTTPError("url", 404, "Not Found", {}, None),
        ):
            with self.assertRaisesRegex(
                RuntimeError, "Check that SUBREPO_READ_TOKEN has Contents: read access"
            ) as raised:
                release_documentation.get_releases(
                    "studio27se/ehub-backend-api", "read-only-token"
                )
        self.assertNotIn("read-only-token", str(raised.exception))

    def test_preserves_other_http_errors(self):
        error = HTTPError("url", 403, "Forbidden", {}, None)
        with patch.object(release_documentation, "urlopen", side_effect=error):
            with self.assertRaises(HTTPError) as raised:
                release_documentation.get_releases(
                    "studio27se/ehub-backend-api", None
                )
        self.assertIs(raised.exception, error)


class GenerateDocumentTests(unittest.TestCase):
    def test_does_not_pass_subrepository_token_to_copilot(self):
        with patch.dict(
            os.environ,
            {"SUBREPO_READ_TOKEN": "read-only-token", "GITHUB_TOKEN": "copilot-token"},
            clear=True,
        ), patch.object(
            release_documentation.subprocess,
            "run",
            return_value=SimpleNamespace(stdout="generated document"),
        ) as run:
            result = release_documentation.generate_document("prompt")

        environment = run.call_args.kwargs["env"]
        self.assertEqual(result, "generated document")
        self.assertIn("GITHUB_TOKEN", environment)
        self.assertNotIn("SUBREPO_READ_TOKEN", environment)


if __name__ == "__main__":
    unittest.main()
