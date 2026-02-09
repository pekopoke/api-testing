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
    """从磁盘加载 OpenAPI/Swagger 文档：支持 .json 与 .yaml/.yml，按扩展名解析。"""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    text = path.read_text(encoding="utf-8")
    # YAML 需安装 pyyaml
    if path.suffix.lower() in (".yaml", ".yml"):
        try:
            import yaml
            return yaml.safe_load(text)
        except ImportError:
            raise RuntimeError("YAML 需安装 PyYAML: pip install pyyaml")
    return json.loads(text)


def is_openapi3(spec):
    """判断是否为 OpenAPI 3.x 文档（通过 openapi 字段且以 3 开头）。"""
    return "openapi" in spec and str(spec.get("openapi", "")).startswith("3")


def is_swagger2(spec):
    """判断是否为 Swagger 2.0 文档。"""
    return "swagger" in spec and spec.get("swagger") == "2.0"


def get_paths(spec):
    """从文档中取出 paths 对象（兼容不同字段名）。"""
    return spec.get("paths") or spec.get("path") or {}


def get_servers(spec):
    """仅 OpenAPI 3.x 有 servers；返回首个 server 的 url 列表。"""
    if is_openapi3(spec):
        servers = spec.get("servers") or []
        return [s.get("url", "") for s in servers if isinstance(s, dict)]
    return []


def collect_endpoints(spec):
    """
    遍历 paths，收集每个 path 下各 HTTP 方法对应的操作信息。
    返回列表，每项包含 path、method、summary、parameters、requestBody、security 等。
    """
    paths = get_paths(spec)
    endpoints = []
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        # 标准 HTTP 方法
        for method in ("get", "post", "put", "patch", "delete", "head", "options"):
            op = path_item.get(method)
            if not isinstance(op, dict):
                continue
            operation_id = op.get("operationId") or op.get("operation_id") or ""
            summary = op.get("summary") or op.get("description") or ""
            tags = op.get("tags") or []
            security = op.get("security") or path_item.get("security") or []
            # 收集参数（query/path/header 等）
            params = []
            for p in op.get("parameters") or path_item.get("parameters") or []:
                if isinstance(p, dict):
                    params.append({
                        "in": p.get("in"),
                        "name": p.get("name"),
                        "required": p.get("required", False),
                    })
            # OpenAPI 3 用 requestBody，Swagger 2 用 parameters.in=body
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
    """将端点列表格式化为「方法 路径 - 摘要」的文本清单，带 API 标题、版本和 Base URL。"""
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
    """命令行入口：解析参数，加载文档，提取端点并输出到 stdout 或文件。"""
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

    # 优先使用命令行 --base-url，否则取 OpenAPI 3 的 servers 首个 URL
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
