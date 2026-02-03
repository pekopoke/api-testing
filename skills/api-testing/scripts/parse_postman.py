#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 Postman Collection 2.x JSON 提取端点清单，供 API 测试用例设计使用。

用法（在本 skill 所在项目根目录执行时，路径指向 Postman 导出文件）:
  python .cursor/skills/api-test-generator/scripts/parse_postman.py path/to/collection.json
  python .cursor/skills/api-test-generator/scripts/parse_postman.py path/to/collection.json --output inventory.txt
"""

import argparse
import json
import sys
from pathlib import Path


def load_collection(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def is_v2(collection):
    info = collection.get("info") or {}
    schema = (info.get("schema") or "").lower()
    return "2." in schema or "v2" in schema or "postman" in str(collection.get("info", {}))


def walk_requests(item, base_path="", results=None):
    if results is None:
        results = []
    name = item.get("name", "")
    if "request" in item:
        req = item["request"]
        if isinstance(req, dict):
            method = (req.get("method") or "GET").upper()
            url = req.get("url")
            if isinstance(url, str):
                path = url
            elif isinstance(url, dict):
                path = url.get("path") or ""
                if isinstance(path, list):
                    path = "/" + "/".join(str(p) for p in path)
                raw = url.get("raw", "")
                if raw and path and not path.startswith("/"):
                    path = raw
            else:
                path = ""
            results.append({
                "method": method,
                "path": path,
                "name": name,
                "folder": base_path,
            })
    for child in item.get("item") or []:
        if isinstance(child, dict):
            folder = "{}/{}".format(base_path, name).strip("/") if name else base_path
            walk_requests(child, folder, results)
    return results


def collect_endpoints(collection):
    results = []
    for item in collection.get("item") or []:
        if isinstance(item, dict):
            walk_requests(item, "", results)
    return results


def format_inventory(collection, endpoints, base_url=""):
    info = collection.get("info") or {}
    name = info.get("name") or "Postman Collection"
    lines = ["# {}".format(name), ""]
    if base_url:
        lines.append("# Base URL: {}".format(base_url))
        lines.append("")
    for e in endpoints:
        path = e["path"]
        line = "{:6} {}".format(e["method"], path)
        if e.get("name"):
            line += "  - {}".format(e["name"])
        lines.append(line)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="从 Postman Collection 提取端点清单")
    parser.add_argument("collection_path", help="Postman 导出的 collection JSON 路径")
    parser.add_argument("--output", "-o", help="写入文件（默认 stdout）")
    parser.add_argument("--base-url", help="Base URL，写入清单头部")
    args = parser.parse_args()

    try:
        collection = load_collection(args.collection_path)
    except Exception as e:
        print("加载 Collection 失败: {}".format(e), file=sys.stderr)
        sys.exit(1)

    if not is_v2(collection):
        print("警告: 可能非 v2 格式，继续执行。", file=sys.stderr)

    base_url = args.base_url or ""
    endpoints = collect_endpoints(collection)
    out = format_inventory(collection, endpoints, base_url)

    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")
        print("已写入 {} 个端点到 {}".format(len(endpoints), args.output), file=sys.stderr)
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
