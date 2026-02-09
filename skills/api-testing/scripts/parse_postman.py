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
    """从磁盘加载 Postman Collection JSON 文件。"""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def is_v2(collection):
    """根据 info.schema 等判断是否为 Postman Collection 2.x 格式。"""
    info = collection.get("info") or {}
    schema = (info.get("schema") or "").lower()
    return "2." in schema or "v2" in schema or "postman" in str(collection.get("info", {}))


def walk_requests(item, base_path="", results=None):
    """
    递归遍历 Collection 的 item 树：若当前节点带 request 则视为一个请求并加入 results，
    再对子 item 递归，子节点会带上当前文件夹路径。
    """
    if results is None:
        results = []
    name = item.get("name", "")
    # 叶子节点：包含 request 的为实际请求
    if "request" in item:
        req = item["request"]
        if isinstance(req, dict):
            method = (req.get("method") or "GET").upper()
            url = req.get("url")
            # url 可能是字符串或对象（含 path/raw 等）
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
    # 递归子项（文件夹或嵌套请求）
    for child in item.get("item") or []:
        if isinstance(child, dict):
            folder = "{}/{}".format(base_path, name).strip("/") if name else base_path
            walk_requests(child, folder, results)
    return results


def collect_endpoints(collection):
    """从 Collection 根级的 item 开始递归，收集所有请求为端点列表。"""
    results = []
    for item in collection.get("item") or []:
        if isinstance(item, dict):
            walk_requests(item, "", results)
    return results


def format_inventory(collection, endpoints, base_url=""):
    """将端点列表格式化为「方法 路径 - 名称」的文本清单，带 Collection 名称和 Base URL。"""
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
    """命令行入口：解析参数，加载 Collection，提取端点并输出到 stdout 或文件。"""
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
