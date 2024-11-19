from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class CommitInfo:
    sha: str
    message: str
    author: str
    date: datetime
    stats: Dict[str, int]
    diff: Optional[str] = None
