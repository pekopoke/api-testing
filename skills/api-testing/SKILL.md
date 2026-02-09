---
name: api-testing
description: 根据 API 文档（OpenAPI/Swagger/Postman）生成 REST 与 GraphQL 接口的集成测试，
  覆盖各 HTTP 方法、状态码、鉴权与参数校验。
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# API 测试生成 Skill

## 目的

本 skill 用于生成接口的集成测试，覆盖各 HTTP 方法、成功/错误状态码、鉴权与鉴权失败、请求/响应校验及错误处理。

## 适用场景

- **从 API 文档生成测试**：为 REST 接口生成测试，支持 OpenAPI 2.0/3.x（Swagger）、Postman Collection — 先用本目录下 `scripts/` 中的脚本得到端点清单
- 为 GraphQL 的 query/mutation 生成测试
- 校验接口的请求/响应契约
- 校验鉴权、鉴权失败及状态码

## 测试覆盖范围

每个端点需覆盖：

- ✅ **成功场景**（200、201、204）
- ✅ **参数/校验错误**（400、422）— 见下文「负向测试用例」
- ✅ **未认证**（401）
- ✅ **无权限**（403）
- ✅ **未找到**（404）
- ✅ **冲突**（409）
- ✅ **服务错误**（500）
- ✅ **请求体/查询参数校验**（覆盖各类负向情形）
- ✅ **响应结构校验**

### 负向测试用例（请求校验与错误场景）

除鉴权、权限、资源存在性外，应对**请求参数与请求体**做负向校验，确保接口在非法输入时返回预期错误（通常 400 或 422）。生成测试时需覆盖以下负向类型，**每个类型可单独一个用例，只断言一种预期状态码**：

| 类型 | 说明 | 示例 | 预期状态码 |
|------|------|------|------------|
| **无效值** | 值不符合业务或约束规则 | 枚举外取值、超出 min/max、负数（应为正数）、非法 ID 格式 | 400 / 422 |
| **缺失必要字段** | 请求体或必填参数未提供 | body 少 required 字段、query/path 缺必填参数 | 400 / 422 |
| **格式错误** | 字符串格式不符合约定 | 非法 email、错误日期/时间格式、非法 URL、错误正则 | 400 / 422 |
| **类型错误** | 类型与 schema 不一致 | 传字符串给 number、传数组给 string、传 object 给 array | 400 / 422 |
| **空值/空字符串** | 必填字段为空或不允许的空值 | 空字符串 `""`、`null`、空数组/对象（若不允许） | 400 / 422 |
| **长度/大小超限** | 违反 minLength/maxLength/minItems/maxItems 等 | 超长字符串、数组过长或过短 | 400 / 422 |
| **非法字符/注入** | 含特殊字符或潜在注入内容 | 非法 Unicode、控制字符、SQL/NoSQL 片段（视接口是否校验） | 400 / 403 |
| **重复/冲突** | 违反唯一性或有状态冲突 | 重复创建同一资源、版本冲突、条件冲突 | 409 |

- **设计原则**：每个负向用例**只改一处**（如只缺一个必填字段、只错一个类型），便于定位是哪种校验生效；预期状态码与接口文档的 `responses` 一致（常见 400 或 422）。
- **与文档对齐**：若 OpenAPI/Postman 中定义了 schema（required、enum、format、minLength 等），应优先为这些约束各写至少一个负向用例。

---

## 真实场景与测试数据

为让测试能**发现接口行为问题**（如该返回 400 却返回 200），需按真实场景设计并**严格断言**。

### 测试数据准备

- **依赖资源的接口**（如「获取/更新/删除某条 pipeline」）：在 fixture 或 class/session 级 setup 中**先调用创建接口**，拿到真实 `id`（如 `pipeline_id`、`file_id`），再用该 ID 写后续用例。
- **示例**：先 `POST /studio/pipelines` 创建 pipeline → 用返回的 `pipeline_id` 测 `GET /studio/pipelines/{pipeline_id}`、`POST .../run`、`DELETE .../files/{file_id}` 等。
- 可选：在 teardown 中删除本次创建的资源，或使用独立测试账号/项目，避免污染环境。

### 断言严格度

- **每个场景只断言一种预期状态码**（如成功 → `assert response.status_code == 200`，非法参数 → `assert response.status_code == 400`，不存在 → `assert response.status_code == 404`）。
- **不要写「接受 200 或 400」等宽松断言**：否则无法发现「该 400 却 200」等接口错误，QA 难以发现问题。
- 响应结构：成功场景除状态码外，应校验文档中约定的字段（如 `code`、`data`、`meta`、`pipeline_id`）。

### 两种测试模式

| 模式 | 适用 | 断言方式 | 用途 |
|------|------|----------|------|
| **契约/真实场景** | 有可控数据或 Mock | 每场景一种预期状态码 + 响应结构 | 发现接口行为错误，适合 QA |
| **冒烟/连通性** | 无数据、直连外部 API | 可接受多种状态码（如 200/404/401） | 快速验证可达性，不做严格校验 |

优先生成**契约/真实场景**用例；若暂时无法造数据，可单独标注为冒烟用例（如 `@pytest.mark.smoke`），并在文档中说明。

