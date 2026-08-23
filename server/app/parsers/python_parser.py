import tree_sitter
import tree_sitter_python
from app.parsers.base_parser import BaseParser, ParseResult
from app.models.analysis import ClassInfo, FunctionInfo


class PythonParser(BaseParser):
    def __init__(self):
        self.language = tree_sitter.Language(tree_sitter_python.language())
        self.parser = tree_sitter.Parser(self.language)

    def parse_file(self, content: str, file_path: str) -> ParseResult:
        if not content.strip():
            return ParseResult()

        content_bytes = content.encode("utf-8")
        tree = self.parser.parse(content_bytes)

        classes = []
        functions = []
        imports = []

        def get_node_text(node) -> str:
            return content_bytes[node.start_byte : node.end_byte].decode(
                "utf-8", errors="ignore"
            )

        def extract_params(parameters_node) -> list[str]:
            params = []
            if not parameters_node:
                return params
            for child in parameters_node.children:
                if child.type in ("identifier", "typed_parameter", "default_parameter", "typed_default_parameter"):
                    param_name = get_node_text(child).split(":")[0].split("=")[0].strip()
                    if param_name and param_name != "self" and param_name != "cls":
                        params.append(param_name)
            return params

        def traverse(node, current_class=None):
            if node.type == "class_definition":
                name_node = node.child_by_field_name("name")
                class_name = get_node_text(name_node) if name_node else "UnknownClass"
                classes.append(
                    ClassInfo(
                        name=class_name,
                        file_path=file_path,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                    )
                )

                body_node = node.child_by_field_name("body")
                if body_node:
                    for child in body_node.children:
                        traverse(child, current_class=class_name)
                return

            elif node.type == "function_definition":
                name_node = node.child_by_field_name("name")
                fn_name = get_node_text(name_node) if name_node else "anonymous"
                params_node = node.child_by_field_name("parameters")
                params = extract_params(params_node)

                functions.append(
                    FunctionInfo(
                        name=fn_name,
                        file_path=file_path,
                        containing_class=current_class,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        parameters=params,
                    )
                )

                body_node = node.child_by_field_name("body")
                if body_node:
                    for child in body_node.children:
                        traverse(child, current_class=current_class)
                return

            elif node.type == "import_statement":
                import_text = get_node_text(node).strip()
                imports.append(import_text)

            elif node.type == "import_from_statement":
                import_text = get_node_text(node).strip()
                imports.append(import_text)

            for child in node.children:
                traverse(child, current_class)

        traverse(tree.root_node)
        return ParseResult(classes=classes, functions=functions, imports=imports)
