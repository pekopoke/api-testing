# -*- coding: utf-8 -*-
"""
REST API 集成测试示例（完整版见 SKILL 历史或按需展开）。

适用于：FastAPI TestClient + 本地 DB；或外部 HTTP API 时用 requests + base_url，fixture 提供 api_client/base_url。
按端点分 class，按场景写 test_xxx；正向（成功码）与反向（400/401/403/404/409）均需覆盖。
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# from src.models import User


# ============================================================================
# GET /api/users - 列表
# ============================================================================

class TestGetUsers:
    """GET /api/users 示例：空列表、分页、非法参数."""

    def test_get_users_empty_returns_empty_list(self, client: TestClient):
        response = client.get("/api/users")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_users_with_pagination(self, client: TestClient, db: Session):
        # Arrange: 造数后请求
        # response = client.get("/api/users?limit=5&offset=0")
        # assert response.status_code == 200
        # assert len(response.json()) == 5
        pass

    def test_get_users_invalid_limit_returns_400(self, client: TestClient):
        response = client.get("/api/users?limit=-1")
        assert response.status_code == 400


# ============================================================================
# GET /api/users/:id - 详情
# ============================================================================

class TestGetUserById:
    """GET /api/users/:id：成功、404、非法 ID."""

    def test_get_user_nonexistent_id_returns_404(self, client: TestClient):
        response = client.get("/api/users/99999")
        assert response.status_code == 404

    def test_get_user_invalid_id_format_returns_400(self, client: TestClient):
        response = client.get("/api/users/invalid-id")
        assert response.status_code == 400


# ============================================================================
# POST /api/users - 创建
# ============================================================================

class TestCreateUser:
    """POST /api/users：201、缺必填 400、重复 409、无鉴权 401、非管理员 403."""

    def test_create_user_missing_required_field_returns_400(self, client: TestClient, admin_headers: dict):
        invalid_data = {"name": "User", "password": "password"}  # 缺 email
        response = client.post("/api/users", json=invalid_data, headers=admin_headers)
        assert response.status_code == 400

    def test_create_user_without_auth_returns_401(self, client: TestClient):
        response = client.post("/api/users", json={"name": "x", "email": "x@x.com", "password": "x"})
        assert response.status_code == 401


# ============================================================================
# PUT /api/users/:id、PATCH、DELETE 同理：成功码 + 404/403/401 等反向用例
# ============================================================================

class TestDeleteUser:
    """DELETE /api/users/:id：204、404、401、403."""

    def test_delete_user_nonexistent_returns_404(self, client: TestClient, admin_headers: dict):
        response = client.delete("/api/users/99999", headers=admin_headers)
        assert response.status_code == 404
