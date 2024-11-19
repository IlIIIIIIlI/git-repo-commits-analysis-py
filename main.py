# main.py
import asyncio
import json
import os
import uuid
from pathlib import Path
from typing import List, Optional, Dict
from fastapi import FastAPI, HTTPException, BackgroundTasks
import time
from datetime import datetime
from dotenv import load_dotenv
from report_generator import ReportGenerator
from report_models import BatchReportStatus, ReportRequest, CommitReport

from models import (
    CommitDiff,
    CommitSummary,
    AnalysisRequest,
    AnalysisTask,
    AnalysisStatus,
    CommitStats
)
from github_diff_analyzer import GitHubDiffAnalyzer
from config import Settings

# Load environment variables
load_dotenv()

app = FastAPI(title="GitHub Analyzer API")
report_generator = ReportGenerator()

# Global storage
commit_storage: List[CommitDiff] = []
analysis_tasks: Dict[str, AnalysisTask] = {}

def reload_commits():
    """Reload all commits from filesystem"""
    global commit_storage
    commit_storage = load_commits_from_fs()

def get_repository_name(repo_dir: Path) -> str:
    return repo_dir.name.replace("_", "/")

def get_commit_dates(repo_dir: Path) -> List[str]:
    """Get list of dates that have been analyzed for a repository"""
    dates = []
    if repo_dir.exists():
        for date_dir in repo_dir.glob("*"):
            if date_dir.is_dir() and date_dir.name != ".git":
                dates.append(date_dir.name)
    return sorted(dates)

def load_commits_from_fs(base_dir: Path = Path("./github_diffs")) -> List[CommitDiff]:
    commits = []
    if not base_dir.exists():
        return commits

    for repo_dir in base_dir.glob("*"):
        if not repo_dir.is_dir():
            continue
            
        repository = get_repository_name(repo_dir)
        for date_dir in repo_dir.glob("*"):
            if not date_dir.is_dir() or date_dir.name == ".git":
                continue
                
            metadata_path = date_dir / "metadata.json"
            if not metadata_path.exists():
                continue
                
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                for commit_data in metadata:
                    diff_path = date_dir / f"{commit_data['sha']}.diff"
                    diff_content = None
                    if diff_path.exists():
                        diff_content = diff_path.read_text(encoding="utf-8")
                        
                    commit = CommitDiff(
                        id=commit_data['sha'],
                        title=commit_data['message'],
                        author=commit_data['author'],
                        date=datetime.fromisoformat(commit_data['date']),
                        stats=CommitStats(**commit_data['stats']),
                        diff_content=diff_content,
                        repository=repository
                    )
                    commits.append(commit)
            except Exception as e:
                print(f"Error loading commits from {metadata_path}: {e}")
                continue
                
    return commits

def get_missing_dates(start_date: str, end_date: str, existing_dates: List[str]) -> List[str]:
    """Get list of dates that need to be analyzed"""
    from datetime import datetime, timedelta

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    all_dates = []
    current = start
    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        if date_str not in existing_dates:
            all_dates.append(date_str)
        current += timedelta(days=1)
    
    return all_dates

async def run_analysis(task_id: str, repositories: str, start_date: str, end_date: str):
    """Run the analysis task"""
    task = analysis_tasks[task_id]
    try:
        task.status = AnalysisStatus.RUNNING

        # Check existing data
        repo_name = repositories.replace("/", "_")
        repo_dir = Path("./github_diffs") / repo_name
        existing_dates = get_commit_dates(repo_dir)
        
        # Get the date that needs to be analyzed
        missing_dates = get_missing_dates(start_date, end_date, existing_dates)
        
        if not missing_dates:
            task.status = AnalysisStatus.COMPLETED
            task.completed_at = datetime.now()
            task.processed_commits = len([c for c in commit_storage if c.repository == repositories])
            return

        # Create new setup to analyze only missing dates
        settings_dict = {
            "github_token": os.getenv("GITHUB_TOKEN"),
            "output_base_dir": "./github_diffs",
            "repositories": repositories,
            "start_date": missing_dates[0],
            "end_date": missing_dates[-1],
            "request_delay": 1.0
        }
        
        settings = Settings(**settings_dict)
        analyzer = GitHubDiffAnalyzer(settings)
        analyzer.analyze()
        
        # Reload all commits
        reload_commits()
        
        task.status = AnalysisStatus.COMPLETED
        task.completed_at = datetime.now()
        task.processed_commits = len([c for c in commit_storage if c.repository == repositories])
        
    except Exception as e:
        task.status = AnalysisStatus.FAILED
        task.error = str(e)
        print(f"Analysis failed: {str(e)}")

