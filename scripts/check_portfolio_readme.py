#!/usr/bin/env python3
"""Validate build000r portfolio README links, manifest, and private entries."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PORTFOLIO_END_HEADING = "source of truth"
ENTRY_RE = re.compile(
    r"^\*\*(?:\[(?P<linked_name>[^\]]+)\]\((?P<entry_url>https?://[^)]+)\)"
    r"|(?P<plain_name>[^*]+))\*\*\s+--\s+(?P<description>.+)$"
)
HEADING_RE = re.compile(r"^###\s+(?P<heading>.+?)\s*$")
LINK_RE = re.compile(r"\[[^\]]+\]\((?P<url>https?://[^)]+)\)")
REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class PortfolioEntry:
    name: str
    url: str | None
    line: int

    @property
    def normalized_name(self) -> str:
        return normalize_name(self.name)


def normalize_name(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def load_policy(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        policy = json.load(handle)
    policy.setdefault("intentionally_unlinked", {})
    policy.setdefault("link_overrides", {})
    return policy


def load_manifest(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def manifest_section_titles(manifest: dict) -> set[str]:
    return {normalize_name(section["title"]) for section in manifest["sections"]}


def link_text(label: str, url: str | None = None, code: bool = False) -> str:
    text = f"`{label}`" if code else label
    if url:
        return f"[{text}]({url})"
    return text


def render_entry(entry: dict) -> list[str]:
    name = entry["name"]
    url = entry.get("url")
    title = f"[{name}]({url})" if url else name
    lines = [f"**{title}** -- {entry['description']}"]

    subitems = entry.get("subitems", [])
    if subitems:
        lines.append("")

    for subitem in subitems:
        label = subitem.get("markdown") or link_text(
            subitem["label"], subitem.get("url"), code=True
        )
        lines.append(f"- {label} -- {subitem['description']}")

    return lines


def render_manifest_portfolio(manifest: dict) -> str:
    lines: list[str] = []

    intro = manifest["intro"]
    intro_link = intro["link"]
    lines.append(
        f"{intro['text']} · [{intro_link['label']}]({intro_link['url']})"
    )
    lines.append("")

    for item in manifest["focus"]:
        lines.append(f"**{item['name']}** -- {item['description']}")
        lines.append("")

    lines.append("---")
    lines.append("")

    for section_index, section in enumerate(manifest["sections"]):
        if section_index:
            lines.append("---")
            lines.append("")

        lines.append(f"### {section['title']}")
        if section.get("note"):
            lines.append(section["note"])
        lines.append("")

        for entry in section["entries"]:
            lines.extend(render_entry(entry))
            lines.append("")

    footer = manifest["footer"]
    footer_link = footer["link"]
    lines.append(
        f"{footer['text']} · [{footer_link['label']}]({footer_link['url']})"
    )

    return "\n".join(lines).rstrip() + "\n"


def read_readme_portfolio_block(readme: Path) -> str:
    lines: list[str] = []
    for line in readme.read_text(encoding="utf-8").splitlines():
        heading = HEADING_RE.match(line)
        if heading and normalize_name(heading.group("heading")) == PORTFOLIO_END_HEADING:
            break
        lines.append(line)
    return "\n".join(lines).rstrip() + "\n"


def check_manifest_matches_readme(readme: Path, manifest: dict) -> list[str]:
    rendered = render_manifest_portfolio(manifest)
    current = read_readme_portfolio_block(readme)
    if rendered == current:
        return []
    return [
        "README.md portfolio block differs from portfolio-manifest.json; "
        "run scripts/check_portfolio_readme.py --render-portfolio and update README.md"
    ]


def parse_entries(
    readme: Path, portfolio_sections: set[str]
) -> tuple[list[PortfolioEntry], list[str]]:
    text = readme.read_text(encoding="utf-8")
    entries: list[PortfolioEntry] = []
    active_section: str | None = None

    for line_number, line in enumerate(text.splitlines(), start=1):
        heading = HEADING_RE.match(line)
        if heading:
            active_section = normalize_name(heading.group("heading"))
            continue

        if active_section not in portfolio_sections:
            continue

        match = ENTRY_RE.match(line)
        if not match:
            continue

        name = match.group("linked_name") or match.group("plain_name")
        entries.append(
            PortfolioEntry(
                name=name,
                url=match.group("entry_url"),
                line=line_number,
            )
        )

    urls = sorted(set(match.group("url") for match in LINK_RE.finditer(text)))
    return entries, urls


def check_unlinked_entries(entries: list[PortfolioEntry], policy: dict) -> list[str]:
    errors: list[str] = []
    allowed = {
        normalize_name(name): reason
        for name, reason in policy["intentionally_unlinked"].items()
    }
    seen_unlinked = {entry.normalized_name for entry in entries if entry.url is None}

    for entry in entries:
        if entry.url is not None:
            continue
        reason = allowed.get(entry.normalized_name)
        if not reason:
            errors.append(
                f"README.md:{entry.line}: unlinked portfolio entry "
                f"{entry.name!r} needs an intentional-private reason"
            )

    for policy_name in sorted(set(allowed) - seen_unlinked):
        errors.append(
            "portfolio-link-policy.json: intentionally_unlinked entry "
            f"{policy_name!r} is not present as an unlinked README entry"
        )

    return errors


def fetch_status(url: str, timeout: float) -> tuple[int | None, str]:
    for method in ("HEAD", "GET"):
        request = Request(
            url,
            method=method,
            headers={"User-Agent": "build000r-readme-check/1.0"},
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                return response.status, method
        except HTTPError as error:
            if method == "HEAD" and error.code in {403, 405}:
                continue
            return error.code, method
        except URLError as error:
            if method == "HEAD":
                continue
            return None, str(error.reason)
        except TimeoutError:
            if method == "HEAD":
                continue
            return None, "timeout"
    return None, "no response"


def check_urls(urls: list[str], policy: dict, timeout: float) -> list[str]:
    errors: list[str] = []
    overrides = policy["link_overrides"]

    for url in urls:
        status, source = fetch_status(url, timeout)
        allowed_statuses = set(range(200, 400))
        override = overrides.get(url)
        if override:
            allowed_statuses.update(int(value) for value in override["allowed_statuses"])

        if status not in allowed_statuses:
            errors.append(
                f"{url}: returned {status or source}; expected 2xx/3xx"
                + (" or configured override" if override else "")
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readme", type=Path, default=REPO_ROOT / "README.md")
    parser.add_argument(
        "--policy",
        type=Path,
        default=REPO_ROOT / "portfolio-link-policy.json",
        help="JSON file listing intentional private/unlinked entries",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=REPO_ROOT / "portfolio-manifest.json",
        help="JSON manifest used to render the README portfolio block",
    )
    parser.add_argument(
        "--render-portfolio",
        action="store_true",
        help="print the README portfolio block rendered from the manifest",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="parse README and policy without fetching links",
    )
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    if args.render_portfolio:
        print(render_manifest_portfolio(manifest), end="")
        return 0

    policy = load_policy(args.policy)
    entries, urls = parse_entries(args.readme, manifest_section_titles(manifest))
    errors = check_manifest_matches_readme(args.readme, manifest)
    errors.extend(check_unlinked_entries(entries, policy))
    if not args.offline:
        errors.extend(check_urls(urls, policy, args.timeout))

    if errors:
        print("portfolio README check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    linked = sum(1 for entry in entries if entry.url)
    unlinked = len(entries) - linked
    link_mode = "offline" if args.offline else f"{len(urls)} links fetched"
    print(
        "portfolio README check passed: "
        f"{linked} linked entries, {unlinked} intentional private entries, "
        f"manifest matches README, {link_mode}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
