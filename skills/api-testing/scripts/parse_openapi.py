#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 OpenAPI 2.0 (Swagger) 或 OpenAPI 3.x 文档提取端点清单，供 API 测试用例设计使用。

用法（在本 skill 所在项目根目录执行时，路径指向文档文件）:
  python .cursor/skills/api-test-generator/scripts/parse_openapi.py path/to/openapi.json
  python .cursor/skills/api-test-generator/scripts/parse_openapi.py path/to/openapi.yaml --output inventory.txt
"""

import argparse
import json
import sys
from pathlib import Path


def load_spec(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".yaml", ".yml"):
        try:
            import yaml
            return yaml.safe_load(text)
        except ImportError:
            raise RuntimeError("YAML 需安装 PyYAML: pip install pyyaml")
    return json.loads(text)


def is_openapi3(spec):
    return "openapi" in spec and str(spec.get("openapi", "")).startswith("3")


def is_swagger2(spec):
    return "swagger" in spec and spec.get("swagger") == "2.0"


def get_paths(spec):
    return spec.get("paths") or spec.get("path") or {}


def get_servers(spec):
    if is_openapi3(spec):
        servers = spec.get("servers") or []
        return [s.get("url", "") for s in servers if isinstance(s, dict)]
    return []


def collect_endpoints(spec):
    paths = get_paths(spec)
    endpoints = []
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method in ("get", "post", "put", "patch", "delete", "head", "options"):
            op = path_item.get(method)
            if not isinstance(op, dict):
                continue
            operation_id = op.get("operationId") or op.get("operation_id") or ""
            summary = op.get("summary") or op.get("description") or ""
            tags = op.get("tags") or []
            security = op.get("security") or path_item.get("security") or []
            params = []
            for p in op.get("parameters") or path_item.get("parameters") or []:
                if isinstance(p, dict):
                    params.append({
                        "in": p.get("in"),
                        "name": p.get("name"),
                        "required": p.get("required", False),
                    })
            body = None
            if "requestBody" in op:
                body = "requestBody"
            elif any(p.get("in") == "body" for p in (op.get("parameters") or [])):
                body = "body"
            endpoints.append({
                "path": path,
                "method": method.upper(),
                "operationId": operation_id,
                "summary": summary,
                "tags": tags,
                "parameters": params,
                "requestBody": body,
                "security": security,
            })
    return endpoints


def format_inventory(spec, endpoints, base_url=""):
    lines = []
    title = spec.get("info", {}).get("title") or "API"
    version = spec.get("info", {}).get("version") or ""
    lines.append("# {} (version {})".format(title, version))
    if base_url:
        lines.append("# Base URL: {}".format(base_url))
    lines.append("")
    for e in endpoints:
        line = "{:6} {}".format(e["method"], e["path"])
        if e["summary"]:
            line += "  - {}".format(e["summary"])
        lines.append(line)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="从 OpenAPI/Swagger 文档提取端点清单")
    parser.add_argument("spec_path", help="openapi.json 或 openapi.yaml 路径")
    parser.add_argument("--output", "-o", help="写入文件（默认 stdout）")
    parser.add_argument("--base-url", help="Base URL，写入清单头部")
    args = parser.parse_args()

    try:
        spec = load_spec(args.spec_path)
    except Exception as e:
        print("加载文档失败: {}".format(e), file=sys.stderr)
        sys.exit(1)

    if not is_openapi3(spec) and not is_swagger2(spec):
        print("不支持的文档格式，需要 openapi 3.x 或 swagger 2.0", file=sys.stderr)
        sys.exit(1)

    base_url = args.base_url or (get_servers(spec) and get_servers(spec)[0]) or ""
    endpoints = collect_endpoints(spec)
    out = format_inventory(spec, endpoints, base_url)

    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")
        print("已写入 {} 个端点到 {}".format(len(endpoints), args.output), file=sys.stderr)
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
