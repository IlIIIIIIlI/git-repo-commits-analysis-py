import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from config import Settings


def analyze_repository_diffs(repo_dir: Path) -> Dict:
    """分析仓库的diff数据"""
    stats = {
        "total_commits": 0,
        "total_additions": 0,
        "total_deletions": 0,
        "commits_by_author": defaultdict(int),
        "changes_by_author": defaultdict(lambda: {"additions": 0, "deletions": 0}),
        "commits_by_date": defaultdict(int),
        "daily_stats": defaultdict(
            lambda: {"additions": 0, "deletions": 0, "commits": 0}
        ),
    }

    for date_dir in repo_dir.glob("*"):
        if not date_dir.is_dir():
            continue

        metadata_path = date_dir / "metadata.json"
        if not metadata_path.exists():
            continue

        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        date = date_dir.name

        for commit in metadata:
            stats["total_commits"] += 1
            stats["total_additions"] += commit["stats"]["additions"]
            stats["total_deletions"] += commit["stats"]["deletions"]

            author = commit["author"]
            stats["commits_by_author"][author] += 1
            stats["changes_by_author"][author]["additions"] += commit["stats"][
                "additions"
            ]
            stats["changes_by_author"][author]["deletions"] += commit["stats"][
                "deletions"
            ]

            stats["commits_by_date"][date] += 1
            stats["daily_stats"][date]["additions"] += commit["stats"]["additions"]
            stats["daily_stats"][date]["deletions"] += commit["stats"]["deletions"]
            stats["daily_stats"][date]["commits"] += 1

    return stats


def generate_report():
    """生成分析报告"""
    settings = Settings()

    for owner, repo in settings.repositories_list:
        repo_dir = settings.output_base_dir / f"{owner}_{repo}"
        if not repo_dir.exists():
            print(f"No data found for {owner}/{repo}")
            continue

        stats = analyze_repository_diffs(repo_dir)

        report_path = repo_dir / "analysis_report.json"
        report_path.write_text(
            json.dumps(stats, indent=2, default=str), encoding="utf-8"
        )

        print(f"\nAnalysis Report for {owner}/{repo}:")
        print(f"Total Commits: {stats['total_commits']}")
        print(f"Total Lines Added: {stats['total_additions']}")
        print(f"Total Lines Deleted: {stats['total_deletions']}")
        print("\nTop Contributors:")
        for author, count in sorted(
            stats["commits_by_author"].items(), key=lambda x: x[1], reverse=True
        )[:5]:
            print(f"  {author}: {count} commits")


if __name__ == "__main__":
    generate_report()
