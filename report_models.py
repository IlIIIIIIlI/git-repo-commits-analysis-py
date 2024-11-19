from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
import json
from pathlib import Path

class ReportRequest(BaseModel):
    repository: str = Field(..., description="Repository name (e.g., 'owner/repo')")
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    commit_sha: Optional[str] = Field(None, description="Specific commit SHA")
    force_regenerate: bool = Field(False, description="Force regenerate existing reports")

class CommitReport(BaseModel):
    id: str = Field(..., description="Report ID (commit SHA)")
    repository: str = Field(..., description="Repository name")
    commit_sha: str = Field(..., description="Commit SHA")
    date: str = Field(..., description="Date of the commit")
    title: str = Field(..., description="Commit title/message")
    content: str = Field(..., description="Generated report content")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    status: str = Field(default="pending")
    error: Optional[str] = None

class BatchReportStatus(BaseModel):
    task_id: str = Field(..., description="Batch task ID")
    repository: str = Field(..., description="Repository name")
    date: str = Field(..., description="Target date")
    total_commits: int = Field(0, description="Total number of commits to process")
    completed_commits: int = Field(0, description="Number of completed commits")
    status: str = Field(default="pending")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

class ReportStorage:
    def __init__(self, base_dir: str = "./reports"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.reports_file = self.base_dir / "reports.json"
        self.reports: Dict[str, Dict[str, CommitReport]] = {}
        self._load_reports()

    def _load_reports(self):
        """Load reports from JSON file"""
        if self.reports_file.exists():
            try:
                data = json.loads(self.reports_file.read_text())
                for repo, commits in data.items():
                    self.reports[repo] = {
                        sha: CommitReport(**report_data)
                        for sha, report_data in commits.items()
                    }
            except Exception as e:
                print(f"Error loading reports: {e}")
                self.reports = {}

    def _save_reports(self):
        """Save reports to JSON file"""
        data = {
            repo: {
                sha: report.dict()
                for sha, report in commits.items()
            }
            for repo, commits in self.reports.items()
        }
        self.reports_file.write_text(json.dumps(data, default=str, indent=2))

    def add_report(self, report: CommitReport):
        """Add or update a report"""
        if report.repository not in self.reports:
            self.reports[report.repository] = {}
        self.reports[report.repository][report.commit_sha] = report
        self._save_reports()

    def get_report(self, repository: str, commit_sha: str) -> Optional[CommitReport]:
        """Get a specific report"""
        return self.reports.get(repository, {}).get(commit_sha)

    def get_reports_by_date(self, repository: str, date: str) -> List[CommitReport]:
        """Get all reports for a repository on a specific date"""
        if repository not in self.reports:
            return []
        return [
            report for report in self.reports[repository].values()
            if report.date == date
        ]

    def get_all_reports(self, repository: str) -> List[CommitReport]:
        """Get all reports for a repository"""
        return list(self.reports.get(repository, {}).values())