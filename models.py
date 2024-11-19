# models.py
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, List
from pydantic import BaseModel, Field, computed_field

class AnalysisRequest(BaseModel):
    repositories: str = Field(..., description="Repository in format owner/repo")
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")

class AnalysisStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class AnalysisTask(BaseModel):
    id: str
    repositories: str
    start_date: str
    end_date: str
    status: AnalysisStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    processed_commits: int = 0
    total_commits: int = 0

class ChangeSize(str, Enum):
    SMALL = "small"      # 50-99
    MEDIUM = "medium"    # 100-199
    LARGE = "large"      # 200+

class CommitStats(BaseModel):
    additions: int = Field(default=0)
    deletions: int = Field(default=0)
    total: int = Field(default=0)

    @computed_field
    @property
    def additions_size(self) -> Optional[ChangeSize]:
        return self._get_size(self.additions)

    @computed_field
    @property
    def deletions_size(self) -> Optional[ChangeSize]:
        return self._get_size(self.deletions)

    @computed_field
    @property
    def total_size(self) -> Optional[ChangeSize]:
        return self._get_size(self.total)

    def _get_size(self, value: int) -> Optional[ChangeSize]:
        if value >= 200:
            return ChangeSize.LARGE
        elif value >= 100:
            return ChangeSize.MEDIUM
        elif value >= 50:
            return ChangeSize.SMALL
        return None

    class Config:
        from_attributes = True

class CommitSummary(BaseModel):
    id: str = Field(..., description="Commit SHA")
    title: str = Field(..., description="Commit message")
    stats: CommitStats
    repository: str
    date: datetime

class CommitDiff(CommitSummary):
    author: str = Field(..., description="Author name")
    diff_content: Optional[str] = Field(None, description="Diff content")

    class Config:
        from_attributes = True