class Config:
    BASE_DIR = Path.cwd()  # 获取当前工作目录
    REPORTS_BASE_DIR = BASE_DIR / "reports"
    DIFFS_BASE_DIR = BASE_DIR / "github_diffs"


@app.on_event("startup")
async def startup_event():
    """Initialize necessary directories and load existing data"""
    print(f"Current working directory: {Config.BASE_DIR}")
    print("Initializing directories...")
    
    # Create necessary directories
    Config.REPORTS_BASE_DIR.mkdir(exist_ok=True)
    Config.DIFFS_BASE_DIR.mkdir(exist_ok=True)
    
    print(f"Reports directory: {Config.REPORTS_BASE_DIR}")
    print(f"Diffs directory: {Config.DIFFS_BASE_DIR}")
    
    # Load commits
    reload_commits()
    
    # Print directory structure
    print("\nCurrent reports structure:")
    for repo_dir in Config.REPORTS_BASE_DIR.glob("*"):
        if repo_dir.is_dir():
            repo_name = repo_dir.name.replace("_", "/")
            print(f"\nRepository: {repo_name}")
            for date_dir in repo_dir.glob("*"):
                if date_dir.is_dir():
                    json_files = list(date_dir.glob("*.json"))
                    print(f"  {date_dir.name}: {len(json_files)} reports")
                    for json_file in json_files:
                        print(f"    - {json_file.name}")


@app.post("/analyze", response_model=Dict, tags=["analysis"])
async def start_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
):
    """Start a new analysis task"""
    task_id = str(uuid.uuid4())
    repo_name = request.repositories.replace("/", "_")
    repo_dir = Path("./github_diffs") / repo_name
    existing_dates = get_commit_dates(repo_dir)
    missing_dates = get_missing_dates(request.start_date, request.end_date, existing_dates)
    
    task = AnalysisTask(
        id=task_id,
        repositories=request.repositories,
        start_date=request.start_date,
        end_date=request.end_date,
        status=AnalysisStatus.PENDING,
        created_at=datetime.now()
    )
    analysis_tasks[task_id] = task
    
    background_tasks.add_task(
        run_analysis,
        task_id,
        request.repositories,
        request.start_date,
        request.end_date
    )
    
    return {
        "task_id": task_id,
        "message": "Analysis started",
        "repositories": request.repositories,
        "start_date": request.start_date,
        "end_date": request.end_date,
        "existing_dates": existing_dates,
        "dates_to_analyze": missing_dates,
        "current_commits": len([c for c in commit_storage if c.repository == request.repositories])
    }

@app.get("/tasks/{task_id}", response_model=AnalysisTask, tags=["analysis"])
async def get_task_status(task_id: str):
    """Get status of a specific analysis task"""
    if task_id not in analysis_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return analysis_tasks[task_id]

@app.get("/commits", response_model=List[CommitDiff], tags=["commits"])
async def get_all_commits():
    """Get all commits"""
    return commit_storage

@app.get("/commits/summary", response_model=List[CommitSummary], tags=["commits"])
async def get_commits_summary():
    """Get summary of all commits with their titles and stats"""
    return [CommitSummary(
        id=commit.id,
        title=commit.title,
        stats=commit.stats,
        repository=commit.repository,
        date=commit.date
    ) for commit in commit_storage]

@app.get("/commits/{commit_id}", response_model=CommitDiff, tags=["commits"])
async def get_commit(commit_id: str):
    """Get a specific commit by ID"""
    for commit in commit_storage:
        if commit.id == commit_id:
            return commit
    raise HTTPException(status_code=404, detail="Commit not found")

