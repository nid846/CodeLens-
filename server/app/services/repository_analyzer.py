import os
import shutil
import tempfile
from typing import List, Dict
from app.models.analysis import (
    AnalysisResult,
    AnalysisSummary,
    FileInfo,
    ClassInfo,
    FunctionInfo,
    RepositoryInfo,
)
from app.services.github_service import GitHubService, GitHubServiceError
from app.services.dependency_analyzer import DependencyAnalyzer
from app.parsers.parser_factory import ParserFactory


IGNORED_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    "target",
    "coverage",
    ".idea",
    ".vscode",
    ".next",
    ".pytest_cache",
}

LANGUAGE_MAP = {
    ".py": "Python",
    ".java": "Java",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".ejs": "EJS",
    ".html": "HTML",
    ".htm": "HTML",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".css": "CSS",
    ".scss": "CSS",
    ".json": "JSON",
    ".sql": "SQL",
    ".go": "Go",
    ".rs": "Rust",
    ".php": "PHP",
    ".rb": "Ruby",
    ".c": "C",
    ".cpp": "C++",
    ".h": "C/C++ Header",
}


class RepositoryAnalyzer:
    @staticmethod
    def analyze_repository(github_url: str) -> AnalysisResult:
        if not GitHubService.validate_url(github_url):
            raise GitHubServiceError(f"Invalid GitHub repository URL: '{github_url}'")

        repo_info = GitHubService.parse_repo_info(github_url)

        temp_dir = tempfile.mkdtemp(prefix="codelens_repo_")
        try:
            GitHubService.clone_repository(github_url, temp_dir)

            all_files: List[FileInfo] = []
            all_classes: List[ClassInfo] = []
            all_functions: List[FunctionInfo] = []
            failed_files: List[str] = []
            
            imports_by_file: Dict[str, List[str]] = {}
            java_packages: Dict[str, str] = {}
            class_to_file: Dict[str, str] = {}

            for root, dirs, filenames in os.walk(temp_dir):
                dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]

                for fname in filenames:
                    ext = os.path.splitext(fname)[1].lower()
                    if not ParserFactory.is_supported(fname):
                        continue

                    abs_path = os.path.join(root, fname)
                    rel_path = os.path.relpath(abs_path, temp_dir)
                    rel_path_normalized = rel_path.replace("\\", "/")

                    try:
                        file_size = os.path.getsize(abs_path)
                        with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()

                        parser = ParserFactory.get_parser(ext)
                        if not parser:
                            continue

                        parse_res = parser.parse_file(content, rel_path_normalized)

                        language = LANGUAGE_MAP.get(ext, "Web")
                        file_info = FileInfo(
                            path=rel_path_normalized,
                            name=fname,
                            language=language,
                            size=file_size,
                            class_count=len(parse_res.classes),
                            function_count=len(parse_res.functions),
                        )
                        all_files.append(file_info)

                        all_classes.extend(parse_res.classes)
                        all_functions.extend(parse_res.functions)
                        imports_by_file[rel_path_normalized] = parse_res.imports

                        if parse_res.package_name:
                            java_packages[rel_path_normalized] = parse_res.package_name

                        for cls in parse_res.classes:
                            class_to_file[cls.name] = rel_path_normalized

                    except Exception as e:
                        failed_files.append(rel_path_normalized)

            dependencies, graph_data = DependencyAnalyzer.resolve_dependencies(
                all_files, imports_by_file, java_packages, class_to_file
            )

            summary = AnalysisSummary(
                total_files=len(all_files),
                total_classes=len(all_classes),
                total_functions=len(all_functions),
                total_dependencies=len(dependencies),
            )

            return AnalysisResult(
                repository=repo_info,
                summary=summary,
                files=all_files,
                classes=all_classes,
                functions=all_functions,
                dependencies=dependencies,
                graph=graph_data,
                failed_files=failed_files,
            )

        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
