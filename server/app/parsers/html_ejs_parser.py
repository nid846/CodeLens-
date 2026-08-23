import re
from app.parsers.base_parser import BaseParser, ParseResult
from app.models.analysis import ClassInfo, FunctionInfo


class HtmlEjsParser(BaseParser):
    def parse_file(self, content: str, file_path: str) -> ParseResult:
        if not content.strip():
            return ParseResult()

        functions = []
        imports = []

        # 1. Extract EJS includes e.g. <%- include('partials/header') %> or include("header.ejs")
        ejs_include_matches = re.findall(
            r"include\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", content, re.IGNORECASE
        )
        for inc in ejs_include_matches:
            imports.append(f"include({inc})")

        # 2. Extract script src and link href dependencies
        src_matches = re.findall(
            r"<(?:script|link)[^>]+(?:src|href)\s*=\s*['\"]([^'\"]+)['\"]", content, re.IGNORECASE
        )
        for src in src_matches:
            imports.append(f"asset({src})")

        # 3. Extract client-side inline functions in <script> blocks
        lines = content.splitlines()
        script_fn_matches = re.finditer(
            r"function\s+([A-Za-z0-9_$]+)\s*\(([^)]*)\)", content
        )
        for m in script_fn_matches:
            fn_name = m.group(1)
            params = [p.strip() for p in m.group(2).split(",") if p.strip()]
            start_pos = m.start()
            line_no = content[:start_pos].count("\n") + 1

            functions.append(
                FunctionInfo(
                    name=fn_name,
                    file_path=file_path,
                    containing_class=None,
                    start_line=line_no,
                    end_line=line_no + 5,
                    parameters=params,
                )
            )

        return ParseResult(classes=[], functions=functions, imports=imports)
