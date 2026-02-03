# 示例说明

本目录为 **api-test-generator** skill 的测试代码示例，供生成用例时参考。

| 文件 | 说明 |
|------|------|
| `rest_api_test_example.py` | REST 接口测试结构：按端点分 class，正向/反向用例，Arrange-Act-Assert |
| `graphql_test_example.py` | GraphQL query/mutation 测试示例 |
| `http_status_codes_example.py` | 各 HTTP 状态码（200/201/204/400/401/403/404/409/422/500）的断言示例 |

使用方式：根据端点清单与业务，参考上述结构编写或生成 `tests/test_xxx_api.py`，并结合项目 `conftest.py` 提供 `client`、`db`、`admin_headers` 等 fixture。