@app.get("/commits/by-author/{author}", response_model=List[CommitDiff], tags=["commits"])
async def get_commits_by_author(author: str):
    """Get all commits by a specific author"""
    matched_commits = [commit for commit in commit_storage if commit.author == author]
    if not matched_commits:
        raise HTTPException(status_code=404, detail=f"No commits found for author: {author}")
    return matched_commits

@app.get("/commits/by-date/{date}", response_model=List[CommitDiff], tags=["commits"])
async def get_commits_by_date(date: str):
    """Get all commits on a specific date"""
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
    matched_commits = [
        commit for commit in commit_storage 
        if commit.date.date() == target_date
    ]
    
    if not matched_commits:
        raise HTTPException(status_code=404, detail=f"No commits found for date: {date}")
    return matched_commits

@app.get("/commits/stats/summary", response_model=Dict, tags=["stats"])
async def get_stats_summary():
    """Get summary of commit statistics with size categorization"""
    summary = {
        "small": {"additions": 0, "deletions": 0, "total": 0},
        "medium": {"additions": 0, "deletions": 0, "total": 0},
        "large": {"additions": 0, "deletions": 0, "total": 0}
    }
    
    for commit in commit_storage:
        if commit.stats.additions_size:
            summary[commit.stats.additions_size]["additions"] += 1
        if commit.stats.deletions_size:
            summary[commit.stats.deletions_size]["deletions"] += 1
        if commit.stats.total_size:
            summary[commit.stats.total_size]["total"] += 1
            
    return summary

@app.get("/repositories", response_model=List[str], tags=["repositories"])
async def get_repositories():
    """Get list of all repositories"""
    return list(set(commit.repository for commit in commit_storage))

@app.get("/repositories/{repo}/dates", response_model=List[str], tags=["repositories"])
async def get_repository_dates(repo: str):
    """Get list of dates that have been analyzed for a repository"""
    repo_dir = Path("./github_diffs") / repo.replace("/", "_")
    return get_commit_dates(repo_dir)

@app.get("/health", tags=["system"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "commits_loaded": len(commit_storage),
        "repositories": list(set(commit.repository for commit in commit_storage)),
        "running_tasks": len([t for t in analysis_tasks.values() if t.status == AnalysisStatus.RUNNING])
    }

# for report generation
@app.post("/reports/generate", response_model=CommitReport, tags=["reports"])
async def generate_commit_report(request: ReportRequest):
    """Generate a report for a specific commit or all commits on a date"""
    try:
        repo_dir = Path("./github_diffs") / request.repository.replace("/", "_")
        date_dir = repo_dir / request.date
        
        if not date_dir.exists():
            raise HTTPException(
                status_code=404,
                detail=f"No data found for repository {request.repository} on date {request.date}"
            )

        metadata_path = date_dir / "metadata.json"
        if not metadata_path.exists():
            raise HTTPException(
                status_code=404,
                detail="No commit metadata found"
            )

        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        
        # If commit_sha is provided, generate report for specific commit
        if request.commit_sha:
            commit_data = None
            for commit in metadata:
                if commit["sha"] == request.commit_sha:
                    commit_data = commit
                    break
                    
            if not commit_data:
                raise HTTPException(
                    status_code=404,
                    detail=f"Commit {request.commit_sha} not found"
                )

            # Check if report already exists
            existing_report = report_generator.get_report(request.repository, request.commit_sha)
            if existing_report and existing_report.status == "completed":
                return existing_report

            # Get diff content
            diff_path = date_dir / f"{request.commit_sha}.diff"
            if not diff_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"Diff file not found for commit {request.commit_sha}"
                )

            diff_content = diff_path.read_text(encoding="utf-8")
            
            # Add repository to commit data
            commit_data["repository"] = request.repository
            
            # Generate report
            return await report_generator.generate_report(commit_data, diff_content)
            
        else:
            raise HTTPException(
                status_code=400,
                detail="commit_sha is required"
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating report: {str(e)}"
        )