### Mock 文件（多种格式）

对**上传、文件相关接口**等需要文件体的场景，可使用 **Mock 文件** 提供内存中的多格式文件内容，**不启动 mock 服务**、不依赖真实磁盘文件，便于 CI 与无环境依赖下跑用例。

- **用途**：上传接口（如 `POST .../upload`）、依赖 `file_id` 的接口（先上传 mock 文件拿到 `file_id` 再测）等。
- **设计要点**：
  - 在测试项目中提供统一模块（如 `tests/mock_files.py`），按格式维护最小合法或占位字节（如 PDF 最小结构、1×1 PNG、JPEG 头、txt/csv/json 等）。
  - 提供 `get_mock_file_bytes(format)` 返回 `bytes`，以及 `get_mock_upload_tuple(format [, filename])` 返回 `(filename, BytesIO(bytes), content_type)`，供 `requests` 的 `files=` 直接使用。
  - 支持格式示例：`pdf`、`png`、`jpg`/`jpeg`、`gif`、`txt`、`csv`、`json`、`xml`；可按接口文档扩展。
- **在 conftest 中**：可提供 `mock_upload_file(format)` 工厂或 `mock_pdf_file`、`mock_png_file` 等 fixture，便于用例注入。
- **用例策略**：上传成功、删除成功等用例**优先使用 mock 文件**；若服务端仅接受真实文件（如校验 magic bytes），再回退到项目内真实文件（若存在）或 skip 并说明。

示例（上传 mock PNG）：

```python
from tests.mock_files import get_mock_upload_tuple

file_tuple = get_mock_upload_tuple("png")  # ("mock.png", BytesIO(...), "image/png")
payload = {"files": file_tuple, "pipeline_id": (None, pipeline_id)}
resp = api_client("POST", f"/studio/pipelines/{pipeline_id}/upload", files=payload)
```

---

## 支持的 API 文档格式

当接口由 **API 文档** 定义时，可使用以下格式，并用本 skill 目录下 `scripts/` 中的脚本得到端点清单：

| 格式 | 说明 | 脚本 |
|------|------|------|
| **OpenAPI 3.x** | OpenAPI 3.0/3.1 JSON 或 YAML | `scripts/parse_openapi.py <文档路径>` |
| **OpenAPI 2.0 (Swagger)** | Swagger 2.0 JSON 或 YAML | `scripts/parse_openapi.py <文档路径>` |
| **Postman Collection 2.x** | Postman 导出的 JSON | `scripts/parse_postman.py <文档路径>` |

- **OpenAPI/Swagger**：在项目根执行 `python .cursor/skills/api-testing/scripts/parse_openapi.py path/to/openapi.json`（或 `.yaml`）。可选：`--output inventory.txt`、`--base-url https://api.example.com`。YAML 需安装 `pyyaml`。
- **Postman**：执行 `python .cursor/skills/api-testing/scripts/parse_postman.py path/to/collection.json`。可选：`--output inventory.txt`、`--base-url https://api.example.com`。

输出为「方法 路径 - 摘要」的文本清单，即工作流第 1 步的**交付物**。脚本用法详见本目录下 `scripts/README.md`。

---

## 工作流

### 1. 从 API 文档得到端点清单

使用本目录 `scripts/` 中的脚本从 OpenAPI / Swagger / Postman 文档提取端点：

```bash
# OpenAPI 3.x 或 Swagger 2.0（JSON/YAML）
python .cursor/skills/api-testing/scripts/parse_openapi.py path/to/openapi.json --output inventory.txt

# Postman Collection 2.x
python .cursor/skills/api-testing/scripts/parse_postman.py path/to/collection.json --output inventory.txt
```

根据生成的清单和文档内容，整理每个端点的：路径、方法、参数、请求体、响应、鉴权要求。Base URL 来自 `--base-url` 或 OpenAPI 的 `servers` / Postman 变量。

**端点清单示例：**

```
GET    /api/users              - 用户列表（公开）
GET    /api/users/:id          - 用户详情（公开）
POST   /api/users              - 创建用户（仅管理员）
PUT    /api/users/:id          - 更新用户（需登录，本人或管理员）
DELETE /api/users/:id          - 删除用户（需登录，本人或管理员）
```

**交付物：** API 端点清单（脚本输出）。

**测试环境说明：** 若被测对象是**外部 HTTP 服务**（通过 OpenAPI/Postman 描述、用 HTTP 调用），测试通常使用 `requests` + 可配置的 base_url（及可选鉴权头），而不是进程内 TestClient 和数据库。在 `conftest.py` 中提供 `api_client`、`base_url` 等 fixture；无本地应用/DB 时不提供 DB 相关 fixture。为做**真实场景**测试，应在 fixture 中通过创建接口造数据（如创建 pipeline），再用真实 ID 写用例并严格断言状态码（见上文「真实场景与测试数据」）。

---

### 2. 生成 REST API 测试

