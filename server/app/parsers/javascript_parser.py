import re
import tree_sitter
import tree_sitter_javascript
import tree_sitter_typescript
from app.parsers.base_parser import BaseParser, ParseResult
from app.models.analysis import ClassInfo, FunctionInfo


class JavaScriptParser(BaseParser):
    def __init__(self, is_typescript: bool = False):
        self.is_typescript = is_typescript
        if is_typescript:
            self.language = tree_sitter.Language(tree_sitter_typescript.language_typescript())
        else:
            self.language = tree_sitter.Language(tree_sitter_javascript.language())
        self.parser = tree_sitter.Parser(self.language)

    def parse_file(self, content: str, file_path: str) -> ParseResult:
        if not content.strip():
            return ParseResult()

        content_bytes = content.encode("utf-8")
        try:
            tree = self.parser.parse(content_bytes)
        except Exception:
            return ParseResult()

        classes = []
        functions = []
        imports = []
        visited_functions = set()

        def get_node_text(node) -> str:
            return content_bytes[node.start_byte : node.end_byte].decode(
                "utf-8", errors="ignore"
            )

        def extract_params(parameters_node) -> list[str]:
            params = []
            if not parameters_node:
                return params
            for child in parameters_node.children:
                if child.type in ("identifier", "formal_parameter", "required_parameter", "optional_parameter"):
                    name_node = child.child_by_field_name("pattern") or child
                    param_name = get_node_text(name_node).split(":")[0].strip()
                    if param_name and param_name not in ("(", ")", ",", "{", "}"):
                        params.append(param_name)
            return params

        def get_route_or_call_context(node):
            """Identify parent call context like app.get('/login') or passport.use('local')"""
            curr = node.parent
            while curr:
                if curr.type == "call_expression":
                    fn_child = curr.child_by_field_name("function")
                    if fn_child:
                        fn_text = get_node_text(fn_child)
                        args_child = curr.child_by_field_name("arguments")
                        arg_text = ""
                        if args_child and len(args_child.children) > 1:
                            first_arg = args_child.children[1]
                            if first_arg.type in ("string", "template_string"):
                                arg_text = get_node_text(first_arg).strip("'\"`")
                        if arg_text:
                            return f"{fn_text}('{arg_text}') handler"
                        return f"{fn_text} callback"
                curr = curr.parent
            return None

        # Regex fallback for res.render(...) imports e.g. res.render("home.ejs")
        render_matches = re.findall(
            r"res\.render\s*\(\s*['\"]([^'\"]+)['\"]", content
        )
        for view_name in render_matches:
            imports.append(f"render({view_name})")

        def traverse(node, current_class=None):
            node_key = (node.start_byte, node.end_byte, node.type)

            if node.type == "class_declaration":
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

            elif node.type in ("function_declaration", "generator_function_declaration"):
                if node_key not in visited_functions:
                    visited_functions.add(node_key)
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

            elif node.type == "method_definition":
                if node_key not in visited_functions:
                    visited_functions.add(node_key)
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

            elif node.type in ("arrow_function", "function_expression"):
                if node_key not in visited_functions:
                    visited_functions.add(node_key)
                    fn_name = None
                    
                    # 1. Check if assigned to variable e.g. const foo = () => {}
                    if node.parent and node.parent.type == "variable_declarator":
                        name_node = node.parent.child_by_field_name("name")
                        if name_node:
                            fn_name = get_node_text(name_node)
                    
                    # 2. Check if function_expression has explicit name
                    if not fn_name:
                        name_node = node.child_by_field_name("name")
                        if name_node:
                            fn_name = get_node_text(name_node)

                    # 3. Check if passed as route or callback argument e.g. app.get('/login', ...)
                    if not fn_name:
                        call_ctx = get_route_or_call_context(node)
                        if call_ctx:
                            fn_name = call_ctx

                    if not fn_name:
                        fn_name = f"fn_L{node.start_point[0] + 1}"

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

            elif node.type == "import_statement":
                import_text = get_node_text(node).strip()
                imports.append(import_text)

            elif node.type == "call_expression":
                fn_node = node.child_by_field_name("function")
                if fn_node and get_node_text(fn_node) == "require":
                    imports.append(get_node_text(node).strip())

            for child in node.children:
                traverse(child, current_class)

        traverse(tree.root_node)
        return ParseResult(classes=classes, functions=functions, imports=imports)
