import os
import re
import shutil
import tempfile
import subprocess
from app.models.analysis import RepositoryInfo


class GitHubServiceError(Exception):
    pass


class GitHubService:
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate if the string is a public GitHub repository URL."""
        pattern = r"^https?:\/\/(www\.)?github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+(?:\.git)?\/?$"
        return bool(re.match(pattern, url.strip()))

    @staticmethod
    def parse_repo_info(url: str) -> RepositoryInfo:
        clean_url = url.strip().rstrip("/")
        if clean_url.endswith(".git"):
            clean_url = clean_url[:-4]

        parts = clean_url.split("/")
        repo_name = parts[-1] if len(parts) >= 1 else "repository"
        return RepositoryInfo(name=repo_name, url=clean_url, branch="main")

    @staticmethod
    def clone_repository(github_url: str, dest_dir: str):
        """Clone a public GitHub repository into dest_dir using shallow clone."""
        if not GitHubService.validate_url(github_url):
            raise GitHubServiceError(f"Invalid GitHub URL: {github_url}")

        clean_url = github_url.strip()
        if not clean_url.endswith(".git"):
            clean_url += ".git"

        try:
            cmd = ["git", "clone", "--depth", "1", clean_url, dest_dir]
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                stderr_text = result.stderr.strip()
                if "Repository not found" in stderr_text or "404" in stderr_text:
                    raise GitHubServiceError("Repository not found or is private.")
                raise GitHubServiceError(f"Git clone failed: {stderr_text}")
        except subprocess.TimeoutExpired:
            raise GitHubServiceError("Git clone timed out after 60 seconds.")
        except Exception as e:
            if not isinstance(e, GitHubServiceError):
                raise GitHubServiceError(f"Cloning error: {str(e)}")
            raise e