@app.get("/reports/{repository}/{commit_sha}", response_model=CommitReport, tags=["reports"])
@app.get("/reports/{repository}/{commit_sha}", response_model=CommitReport, tags=["reports"])
async def get_commit_report(repository: str, commit_sha: str):
    """Get a generated report for a specific commit"""
    try:
        # Traverse all date directories to find reports
        reports_base = Path("./reports") / repository.replace("/", "_")
        if not reports_base.exists():
            raise HTTPException(
                status_code=404,
                detail=f"No reports found for repository {repository}"
            )
            
        for date_dir in reports_base.glob("*"):
            if not date_dir.is_dir():
                continue
                
            report_path = date_dir / f"{commit_sha}.json"
            if report_path.exists():
                try:
                    meta_data = json.loads(report_path.read_text(encoding="utf-8"))
                    return CommitReport(**meta_data)
                except Exception as e:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Error loading report: {str(e)}"
                    )
                    
        raise HTTPException(
            status_code=404,
            detail=f"Report not found for commit {commit_sha}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving report: {str(e)}"
        )

@app.get("/reports/{repository}/date/{date}", response_model=List[CommitReport], tags=["reports"])
async def get_reports_by_date(repository: str, date: str):
    """Get all reports for a specific date"""
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
        
    reports = report_generator.get_reports_by_date(repository, date)
    return reports

batch_tasks: Dict[str, BatchReportStatus] = {}

async def generate_reports_for_date(task_id: str, repository: str, date: str, force_regenerate: bool = False):
    task = batch_tasks[task_id]
    try:
        # Update task status
        task.status = "running"
        task.updated_at = datetime.now()
        
        repo_dir = Path("./github_diffs") / repository.replace("/", "_")
        date_dir = repo_dir / date
        
        if not date_dir.exists():
            # Create directory
            date_dir.mkdir(parents=True, exist_ok=True)
            
        # Make sure the reports directory exists
        reports_dir = Path("./reports") / repository.replace("/", "_") / date
        reports_dir.mkdir(parents=True, exist_ok=True)

        metadata_path = date_dir / "metadata.json"
        if not metadata_path.exists():
            task.status = "failed"
            task.error = "No commit metadata found"
            return

        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        diff_contents = {}
        
        for commit_data in metadata:
            commit_data["repository"] = repository
            diff_path = date_dir / f"{commit_data['sha']}.diff"
            if diff_path.exists():
                diff_contents[commit_data["sha"]] = diff_path.read_text(encoding="utf-8")

        task.total_commits = len(metadata)
        completed = await report_generator.generate_batch_reports(metadata, diff_contents)
        
        task.completed_commits = completed
        task.status = "completed"
        task.completed_at = datetime.now()
        task.updated_at = datetime.now()
        
    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        task.updated_at = datetime.now()

        
