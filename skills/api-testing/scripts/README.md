# 脚本说明

本目录为 **api-testing** skill 的辅助脚本，用于从 API 文档中提取端点清单，供 SKILL 工作流「从 API 文档得到端点清单」步骤使用。

## 依赖

- Python 3.7+
- 解析 YAML 格式 OpenAPI 时需安装：`pip install pyyaml`

## 路径说明

脚本位于 skill 目录下：`.cursor/skills/api-test-generator/scripts/`。在**项目根目录**执行时，文档路径为相对于项目根的路径。

## 用法

### OpenAPI / Swagger

支持 **OpenAPI 2.0 (Swagger)** 与 **OpenAPI 3.x**，支持 `.json` / `.yaml` / `.yml`。

```bash
# 输出到终端
python .cursor/skills/api-test-generator/scripts/parse_openapi.py path/to/openapi.json
python .cursor/skills/api-test-generator/scripts/parse_openapi.py path/to/openapi.yaml

# 输出到文件
python .cursor/skills/api-test-generator/scripts/parse_openapi.py path/to/openapi.json --output inventory.txt
python .cursor/skills/api-test-generator/scripts/parse_openapi.py path/to/openapi.json --base-url https://api.example.com
```

### Postman Collection

支持 **Postman Collection 2.x** JSON 导出。

```bash
# 输出到终端
python .cursor/skills/api-test-generator/scripts/parse_postman.py path/to/collection.json

# 输出到文件
python .cursor/skills/api-test-generator/scripts/parse_postman.py path/to/collection.json --output inventory.txt --base-url https://api.example.com
```

## 输出示例

```
# API 名称 (version 1.0)
# Base URL: https://api.example.com

GET    /api/users              - 获取用户列表
GET    /api/users/{id}         - 获取用户详情
POST   /api/users              - 创建用户
PUT    /api/users/{id}         - 更新用户
DELETE /api/users/{id}         - 删除用户
```

将此清单作为工作流中的 **API 端点清单** 输入，再按端点生成正向/反向测试用例。
