import os
import re
from typing import List, Dict, Set, Tuple
from app.models.analysis import DependencyInfo, GraphNode, GraphEdge, GraphData, FileInfo


class DependencyAnalyzer:
    @staticmethod
    def resolve_dependencies(
        files: List[FileInfo],
        imports_by_file: Dict[str, List[str]],
        java_packages: Dict[str, str],
        class_to_file: Dict[str, str],
    ) -> Tuple[List[DependencyInfo], GraphData]:
        
        file_paths_set: Set[str] = {f.path for f in files}
        file_map: Dict[str, FileInfo] = {f.path: f for f in files}
        
        dependencies: List[DependencyInfo] = []
        edges_set: Set[Tuple[str, str]] = set()

        for source_file, import_list in imports_by_file.items():
            source_dir = os.path.dirname(source_file)
            source_lang = file_map[source_file].language if source_file in file_map else ""

            for imp in import_list:
                target_file = None

                # 1. Express res.render(...) resolution e.g., render(home.ejs)
                if imp.startswith("render("):
                    view_name = imp[7:-1].strip()
                    target_file = DependencyAnalyzer._resolve_view_render(
                        source_dir, view_name, file_paths_set
                    )

                # 2. EJS include(...) resolution e.g., include(partials/header)
                elif imp.startswith("include("):
                    inc_path = imp[8:-1].strip()
                    target_file = DependencyAnalyzer._resolve_ejs_include(
                        source_dir, inc_path, file_paths_set
                    )

                # 3. HTML/CSS asset(...) resolution
                elif imp.startswith("asset("):
                    asset_path = imp[6:-1].strip()
                    target_file = DependencyAnalyzer._resolve_asset_reference(
                        asset_path, file_paths_set
                    )

                # 4. Standard JS / TS import resolution
                elif source_lang in ("JavaScript", "TypeScript"):
                    target_file = DependencyAnalyzer._resolve_js_import(
                        source_file, source_dir, imp, file_paths_set
                    )

                # 5. Python import resolution
                elif source_lang == "Python":
                    target_file = DependencyAnalyzer._resolve_python_import(
                        source_file, source_dir, imp, file_paths_set, class_to_file
                    )

                # 6. Java import resolution
                elif source_lang == "Java":
                    target_file = DependencyAnalyzer._resolve_java_import(
                        source_file, imp, file_paths_set, class_to_file, java_packages
                    )

                if target_file and target_file != source_file and target_file in file_paths_set:
                    edge_key = (source_file, target_file)
                    if edge_key not in edges_set:
                        edges_set.add(edge_key)
                        dependencies.append(
                            DependencyInfo(
                                source_file=source_file,
                                target_file=target_file,
                                import_statement=imp,
                            )
                        )

        # Construct nodes & edges for GraphData
        nodes: List[GraphNode] = []
        for f in files:
            nodes.append(
                GraphNode(
                    id=f.path,
                    label=os.path.basename(f.path),
                    type="file",
                    language=f.language,
                )
            )

        edges: List[GraphEdge] = []
        for i, (src, tgt) in enumerate(edges_set):
            edges.append(
                GraphEdge(
                    id=f"e-{i}-{src}->{tgt}",
                    source=src,
                    target=tgt,
                    type="import",
                )
            )

        return dependencies, GraphData(nodes=nodes, edges=edges)

    @staticmethod
    def _resolve_view_render(source_dir: str, view_name: str, file_paths_set: Set[str]) -> str | None:
        candidates = [
            view_name,
            f"views/{view_name}",
            f"views/{view_name}.ejs",
            f"views/{view_name}.html",
            f"{view_name}.ejs",
            f"{view_name}.html",
        ]
        for cand in candidates:
            norm = os.path.normpath(cand)
            if norm in file_paths_set:
                return norm
        return None

    @staticmethod
    def _resolve_ejs_include(source_dir: str, inc_path: str, file_paths_set: Set[str]) -> str | None:
        candidates = [
            os.path.join(source_dir, inc_path),
            os.path.join(source_dir, inc_path + ".ejs"),
            os.path.join(source_dir, inc_path + ".html"),
            inc_path,
            inc_path + ".ejs",
            f"views/{inc_path}",
            f"views/{inc_path}.ejs",
        ]
        for cand in candidates:
            norm = os.path.normpath(cand)
            if norm in file_paths_set:
                return norm
        return None

    @staticmethod
    def _resolve_asset_reference(asset_path: str, file_paths_set: Set[str]) -> str | None:
        clean = asset_path.lstrip("/")
        candidates = [
            clean,
            f"public/{clean}",
            f"static/{clean}",
        ]
        for cand in candidates:
            norm = os.path.normpath(cand)
            if norm in file_paths_set:
                return norm
        return None

    @staticmethod
    def _resolve_js_import(
        source_file: str, source_dir: str, imp_stmt: str, file_paths_set: Set[str]
    ) -> str | None:
        match = re.search(r"['\"]([^'\"]+)['\"]", imp_stmt)
        if not match:
            return None
        import_path = match.group(1)

        if not import_path.startswith("."):
            return None

        norm_path = os.path.normpath(os.path.join(source_dir, import_path))

        candidates = [
            norm_path,
            norm_path + ".js",
            norm_path + ".jsx",
            norm_path + ".ts",
            norm_path + ".tsx",
            os.path.join(norm_path, "index.js"),
            os.path.join(norm_path, "index.jsx"),
            os.path.join(norm_path, "index.ts"),
            os.path.join(norm_path, "index.tsx"),
        ]

        for cand in candidates:
            if cand in file_paths_set:
                return cand
        return None

    @staticmethod
    def _resolve_python_import(
        source_file: str,
        source_dir: str,
        imp_stmt: str,
        file_paths_set: Set[str],
        class_to_file: Dict[str, str],
    ) -> str | None:
        module_path = ""
        imported_symbol = ""

        if imp_stmt.startswith("from "):
            parts = imp_stmt.split(" import ")
            if len(parts) == 2:
                module_path = parts[0].replace("from ", "").strip()
                imported_symbol = parts[1].strip().split()[0]
        elif imp_stmt.startswith("import "):
            module_path = imp_stmt.replace("import ", "").strip().split()[0].split(",")[0]

        if not module_path:
            return None

        dot_prefix_count = 0
        while module_path.startswith("."):
            dot_prefix_count += 1
            module_path = module_path[1:]

        if dot_prefix_count > 0:
            cur = source_dir
            for _ in range(dot_prefix_count - 1):
                cur = os.path.dirname(cur)
            base_rel = os.path.join(cur, module_path.replace(".", "/")) if module_path else cur
        else:
            base_rel = module_path.replace(".", "/")

        candidates = [
            base_rel + ".py",
            os.path.join(base_rel, "__init__.py"),
        ]

        for cand in candidates:
            norm_cand = os.path.normpath(cand)
            if norm_cand in file_paths_set:
                return norm_cand

        if imported_symbol in class_to_file:
            return class_to_file[imported_symbol]

        return None

    @staticmethod
    def _resolve_java_import(
        source_file: str,
        imp_stmt: str,
        file_paths_set: Set[str],
        class_to_file: Dict[str, str],
        java_packages: Dict[str, str],
    ) -> str | None:
        cleaned = imp_stmt.replace("import ", "").replace(";", "").strip()
        parts = cleaned.split(".")
        if not parts:
            return None

        class_name = parts[-1]
        if class_name in class_to_file:
            return class_to_file[class_name]

        path_candidate = "/".join(parts) + ".java"
        for fpath in file_paths_set:
            if fpath.endswith(path_candidate):
                return fpath

        return None
