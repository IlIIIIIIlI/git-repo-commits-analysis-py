from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    github_token: str = Field(..., description="GitHub Personal Access Token")
    output_base_dir: Path = Field(
        default=Path("./github_diffs"), description="Output directory for diffs"
    )
    repositories: str = Field(
        default="reworkd/AgentGPT", description="Comma-separated list of repositories"
    )
    start_date: str = Field(..., description="Start date for analysis (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date for analysis (YYYY-MM-DD)")
    request_delay: float = Field(
        default=1.0, description="Delay between API requests in seconds"
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @property
    def repositories_list(self) -> List[tuple]:
        """Convert repository strings to (owner, repo) tuples"""
        repos = [repo.strip() for repo in self.repositories.split(",")]
        return [tuple(repo.split("/")) for repo in repos if repo]
