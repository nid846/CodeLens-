from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field


class AnalysisRequest(BaseModel):
    github_url: str = Field(..., description="Public GitHub repository URL")


class RepositoryInfo(BaseModel):
    name: str
    url: str
    branch: str = "main"


class AnalysisSummary(BaseModel):
    total_files: int = 0
    total_classes: int = 0
    total_functions: int = 0
    total_dependencies: int = 0


class FileInfo(BaseModel):
    path: str
    name: str
    language: str
    size: int
    class_count: int = 0
    function_count: int = 0


class ClassInfo(BaseModel):
    name: str
    file_path: str
    start_line: int
    end_line: int


class FunctionInfo(BaseModel):
    name: str
    file_path: str
    containing_class: Optional[str] = None
    start_line: int
    end_line: int
    parameters: List[str] = []


class DependencyInfo(BaseModel):
    source_file: str
    target_file: str
    import_statement: str


class GraphNode(BaseModel):
    id: str
    label: str
    type: str = "file"
    language: str = ""


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str = "import"


class GraphData(BaseModel):
    nodes: List[GraphNode] = []
    edges: List[GraphEdge] = []


class AnalysisResult(BaseModel):
    repository: RepositoryInfo
    summary: AnalysisSummary
    files: List[FileInfo] = []
    classes: List[ClassInfo] = []
    functions: List[FunctionInfo] = []
    dependencies: List[DependencyInfo] = []
    graph: GraphData = Field(default_factory=GraphData)
    failed_files: List[str] = []
