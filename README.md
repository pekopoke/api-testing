# api-testing

基于 API 文档（OpenAPI/Swagger/Postman）生成 REST / GraphQL 接口集成测试的示例与 Skill。

## 如何使用 Skill（Cursor / Claude）

**在 Cursor 或 Claude 中如何调用本项目的 API 测试 Skill**，请直接查看：

# 如何使用 API Testing Skill

本目录包含 **API 测试生成 Skill**，用于根据 API 文档（OpenAPI/Swagger/Postman）生成 REST 与 GraphQL 的集成测试。本文说明如何在 **Cursor** 和 **Claude** 中调用该 skill。

---

## 在 Cursor 中调用 Skill

### 1. 让 Cursor 识别本 Skill（项目级）

Cursor 会从以下位置加载 **项目级** skill：

- 项目根目录下的 **`.cursor/skills/<skill-name>/`**

若你希望 Cursor Agent 自动在对话中应用本 skill，请将本 skill 放到 Cursor 的约定目录：

```text
你的项目根/
├── .cursor/
│   └── skills/
│       └── api-testing/        # 把 skills/api-testing 整份拷到这里
│           ├── SKILL.md
│           ├── examples/
│           └── scripts/
```

**操作示例：**

```powershell
# 在项目根目录执行
mkdir -p .cursor/skills
cp -r skills/api-testing .cursor/skills/
```

或手动复制 `skills/api-testing` 整个文件夹到 `.cursor/skills/api-testing`。

### 2. 如何“调用”Skill

在 Cursor 里 **不需要点选菜单**，用自然语言描述你的需求即可，Agent 会根据 skill 的 `description` 自动判断是否使用本 skill。

**推荐说法示例：**

- 「根据 OpenAPI 文档生成接口测试」
- 「用 Postman Collection 生成 REST API 测试」
- 「为 GraphQL 的 query 和 mutation 生成测试」
- 「按 API 文档生成测试，要覆盖鉴权、状态码和请求响应校验」

只要你的请求和「根据 API 文档生成集成测试」相关，Cursor 会优先应用 **api-testing** skill 并按其中的工作流（解析文档 → 端点清单 → 生成测试）执行。

### 3. 配合脚本使用（可选）

若从 OpenAPI/Postman 生成端点清单，可在对话中让 Agent 执行本 skill 自带的脚本，例如：

- 「用项目里的 parse_openapi 脚本解析 openapi.json，生成端点清单」
- 「用 parse_postman 解析 Postman 导出文件，输出到 inventory.txt」

脚本路径需与你在项目中的实际路径一致（例如 `.cursor/skills/api-testing/scripts/` 或 `skills/api-testing/scripts/`）。

---

## 在 Claude 中调用 Skill

Claude 没有像 Cursor 那样的「.cursor/skills 目录」自动发现机制，需要你**主动把 skill 内容交给 Claude**。

### 方式一：@ 引用文件（推荐）

在 Claude 对话中：

1. 使用 **@** 引用本 skill 的 `SKILL.md`：
   - 例如：`@skills/api-testing/SKILL.md`
2. 然后说明你的需求，例如：
   - 「请按照这个 skill 的说明，根据我项目里的 OpenAPI 文档生成 REST 接口测试。」

这样 Claude 会以 `SKILL.md` 里的工作流和规范来生成测试。

### 方式二：复制 Skill 目录后 @ 引用

若 Claude 支持引用文件夹：

- 引用 `skills/api-testing` 或 `skills/api-testing/SKILL.md`，并说明「按这个 skill 的流程和示例来生成 API 测试」。

### 方式三：粘贴关键说明

若无法 @ 文件，可以：

1. 打开 `skills/api-testing/SKILL.md`
2. 复制「目的」「工作流」「测试覆盖范围」「质量检查清单」等段落
3. 粘贴到对话中，并说明：「请按下面这份 API 测试 skill 的规范，根据 [我的 OpenAPI/Postman 文档] 生成集成测试。」

---

## Skill 内容速览

| 项目     | 说明 |
|----------|------|
| **名称** | api-testing |
| **作用** | 根据 API 文档（OpenAPI/Swagger/Postman）生成 REST 与 GraphQL 集成测试，覆盖 HTTP 方法、状态码、鉴权与参数校验。 |
| **脚本** | `scripts/parse_openapi.py`、`scripts/parse_postman.py`（生成端点清单） |
| **示例** | `examples/` 下有 REST、GraphQL、状态码等示例与说明 |

详细步骤、断言规范、Mock 文件用法等见 **`api-testing/SKILL.md`**。

---

## 小结

| 环境   | 如何调用 |
|--------|----------|
| **Cursor** | 将 `skills/api-testing` 放到 `.cursor/skills/api-testing`，在对话中用自然语言说「根据 OpenAPI/Postman 文档生成接口测试」等，Agent 会自动应用本 skill。 |
| **Claude** | 用 @ 引用 `skills/api-testing/SKILL.md`（或粘贴其内容），然后说明要按该 skill 根据你的 API 文档生成测试。 |

如有脚本路径或项目结构差异，在对话中说明你的项目根目录和文档路径即可。
