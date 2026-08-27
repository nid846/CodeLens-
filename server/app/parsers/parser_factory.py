from typing import Optional
from app.parsers.base_parser import BaseParser, ParseResult
from app.parsers.python_parser import PythonParser
from app.parsers.java_parser import JavaParser
from app.parsers.javascript_parser import JavaScriptParser
from app.parsers.html_ejs_parser import HtmlEjsParser


class GenericFileParser(BaseParser):
    def parse_file(self, content: str, file_path: str) -> ParseResult:
        return ParseResult()


class ParserFactory:
    _parsers = {}

    @classmethod
    def get_parser(cls, extension: str) -> Optional[BaseParser]:
        ext = extension.lower()
        if ext == ".py":
            if ".py" not in cls._parsers:
                cls._parsers[".py"] = PythonParser()
            return cls._parsers[".py"]
        elif ext == ".java":
            if ".java" not in cls._parsers:
                cls._parsers[".java"] = JavaParser()
            return cls._parsers[".java"]
        elif ext in (".js", ".jsx", ".mjs", ".cjs"):
            if ".js" not in cls._parsers:
                cls._parsers[".js"] = JavaScriptParser(is_typescript=False)
            return cls._parsers[".js"]
        elif ext in (".ts", ".tsx"):
            if ".ts" not in cls._parsers:
                cls._parsers[".ts"] = JavaScriptParser(is_typescript=True)
            return cls._parsers[".ts"]
        elif ext in (".ejs", ".html", ".htm", ".vue", ".svelte"):
            if ".ejs" not in cls._parsers:
                cls._parsers[".ejs"] = HtmlEjsParser()
            return cls._parsers[".ejs"]
        elif ext in (".css", ".scss", ".json", ".sql", ".go", ".rs", ".php", ".rb", ".c", ".cpp", ".h", ".md"):
            if "generic" not in cls._parsers:
                cls._parsers["generic"] = GenericFileParser()
            return cls._parsers["generic"]
        return None

    @classmethod
    def is_supported(cls, file_name: str) -> bool:
        lower_name = file_name.lower()
        # Security: Never process or index sensitive files or credential patterns
        if lower_name.startswith(".env") or lower_name in ("id_rsa", "id_dsa", "id_ed25519", "credentials.json", "secrets.json"):
            return False
        if any(lower_name.endswith(pat) for pat in (".pem", ".key", ".pfx", ".p12", ".cer")):
            return False

        supported_exts = {
            ".py", ".java", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
            ".ejs", ".html", ".htm", ".vue", ".svelte",
            ".css", ".scss", ".json", ".sql", ".go", ".rs", ".php", ".rb", ".c", ".cpp", ".h", ".md"
        }
        return any(lower_name.endswith(ext) for ext in supported_exts)
