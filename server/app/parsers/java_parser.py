import tree_sitter
import tree_sitter_java
from app.parsers.base_parser import BaseParser, ParseResult
from app.models.analysis import ClassInfo, FunctionInfo


class JavaParser(BaseParser):
    def __init__(self):
        self.language = tree_sitter.Language(tree_sitter_java.language())
        self.parser = tree_sitter.Parser(self.language)

    def parse_file(self, content: str, file_path: str) -> ParseResult:
        if not content.strip():
            return ParseResult()

        content_bytes = content.encode("utf-8")
        tree = self.parser.parse(content_bytes)

        classes = []
        functions = []
        imports = []
        package_name = ""

        def get_node_text(node) -> str:
            return content_bytes[node.start_byte : node.end_byte].decode(
                "utf-8", errors="ignore"
            )

        def extract_params(parameters_node) -> list[str]:
            params = []
            if not parameters_node:
                return params
            for child in parameters_node.children:
                if child.type == "formal_parameter":
                    name_node = child.child_by_field_name("name")
                    if name_node:
                        params.append(get_node_text(name_node))
            return params

        def traverse(node, current_class=None):
            nonlocal package_name
            if node.type == "package_declaration":
                for child in node.children:
                    if child.type in ("scoped_identifier", "identifier"):
                        package_name = get_node_text(child)

            elif node.type in ("class_declaration", "interface_declaration", "enum_declaration", "record_declaration"):
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

            elif node.type in ("method_declaration", "constructor_declaration"):
                name_node = node.child_by_field_name("name")
                method_name = get_node_text(name_node) if name_node else "method"
                params_node = node.child_by_field_name("parameters")
                params = extract_params(params_node)

                functions.append(
                    FunctionInfo(
                        name=method_name,
                        file_path=file_path,
                        containing_class=current_class,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        parameters=params,
                    )
                )

            elif node.type == "import_declaration":
                import_text = get_node_text(node).strip()
                imports.append(import_text)

            for child in node.children:
                traverse(child, current_class)

        traverse(tree.root_node)
        return ParseResult(
            classes=classes,
            functions=functions,
            imports=imports,
            package_name=package_name,
        )
