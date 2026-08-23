from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass, field
from app.models.analysis import ClassInfo, FunctionInfo


@dataclass
class ParseResult:
    classes: List[ClassInfo] = field(default_factory=list)
    functions: List[FunctionInfo] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    package_name: str = ""


class BaseParser(ABC):
    @abstractmethod
    def parse_file(self, content: str, file_path: str) -> ParseResult:
        """Parse source code string and extract classes, functions, and import statements."""
        pass
