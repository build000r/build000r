import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "check_portfolio_readme.py"
SPEC = importlib.util.spec_from_file_location("check_portfolio_readme", MODULE_PATH)
check_portfolio_readme = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = check_portfolio_readme
SPEC.loader.exec_module(check_portfolio_readme)


class PortfolioReadmeTests(unittest.TestCase):
    def test_manifest_section_titles_are_used_for_policy_enforcement(self):
        manifest = {
            "sections": [
                {"title": "Primary"},
                {"title": "Experiments"},
            ]
        }
        readme_text = """\
**finance** -- ai-powered accounting infrastructure

### primary

**[public app](https://example.com/public)** -- linked entry.

### experiments

**secret app** -- unlinked experimental entry.

### source of truth
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            readme = Path(tmpdir) / "README.md"
            readme.write_text(readme_text, encoding="utf-8")

            entries, _urls = check_portfolio_readme.parse_entries(
                readme, check_portfolio_readme.manifest_section_titles(manifest)
            )

        errors = check_portfolio_readme.check_unlinked_entries(
            entries, {"intentionally_unlinked": {}, "link_overrides": {}}
        )

        self.assertEqual(["public app", "secret app"], [entry.name for entry in entries])
        self.assertEqual(1, len(errors))
        self.assertIn("'secret app' needs an intentional-private reason", errors[0])

    def test_cli_defaults_work_outside_repo_root(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [sys.executable, str(MODULE_PATH), "--offline"],
                cwd=tmpdir,
                check=False,
                text=True,
                capture_output=True,
            )

        self.assertEqual("", result.stderr)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("portfolio README check passed", result.stdout)

    def test_entry_parsing_stops_at_source_of_truth_boundary(self):
        manifest = {
            "sections": [
                {"title": "Primary"},
            ]
        }
        readme_text = """\
### primary

**[public app](https://example.com/public)** -- linked entry.

### source of truth

### primary

**internal docs** -- this heading is outside the portfolio block.

See [docs](https://example.com/docs).
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            readme = Path(tmpdir) / "README.md"
            readme.write_text(readme_text, encoding="utf-8")

            entries, urls = check_portfolio_readme.parse_entries(
                readme, check_portfolio_readme.manifest_section_titles(manifest)
            )

        errors = check_portfolio_readme.check_unlinked_entries(
            entries, {"intentionally_unlinked": {}, "link_overrides": {}}
        )

        self.assertEqual(["public app"], [entry.name for entry in entries])
        self.assertEqual(
            ["https://example.com/docs", "https://example.com/public"], urls
        )
        self.assertEqual([], errors)


if __name__ == "__main__":
    unittest.main()
