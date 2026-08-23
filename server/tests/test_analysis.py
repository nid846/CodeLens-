import pytest
from app.services.github_service import GitHubService
from app.parsers.python_parser import PythonParser
from app.parsers.java_parser import JavaParser
from app.parsers.javascript_parser import JavaScriptParser
from app.services.dependency_analyzer import DependencyAnalyzer
from app.models.analysis import FileInfo, ClassInfo


def test_github_url_validation():
    assert GitHubService.validate_url("https://github.com/fastapi/fastapi") is True
    assert GitHubService.validate_url("https://github.com/user/repo.git") is True
    assert GitHubService.validate_url("https://invalid-url.com/repo") is False
    assert GitHubService.validate_url("not_a_url") is False


def test_python_parser():
    code = """
import os
from auth.service import AuthService

class UserController:
    def __init__(self, name: str):
        self.name = name

    def get_user(self, user_id):
        return AuthService.find(user_id)

def helper_fn():
    pass
"""
    parser = PythonParser()
    result = parser.parse_file(code, "controllers/user_controller.py")

    assert len(result.classes) == 1
    assert result.classes[0].name == "UserController"
    
    assert len(result.functions) == 3
    fn_names = [f.name for f in result.functions]
    assert "__init__" in fn_names
    assert "get_user" in fn_names
    assert "helper_fn" in fn_names

    assert len(result.imports) == 2


def test_java_parser():
    code = """
package com.example.controller;

import com.example.service.UserService;

public class AuthController {
    private UserService userService;

    public void login(String username, String password) {
        userService.authenticate(username, password);
    }
}
"""
    parser = JavaParser()
    result = parser.parse_file(code, "src/com/example/controller/AuthController.java")

    assert len(result.classes) == 1
    assert result.classes[0].name == "AuthController"
    assert len(result.functions) == 1
    assert result.functions[0].name == "login"
    assert len(result.imports) == 1
    assert "UserService" in result.imports[0]
    assert result.package_name == "com.example.controller"


def test_javascript_parser():
    code = """
import UserService from "./UserService";
import { formatName } from '../utils/format';

class DashboardComponent {
    render() {
        return UserService.getUser();
    }
}

const fetchData = async (url) => {
    return fetch(url);
};
"""
    parser = JavaScriptParser(is_typescript=False)
    result = parser.parse_file(code, "components/Dashboard.jsx")

    assert len(result.classes) == 1
    assert result.classes[0].name == "DashboardComponent"
    assert len(result.functions) == 2
    fn_names = [f.name for f in result.functions]
    assert "render" in fn_names
    assert "fetchData" in fn_names
    assert len(result.imports) == 2


def test_dependency_resolution():
    files = [
        FileInfo(path="auth/controller.py", name="controller.py", language="Python", size=100),
        FileInfo(path="auth/service.py", name="service.py", language="Python", size=200),
    ]
    imports_by_file = {
        "auth/controller.py": ["from auth.service import AuthService"],
        "auth/service.py": ["import os"],
    }
    class_to_file = {"AuthService": "auth/service.py"}

    deps, graph = DependencyAnalyzer.resolve_dependencies(
        files=files,
        imports_by_file=imports_by_file,
        java_packages={},
        class_to_file=class_to_file,
    )

    assert len(deps) == 1
    assert deps[0].source_file == "auth/controller.py"
    assert deps[0].target_file == "auth/service.py"
    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1
    assert graph.edges[0].source == "auth/controller.py"
    assert graph.edges[0].target == "auth/service.py"