- **结构**：按端点分 class（如 `TestGetUsers`、`TestCreateUser`），每个 class 内按场景写 `test_xxx`；使用 Arrange-Act-Assert；正向（成功码）与负向（400/401/403/404/409 等）都要写。
- **负向用例**：除鉴权/权限/404 外，需覆盖**负向测试用例**中的类型：无效值、缺失必要字段、格式错误、类型错误、空值/空字符串、长度/大小超限、非法字符/注入、重复/冲突（见上文「负向测试用例」表格）；每个负向用例只改一处、只断言一种预期状态码。
- **断言**：每个场景**只断言一种预期状态码**（如成功 200、非法参数 400、不存在 404），并与接口文档中的 responses 一致；不写「接受 200 或 400」等宽松断言，否则无法作为 QA 发现接口错误。
- **数据**：对依赖资源的接口，在 fixture/setup 中先创建资源（见上文「真实场景与测试数据」），再用真实 ID 写用例。
- **示例代码**：见本目录下 `examples/rest_api_test_example.py`。
- **状态码示例**：见 `examples/http_status_codes_example.py`。

**交付物：** 完整的 REST 接口测试文件（如 `tests/test_xxx_api.py`）。

---

### 3. 生成 GraphQL API 测试

- **结构**：对 query 与 mutation 分别写测试，断言 `response.status_code == 200` 及 `response.json()["data"]` 结构。
- **示例代码**：见本目录下 `examples/graphql_test_example.py`。

**交付物：** GraphQL 接口测试文件。

---

## HTTP 状态码

需覆盖的状态码示例见 `examples/http_status_codes_example.py`，包括：

- 200（GET/PUT/PATCH 成功）、201（POST 创建）、204（DELETE 成功）
- 400 / 422（参数/校验错误：无效值、缺失必要字段、格式错误、类型错误、空值、长度超限等，见「负向测试用例」）、401（未认证）、403（无权限）、404（未找到）、409（冲突）、500（服务错误）

---

## 最佳实践

1. 覆盖所有端点与 HTTP 方法
2. 成功与错误状态码都要测，**每个场景只断言一种预期状态码**（不写多状态码「或」断言）
3. 对依赖资源的接口：**先造数据再测**（fixture/setup 中创建资源，再用真实 ID）
4. 对上传/文件接口：**优先使用 Mock 文件**（多格式内存内容，不依赖真实文件、不启动 mock 服务）；若服务端仅接受真实文件再回退或 skip
5. 校验请求体：必填、格式、约束；负向用例覆盖**无效值、缺失必要字段、格式错误、类型错误、空值/空字符串、长度超限、非法字符/注入、重复/冲突**等类型
6. 校验响应体：结构、字段、类型（与 API 文档 schemas/examples 一致）
7. 测鉴权：有/无 token、过期 token
8. 测权限：不同角色与权限
9. 测边界：空列表、null、最大限制
10. 有 DB 时校验持久化结果；测外部 API 时若有造数据则同样可校验行为
11. 用例命名清晰，一个用例只测一个场景
12. 按端点组织，用例之间相互独立

---

## 质量检查清单

完成测试前确认：

- [ ] 所有端点已覆盖（清单来自 API 文档）
- [ ] 所有 HTTP 方法已覆盖
- [ ] 成功场景（200、201、204）已覆盖，**且每场景只断言预期状态码**（不写 200 或 400 等宽松断言）
- [ ] 错误场景（400、401、403、404、409）已覆盖，**且每场景只断言预期状态码**
- [ ] 负向校验已覆盖：无效值、缺失必要字段、格式错误、类型错误、空值/空字符串、长度超限、非法字符/注入、重复/冲突（按接口文档 schema 酌情覆盖）
- [ ] 依赖资源的接口已通过 fixture/setup **先造数据**，再用真实 ID 测（真实场景）
- [ ] 请求校验已测
- [ ] 响应结构已校验（与文档一致）
- [ ] 鉴权已测（若接口需要）
- [ ] 权限已测（若接口需要）
- [ ] 边界情况已覆盖
- [ ] 有 DB 时已校验持久化；测外部 API 时若有造数据则按真实场景断言
- [ ] 用例可独立运行且全部通过

---

## 与测试流程的衔接

**输入：** API 文档文件（OpenAPI/Swagger/Postman）。  
**过程：** 分析（可选使用本目录 `scripts/`）→ 生成测试 → 运行并修正。  
**输出：** 完整的接口测试套件。  
**后续：** 接入 CI、文档或部署。

---

## 记住

- 覆盖所有端点与 HTTP 方法
- 成功与错误场景都要测，**每个场景只断言一种预期状态码**（便于 QA 发现接口错误）
- 负向用例覆盖：**无效值、缺失必要字段、格式错误、类型错误、空值/空字符串、长度超限、非法字符/注入、重复/冲突**等，每个负向用例只改一处
- 依赖资源的接口：**先造数据再测**，用真实 ID，不写「接受多种状态码」的宽松断言
- 上传/文件接口：**优先 Mock 文件**（多格式内存内容），不依赖真实文件、不启动 mock 服务
- 校验请求与响应结构（与 API 文档一致）
- 测鉴权与权限
- 有 DB 时校验持久化
- 每个用例聚焦一个场景
- 测试即文档，保持可读性
