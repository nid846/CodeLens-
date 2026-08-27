import os
from typing import List, Dict, Set, Optional
from app.models.analysis import AnalysisResult, FileInfo, ClassInfo, FunctionInfo
from app.models.chunk import CodeChunk


class ChunkingService:
    @staticmethod
    def extract_chunks_from_analysis(
        analysis_result: AnalysisResult,
        file_contents: Dict[str, str],
        repository_id: Optional[str] = None,
    ) -> List[CodeChunk]:
        """
        Transforms Module 1 AnalysisResult and raw file contents into structured,
        searchable CodeChunk objects.
        
        Chunking hierarchy:
        1. Functions / Methods (highest fidelity)
        2. Classes (for classes with no separately extracted methods or structural class chunks)
        3. File-level fallback (for files without extracted classes or functions)
        """
        if not repository_id:
            repository_id = analysis_result.repository.name
            if analysis_result.repository.url:
                clean_url = analysis_result.repository.url.rstrip("/")
                parts = clean_url.split("/")
                if len(parts) >= 2:
                    repository_id = f"{parts[-2]}/{parts[-1]}"

        # Index dependencies by source_file
        deps_by_file: Dict[str, List[str]] = {}
        for dep in analysis_result.dependencies:
            deps_by_file.setdefault(dep.source_file, []).append(dep.target_file)

        # Index classes by file_path
        classes_by_file: Dict[str, List[ClassInfo]] = {}
        for cls in analysis_result.classes:
            classes_by_file.setdefault(cls.file_path, []).append(cls)

        # Index functions by file_path
        functions_by_file: Dict[str, List[FunctionInfo]] = {}
        for fn in analysis_result.functions:
            functions_by_file.setdefault(fn.file_path, []).append(fn)

        chunks: List[CodeChunk] = []

        for file_info in analysis_result.files:
            fpath = file_info.path
            content = file_contents.get(fpath, "")
            if not content.strip():
                continue

            lines = content.splitlines()
            total_lines = len(lines)

            file_fns = functions_by_file.get(fpath, [])
            file_classes = classes_by_file.get(fpath, [])
            file_deps = deps_by_file.get(fpath, [])

            covered_lines: Set[int] = set()

            # 1. Extract Function/Method Chunks
            for fn in file_fns:
                start_line = max(1, min(fn.start_line, total_lines))
                end_line = max(start_line, min(fn.end_line, total_lines))
                
                # Extract code snippet from lines
                snippet = "\n".join(lines[start_line - 1 : end_line])
                if not snippet.strip():
                    continue

                for l in range(start_line, end_line + 1):
                    covered_lines.add(l)

                content_hash = CodeChunk.compute_content_hash(snippet)
                chunk_id = CodeChunk.generate_chunk_id(
                    repository_id=repository_id,
                    file_path=fpath,
                    start_line=start_line,
                    end_line=end_line,
                    name=fn.name,
                )

                chunk = CodeChunk(
                    chunk_id=chunk_id,
                    repository_id=repository_id,
                    file_path=fpath,
                    file_name=file_info.name,
                    language=file_info.language,
                    class_name=fn.containing_class,
                    function_name=fn.name,
                    code=snippet,
                    start_line=start_line,
                    end_line=end_line,
                    imports=[],
                    dependencies=file_deps,
                    content_hash=content_hash,
                )
                chunks.append(chunk)

            # 2. Extract Class Chunks (if class has substantial un-chunked content or standalone)
            for cls in file_classes:
                start_line = max(1, min(cls.start_line, total_lines))
                end_line = max(start_line, min(cls.end_line, total_lines))
                
                # If all lines of class are already covered by functions, we still create a class header/summary chunk
                # or standalone class chunk if no functions exist
                cls_fns = [fn for fn in file_fns if fn.containing_class == cls.name]
                if not cls_fns:
                    snippet = "\n".join(lines[start_line - 1 : end_line])
                    if snippet.strip():
                        content_hash = CodeChunk.compute_content_hash(snippet)
                        chunk_id = CodeChunk.generate_chunk_id(
                            repository_id=repository_id,
                            file_path=fpath,
                            start_line=start_line,
                            end_line=end_line,
                            name=cls.name,
                        )
                        chunk = CodeChunk(
                            chunk_id=chunk_id,
                            repository_id=repository_id,
                            file_path=fpath,
                            file_name=file_info.name,
                            language=file_info.language,
                            class_name=cls.name,
                            function_name=None,
                            code=snippet,
                            start_line=start_line,
                            end_line=end_line,
                            imports=[],
                            dependencies=file_deps,
                            content_hash=content_hash,
                        )
                        chunks.append(chunk)

            # 3. Fallback: If file has no functions and no classes, chunk entire file (or split if large)
            if not file_fns and not file_classes:
                # File-level chunk
                # Handle large files (> 300 lines) gracefully with sliding window
                max_chunk_lines = 150
                overlap = 25

                if total_lines <= max_chunk_lines:
                    snippet = content
                    content_hash = CodeChunk.compute_content_hash(snippet)
                    chunk_id = CodeChunk.generate_chunk_id(
                        repository_id=repository_id,
                        file_path=fpath,
                        start_line=1,
                        end_line=total_lines,
                        name="file_root",
                    )
                    chunk = CodeChunk(
                        chunk_id=chunk_id,
                        repository_id=repository_id,
                        file_path=fpath,
                        file_name=file_info.name,
                        language=file_info.language,
                        class_name=None,
                        function_name=None,
                        code=snippet,
                        start_line=1,
                        end_line=total_lines,
                        imports=[],
                        dependencies=file_deps,
                        content_hash=content_hash,
                    )
                    chunks.append(chunk)
                else:
                    curr_start = 1
                    while curr_start <= total_lines:
                        curr_end = min(curr_start + max_chunk_lines - 1, total_lines)
                        snippet = "\n".join(lines[curr_start - 1 : curr_end])
                        if snippet.strip():
                            content_hash = CodeChunk.compute_content_hash(snippet)
                            chunk_id = CodeChunk.generate_chunk_id(
                                repository_id=repository_id,
                                file_path=fpath,
                                start_line=curr_start,
                                end_line=curr_end,
                                name=f"part_{curr_start}",
                            )
                            chunk = CodeChunk(
                                chunk_id=chunk_id,
                                repository_id=repository_id,
                                file_path=fpath,
                                file_name=file_info.name,
                                language=file_info.language,
                                class_name=None,
                                function_name=None,
                                code=snippet,
                                start_line=curr_start,
                                end_line=curr_end,
                                imports=[],
                                dependencies=file_deps,
                                content_hash=content_hash,
                            )
                            chunks.append(chunk)
                        if curr_end >= total_lines:
                            break
                        curr_start += (max_chunk_lines - overlap)

        return chunks
