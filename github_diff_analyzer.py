import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Generator, List, Optional

import requests
from tqdm import tqdm

from config import Settings
from models import CommitInfo


class GitHubDiffAnalyzer:
    def __init__(self, settings: Settings):
        self.settings = settings
        token = settings.github_token.strip()
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self.base_url = "https://api.github.com"
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("github_diff_analyzer.log"),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def get_commit_diff(self, owner: str, repo: str, commit_sha: str) -> Optional[str]:
        """获取特定commit的diff内容"""
        url = f"{self.base_url}/repos/{owner}/{repo}/commits/{commit_sha}"
        try:
            response = requests.get(
                url,
                headers=dict(
                    self.headers, **{"Accept": "application/vnd.github.v3.diff"}
                ),
            )
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching diff for commit {commit_sha}: {e}")
            return None

    def _get_commit_stats(self, owner: str, repo: str, sha: str) -> Dict[str, int]:
        """获取commit的统计信息"""
        url = f"{self.base_url}/repos/{owner}/{repo}/commits/{sha}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return {
                "additions": data["stats"]["additions"],
                "deletions": data["stats"]["deletions"],
                "total": data["stats"]["total"],
            }
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching stats for commit {sha}: {e}")
            return {"additions": 0, "deletions": 0, "total": 0}

    def validate_token(self):
        """验证 token 是否有效"""
        try:
            user_response = requests.get(
                "https://api.github.com/user", headers=self.headers
            )
            self.logger.debug(f"User API Response: {user_response.status_code}")

            if user_response.status_code == 200:
                self.logger.info("Successfully authenticated with GitHub")

                # 检查仓库访问权限
                owner, repo = self.settings.repositories_list[0]
                repo_url = f"{self.base_url}/repos/{owner}/{repo}"
                self.logger.debug(f"Checking repository access: {repo_url}")

                repo_response = requests.get(repo_url, headers=self.headers)
                self.logger.debug(
                    f"Repository API Response: {repo_response.status_code}"
                )
                self.logger.debug(f"Repository Response: {repo_response.text}")

                if repo_response.status_code == 200:
                    self.logger.info(f"Successfully accessed repository {owner}/{repo}")
                    return True
                else:
                    self.logger.error(
                        f"Repository access failed: {repo_response.json().get('message', 'Unknown error')}"
                    )
                    return False
            else:
                self.logger.error(
                    f"Token validation failed: {user_response.json().get('message', 'Unauthorized')}"
                )
                return False

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error during validation: {e}")
            return False

    def check_rate_limit(self):
        """检查 API 速率限制"""
        try:
            response = requests.get(
                "https://api.github.com/rate_limit", headers=self.headers
            )
            if response.status_code == 200:
                limits = response.json()
                self.logger.debug(f"Rate limit status: {json.dumps(limits, indent=2)}")
                core = limits["resources"]["core"]
                self.logger.info(
                    f"API calls remaining: {core['remaining']}/{core['limit']}"
                )
                return core["remaining"] > 0
            return True
        except Exception as e:
            self.logger.error(f"Error checking rate limit: {e}")
            return True

    def date_range(self, start_date: str, end_date: str) -> Generator[str, None, None]:
        """生成日期范围"""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        current = start
        while current <= end:
            yield current.strftime("%Y-%m-%d")
            current += timedelta(days=1)

    def get_repository_commits(
        self, owner: str, repo: str, date: str
    ) -> List[CommitInfo]:
        """获取某一天的所有commits"""
        self.logger.info(f"Fetching commits for {owner}/{repo} on {date}")
        commits = []
        page = 1

        while True:
            url = f"{self.base_url}/repos/{owner}/{repo}/commits"
            params = {
                "since": f"{date}T00:00:00Z",
                "until": f"{date}T23:59:59Z",
                "page": page,
                "per_page": 100,
            }

            try:
                response = requests.get(url, headers=self.headers, params=params)
                self.logger.debug(
                    f"Commits API Response: {response.status_code} for page {page}"
                )
                response.raise_for_status()

                page_commits = response.json()
                if not page_commits:
                    break

                for commit_data in page_commits:
                    commit = CommitInfo(
                        sha=commit_data["sha"],
                        message=commit_data["commit"]["message"],
                        author=commit_data["commit"]["author"]["name"],
                        date=datetime.strptime(
                            commit_data["commit"]["author"]["date"],
                            "%Y-%m-%dT%H:%M:%SZ",
                        ),
                        stats=self._get_commit_stats(owner, repo, commit_data["sha"]),
                    )
                    commits.append(commit)

                page += 1
                time.sleep(self.settings.request_delay)

            except requests.exceptions.RequestException as e:
                self.logger.error(f"Error fetching commits: {e}")
                break

        return commits

    def save_repository_diffs(self, owner: str, repo: str):
        """保存仓库的diff信息"""
        repo_dir = self.settings.output_base_dir / f"{owner}_{repo}"
        repo_dir.mkdir(parents=True, exist_ok=True)

        dates = list(self.date_range(self.settings.start_date, self.settings.end_date))
        if not dates:
            self.logger.error("No valid dates to process")
            return

        self.logger.info(f"Analyzing commits from {dates[0]} to {dates[-1]}")

        for date in tqdm(dates, desc=f"Processing {owner}/{repo}"):
            date_dir = repo_dir / date
            date_dir.mkdir(exist_ok=True)

            commits = self.get_repository_commits(owner, repo, date)
            if not commits:
                self.logger.info(f"No commits found for {owner}/{repo} on {date}")
                continue

            commits_meta = []
            for commit in commits:
                diff = self.get_commit_diff(owner, repo, commit.sha)
                if diff:
                    diff_path = date_dir / f"{commit.sha}.diff"
                    diff_path.write_text(diff, encoding="utf-8")

                    commits_meta.append(
                        {
                            "sha": commit.sha,
                            "message": commit.message,
                            "author": commit.author,
                            "date": commit.date.isoformat(),
                            "stats": commit.stats,
                        }
                    )

            if commits_meta:
                metadata_path = date_dir / "metadata.json"
                metadata_path.write_text(
                    json.dumps(commits_meta, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                self.logger.info(f"Processed {len(commits_meta)} commits for {date}")

    def analyze(self):
        """分析指定的仓库"""
        if not self.validate_token():
            self.logger.error(
                "Token validation failed. Please check your token and permissions."
            )
            return

        if not self.check_rate_limit():
            self.logger.error(
                "API rate limit exceeded. Please wait or use a different token."
            )
            return

        for owner, repo in self.settings.repositories_list:
            self.logger.info(f"Starting analysis for {owner}/{repo}")
            self.save_repository_diffs(owner, repo)
            self.logger.info(f"Completed analysis for {owner}/{repo}")


def main():
    settings = Settings()
    analyzer = GitHubDiffAnalyzer(settings)
    analyzer.analyze()


if __name__ == "__main__":
    main()