async def wait_for_analysis(repository: str, date: str, timeout: int = 300):
    """Wait for the analysis task to complete"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        repo_dir = Path("./github_diffs") / repository.replace("/", "_")
        date_dir = repo_dir / date
        metadata_path = date_dir / "metadata.json"
        
        if metadata_path.exists():
            return True
            
        await asyncio.sleep(5)
    
    raise TimeoutError(f"Analysis for {repository} on {date} did not complete in time")

@app.post("/reports/generate-batch", response_model=BatchReportStatus, tags=["reports"])
async def generate_batch_reports(
    request: ReportRequest,
    background_tasks: BackgroundTasks
):
    """Generate reports for all commits on a specific date"""
    task_id = str(uuid.uuid4())
    task = BatchReportStatus(
        task_id=task_id,
        repository=request.repository,
        date=request.date
    )
    batch_tasks[task_id] = task
    
    background_tasks.add_task(
        generate_reports_for_date,
        task_id,
        request.repository,
        request.date,
        request.force_regenerate
    )
    
    return task

@app.get("/reports/batch/{task_id}", response_model=BatchReportStatus, tags=["reports"])
async def get_batch_status(task_id: str):
    """Get status of a batch report generation task"""
    # Remove the curly braces and use task_id directly
    clean_task_id = task_id.strip('{}')
    if clean_task_id not in batch_tasks:
        raise HTTPException(
            status_code=404,
            detail=f"Batch task {clean_task_id} not found"
        )
    return batch_tasks[clean_task_id]

@app.get("/reports/list/{repository}/{date}", response_model=List[CommitReport])
async def list_date_reports(
    repository: str,
    date: str,
    include_content: bool = False
):
    """List all reports for a specific date"""
    try:
        # Debug logging
        print(f"Listing reports for repository: {repository}, date: {date}")
        
        # build path
        reports_dir = Path("reports")  # Use relative paths
        repo_path = repository.replace('/', '_')
        date_dir = reports_dir / repo_path / date
        
        print(f"Looking for reports in: {date_dir}")
        
        if not date_dir.exists():
            print(f"Directory not found: {date_dir}")
            return []
            
        reports = []
        # Iterate over JSON files
        for meta_file in date_dir.glob("*.json"):
            try:
                print(f"Processing file: {meta_file}")
                meta_data = json.loads(meta_file.read_text(encoding='utf-8'))
                
                # Make sure required fields exist
                if isinstance(meta_data, dict):
                    # Add or update necessary fields
                    meta_data.update({
                        "repository": repository,
                        "date": date if "date" not in meta_data else meta_data["date"],
                        "id": meta_file.stem if "id" not in meta_data else meta_data["id"],
                    })
                    
                    # Read the contents of MD file
                    if include_content:
                        md_file = meta_file.with_suffix('.md')
                        if md_file.exists():
                            meta_data["content"] = md_file.read_text(encoding='utf-8')
                    else:
                        meta_data["content"] = ""
                    
                    # Make sure all necessary fields are present
                    report = CommitReport(
                        id=meta_data.get("id", meta_file.stem),
                        repository=meta_data.get("repository", repository),
                        commit_sha=meta_data.get("commit_sha", meta_file.stem),
                        date=meta_data.get("date", date),
                        title=meta_data.get("title", ""),
                        content=meta_data.get("content", ""),
                        created_at=meta_data.get("created_at", datetime.now()),
                        updated_at=meta_data.get("updated_at", datetime.now()),
                        status=meta_data.get("status", "completed"),
                        error=meta_data.get("error", None)
                    )
                    reports.append(report)
                    print(f"Successfully processed report for commit: {report.commit_sha}")
                
            except Exception as e:
                print(f"Error processing file {meta_file}: {str(e)}")
                continue
        
        # Sort by creation time
        reports.sort(key=lambda x: x.created_at, reverse=True)
        print(f"Found {len(reports)} reports")
        
        return reports
        
    except Exception as e:
        print(f"Error in list_date_reports: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing reports: {str(e)}"
        )
    

@app.get("/debug/reports/structure", tags=["debug"])
async def get_reports_structure():
    """Get the current structure of reports directory"""
    try:
        structure = {}
        reports_dir = Config.REPORTS_BASE_DIR
        
        for repo_dir in reports_dir.glob("*"):
            if repo_dir.is_dir():
                repo_name = repo_dir.name.replace("_", "/")
                structure[repo_name] = {}
                
                for date_dir in repo_dir.glob("*"):
                    if date_dir.is_dir():
                        report_files = list(date_dir.glob("*.json"))
                        structure[repo_name][date_dir.name] = {
                            "report_count": len(report_files),
                            "reports": [f.stem for f in report_files]
                        }
                        
        return structure
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting reports structure: {str(e)}"
        )

@app.get("/debug/test-path/{repository}/{date}")
async def test_path(repository: str, date: str):
    """Test path construction and file access"""
    try:
        reports_dir = Path("reports")
        repo_path = repository.replace('/', '_')
        date_dir = reports_dir / repo_path / date
        
        return {
            "repository": repository,
            "date": date,
            "repo_path": repo_path,
            "full_path": str(date_dir),
            "exists": date_dir.exists(),
            "is_dir": date_dir.is_dir() if date_dir.exists() else False,
            "files": [str(f.name) for f in date_dir.glob("*.json")] if date_dir.exists() else [],
            "parent_exists": date_dir.parent.exists(),
            "cwd": str(Path.cwd()),
            "absolute_path": str(date_dir.absolute())
        }
    except Exception as e:
        return {"error": str(e)}
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)