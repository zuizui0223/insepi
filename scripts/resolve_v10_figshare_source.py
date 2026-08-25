#!/usr/bin/env python3
"""Resolve real-video file metadata for the proposed V10 semi-empirical benchmark.

This is source discovery only. It does not download video bytes, run either
observer, inject perturbations, select V10 evidence, or alter V6/V7/V8/V9.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen


DEFAULT_ARTICLE_ID = 12895433
DEFAULT_DOI = "10.26180/5f4c8d5815940"
API_TEMPLATE = "https://api.figshare.com/v2/articles/{article_id}"
VIDEO_SUFFIXES = (".mp4", ".avi", ".mov", ".mkv", ".m4v")
ARCHIVE_SUFFIXES = (".zip", ".tar", ".tar.gz", ".tgz", ".gz", ".7z")


def fetch_json(url: str) -> dict[str, object]:
    request = Request(url, headers={"User-Agent": "interaction-sensing-v10-source-audit/1"})
    with urlopen(request, timeout=60) as response:
        payload = response.read()
    obj = json.loads(payload.decode("utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("Figshare article API did not return a JSON object")
    return obj


def normalise_file(row: object) -> dict[str, object]:
    if not isinstance(row, dict):
        raise ValueError("Figshare file entry is not an object")
    name = str(row.get("name", ""))
    lower = name.lower()
    return {
        "id": int(row["id"]),
        "name": name,
        "size_bytes": int(row.get("size", 0)),
        "download_url": str(row.get("download_url", "")),
        "computed_md5": str(row.get("computed_md5", "")),
        "supplied_md5": str(row.get("supplied_md5", "")),
        "is_video": lower.endswith(VIDEO_SUFFIXES),
        "is_archive": lower.endswith(ARCHIVE_SUFFIXES),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--article-id", type=int, default=DEFAULT_ARTICLE_ID)
    parser.add_argument("--output", type=Path, default=Path(".v10/source-resolution.json"))
    args = parser.parse_args()

    api_url = API_TEMPLATE.format(article_id=args.article_id)
    article = fetch_json(api_url)
    files_raw = article.get("files")
    if not isinstance(files_raw, list) or not files_raw:
        raise RuntimeError("Figshare article API returned no file list")
    files = sorted(
        (normalise_file(row) for row in files_raw),
        key=lambda row: (str(row["name"]).lower(), int(row["id"])),
    )
    videos = [row for row in files if bool(row["is_video"])]
    archives = [row for row in files if bool(row["is_archive"])]
    expected = [row for row in videos if str(row["name"]).lower().startswith("bee_test_")]

    resolution = {
        "schema": "interaction-sensing-v10-source-resolution-v1",
        "source": {
            "article_id": args.article_id,
            "doi": DEFAULT_DOI,
            "api_url": api_url,
            "title": str(article.get("title", "")),
            "url_public_api": str(article.get("url_public_api", "")),
            "url_private_api": str(article.get("url_private_api", "")),
            "license": article.get("license"),
            "version": article.get("version"),
        },
        "file_count": len(files),
        "video_count": len(videos),
        "archive_count": len(archives),
        "expected_bee_test_count": len(expected),
        "files": files,
        "videos": videos,
        "archives": archives,
        "expected_bee_test_videos": expected,
        "resolution_state": (
            "direct-video-files" if videos else "container-files-require-member-resolution"
        ),
    }
    encoded = (
        json.dumps(resolution, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    resolution["resolution_sha256_without_self_field"] = hashlib.sha256(encoded).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(resolution, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print("V10_SOURCE_TITLE", resolution["source"]["title"])
    print("V10_SOURCE_FILES", len(files))
    print("V10_SOURCE_VIDEOS", len(videos))
    print("V10_SOURCE_ARCHIVES", len(archives))
    print("V10_EXPECTED_BEE_TEST_VIDEOS", len(expected))
    print("V10_RESOLUTION_STATE", resolution["resolution_state"])
    for row in files:
        print(
            "V10_FILE",
            row["id"],
            row["size_bytes"],
            row["name"],
            row["computed_md5"],
            "archive=" + str(row["is_archive"]).lower(),
            "video=" + str(row["is_video"]).lower(),
        )


if __name__ == "__main__":
    main()
