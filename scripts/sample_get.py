"""Save one bounded, credential-free Scrapling GET sample for offline analysis."""

import argparse
import hashlib
import json
import logging
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from urllib.parse import urlsplit

MAX_BODY_BYTES = 8 * 1024 * 1024
BODY_TYPES = {
    "html": ("body.html", {"text/html", "application/xhtml+xml"}),
    "javascript": (
        "body.js",
        {"text/javascript", "application/javascript", "application/x-javascript"},
    ),
    "json": ("body.json", {"application/json"}),
}


def public_http_url(value: str) -> str:
    try:
        url = urlsplit(value)
        valid = (
            url.scheme in {"http", "https"}
            and url.hostname
            and url.username is None
            and "#" not in value
            and not any(character.isspace() or ord(character) < 32 for character in value)
        )
        _ = url.port
    except ValueError:
        valid = False
    if not valid:
        raise argparse.ArgumentTypeError("Use an HTTP(S) URL without userinfo or fragments.")
    return value


def fetch_sample(url: str, expected_type: str) -> tuple[str, bytearray, dict]:
    try:
        from curl_cffi import CurlError
        from curl_cffi.curl import CURL_WRITEFUNC_ERROR
        from scrapling.fetchers import Fetcher
    except ImportError as error:
        raise RuntimeError("Install Scrapling with the fetchers extra in a virtual environment.") from error

    body = bytearray()
    limit_exceeded = False

    def receive(chunk: bytes) -> int:
        nonlocal limit_exceeded
        if len(body) + len(chunk) > MAX_BODY_BYTES:
            limit_exceeded = True
            return CURL_WRITEFUNC_ERROR
        body.extend(chunk)
        return len(chunk)

    logging.getLogger("scrapling").disabled = True
    try:
        response = Fetcher.get(
            url,
            content_callback=receive,
            follow_redirects=False,
            impersonate=None,
            stealthy_headers=False,
            timeout=20,
            retries=1,
        )
    except CurlError as error:
        if limit_exceeded:
            raise RuntimeError(f"Response exceeded the {MAX_BODY_BYTES}-byte sample limit.") from error
        raise RuntimeError(f"HTTP request failed (curl code {error.code}).") from error

    if response.status != 200:
        raise RuntimeError(f"Expected HTTP 200, received {response.status}.")

    content_type = response.headers.get("content-type", "").partition(";")[0].strip().lower()
    body_name, media_types = BODY_TYPES[expected_type]
    structured_json = (
        expected_type == "json"
        and content_type.startswith("application/")
        and content_type.endswith("+json")
    )
    if content_type not in media_types and not structured_json:
        raise RuntimeError(f"Response Content-Type does not match {expected_type}.")
    if not body:
        raise RuntimeError("Response body was empty.")

    metadata = {
        "url": response.url,
        "method": "GET",
        "status": response.status,
        "media_type": content_type,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "scrapling_version": version("scrapling"),
        "body_file": body_name,
        "body_bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
    }
    return body_name, body, metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", type=public_http_url, help="Explicit URL containing only non-sensitive values")
    parser.add_argument("output_directory", type=Path, help="New local directory for the body and evidence")
    parser.add_argument("--expect", choices=BODY_TYPES, required=True)
    args = parser.parse_args()

    destination = args.output_directory
    if destination.exists() or destination.is_symlink():
        parser.error("Output directory already exists.")
    if not destination.parent.is_dir():
        parser.error("Output directory parent must exist.")

    try:
        body_name, body, metadata = fetch_sample(args.url, args.expect)
        destination.mkdir()
        body_path = destination / body_name
        evidence_path = destination / "evidence.json"
        try:
            body_path.write_bytes(body)
            evidence_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        except OSError:
            evidence_path.unlink(missing_ok=True)
            body_path.unlink(missing_ok=True)
            destination.rmdir()
            raise
    except (OSError, RuntimeError) as error:
        parser.exit(1, f"{error}\n")

    print(evidence_path.resolve())


if __name__ == "__main__":
    main()
