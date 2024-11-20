# report_generator.py
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
import uuid
from tqdm import tqdm

from openai import OpenAI
from dotenv import load_dotenv

from report_models import CommitReport

load_dotenv()

REPORT_PROMPT = """
You are an expert developer. You know how a commit is valued, what are some key points on tech side needs to be emphasis.

You should generate the following format.
# Title
[{project_name}] Daily Iteration ({date}) - {focus}

## 💄 Key Code Changes, {diff}
 ⁠diff
// Show the most important code changes
•⁠  ⁠Old code
+ New code  // Add brief inline comments for key changes


## 🔍 Technical Highlights
- List 3-5 key technical elements
- Focus on frameworks/libraries used
- Highlight architectural decisions
- Note performance improvements

## 📝 Context
Brief paragraph explaining:
- Part of which larger changes
- Related commits
- Overall impact
- Evolution path

Guidelines:
1. Keep it focused on one main change
2. Show real code snippets
3. Add inline comments for technical details
4. Connect to broader development context
5. Use emojis for section clarity
6. Keep explanation under 100 words total
7. Highlight practical technical implementation
8. Note any best practices or patterns used


the total answer you generate should not more than 70 words. Strictly follow this requirements.
"""

class Config:
    BASE_DIR = Path.cwd()
    REPORTS_BASE_DIR = BASE_DIR / "reports"
    DIFFS_BASE_DIR = BASE_DIR / "github_diffs"

class ReportGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.reports_dir = Path("./reports")
        self.reports_dir.mkdir(exist_ok=True)

    def _format_prompt(self, commit_data: Dict, diff_content: str) -> str:
        """Format the prompt with commit data"""
        project_name = commit_data['repository'].split('/')[-1]
        date = datetime.fromisoformat(commit_data['date']).strftime('%Y.%m.%d')
        focus = commit_data['message'].split('\n')[0]

        return REPORT_PROMPT.format(
            project_name=project_name,
            date=date,
            focus=focus,
            diff=diff_content,
        )

    async def generate_report(self, commit_data: Dict, diff_content: str, show_progress: bool = False) -> CommitReport:
        """Generate a report for a commit using OpenAI"""
        if show_progress:
            print(f"\nProcessing commit: {commit_data['sha'][:8]} - {commit_data.get('message', '')[:50]}...")
            print(f"Repository: {commit_data.get('repository', 'Unknown')}")
            
        try:
            if "repository" not in commit_data:
                raise ValueError("Repository information missing")
                
            prompt = self._format_prompt(commit_data, diff_content)
            
            # First check if report already exists
            existing_report = self.get_report(commit_data['repository'], commit_data['sha'])
            if existing_report and existing_report.status == "completed":
                if show_progress:
                    print(f"✓ Found existing report for {commit_data['sha'][:8]}")
                return existing_report

            # Create initial report
            report = CommitReport(
                id=str(uuid.uuid4()),
                repository=commit_data['repository'],
                commit_sha=commit_data['sha'],
                date=commit_data['date'],
                title=commit_data.get('message', 'No message provided'),
                content="",
                status="processing"
            )
            self._save_report(report)

            # Generate report with retry logic
            max_retries = 3
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    if show_progress and attempt > 0:
                        print(f"Retry attempt {attempt + 1} for {commit_data['sha'][:8]}")

                    response = self.client.chat.completions.create(
                        model="gpt-4-1106-preview",
                        messages=[
                            {"role": "system", "content": "You are a technical writer specializing in creating detailed commit analysis reports. Focus on technical details and practical implementation. Remember your answer should not exceed a strictly word limit of 70."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.5
                    )
                    
                    report_content = response.choices[0].message.content
                    report.content = report_content
                    report.status = "completed"
                    self._save_report(report)

                    if show_progress:
                        print(f"✓ Successfully generated report for {commit_data['sha'][:8]}")
                    
                    return report

                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
            
            # If we get here, all retries failed
            report.status = "failed"
            report.error = str(last_error)
            self._save_report(report)
            
            if show_progress:
                print(f"✗ Failed to generate report for {commit_data['sha'][:8]}: {str(last_error)}")
            
            raise last_error
            
        except Exception as e:
            if show_progress:
                print(f"✗ Error processing {commit_data['sha'][:8]}: {str(e)}")
            raise e
        
    async def generate_batch_reports(self, commits_data: List[Dict], diff_contents: Dict[str, str]) -> int:
        """Generate reports for multiple commits with progress tracking"""
        total = len(commits_data)
        completed = 0
        
        print(f"\nStarting batch report generation for {total} commits")
        print("Repository:", commits_data[0].get('repository') if commits_data else "Unknown")
        print("Date:", commits_data[0].get('date', '').split('T')[0] if commits_data else "Unknown")
        print("-" * 80)
        
        with tqdm(total=total, desc="Generating reports", dynamic_ncols=True) as pbar:
            for commit_data in commits_data:
                try:
                    sha = commit_data["sha"]
                    message = commit_data.get("message", "No message")[:50]
                    print(f"\nProcessing: [{sha[:8]}] {message}...")

                    # Make sure there is a repository field
                    if "repository" not in commit_data:
                        if "repository" in commits_data[0]:
                            commit_data["repository"] = commits_data[0]["repository"]
                        else:
                            raise ValueError("Repository information missing")

                    diff_content = diff_contents.get(sha)
                    if not diff_content:
                        print(f"⚠ No diff content found for {sha[:8]}")
                        continue
                    
                    report = await self.generate_report(commit_data, diff_content, show_progress=True)
                    if report and report.status == "completed":
                        completed += 1
                        print(f"✓ Report generated: {sha[:8]} - {message[:30]}...")
                    
                except Exception as e:
                    print(f"✗ Error processing {commit_data.get('sha', 'unknown')[:8]}: {str(e)}")
                    continue
                finally:
                    pbar.update(1)
                    pbar.set_postfix({"Success": f"{completed}/{total}"})
        
        print("\nBatch Generation Summary:")
        print(f"Total Commits: {total}")
        print(f"Successfully Generated: {completed}")
        print(f"Failed: {total - completed}")
        print("-" * 80)
                        
        return completed
    
    def _save_report(self, report: CommitReport):
        """Save report to filesystem"""
        try:
            repo_dir = Config.REPORTS_BASE_DIR / report.repository.replace('/', '_')
            date_str = datetime.fromisoformat(report.date).strftime('%Y-%m-%d')
            date_dir = repo_dir / date_str
            
            # Create necessary directories
            date_dir.mkdir(parents=True, exist_ok=True)

            # Save report content and metadata
            md_file = date_dir / f"{report.commit_sha}.md"
            meta_file = date_dir / f"{report.commit_sha}.json"
            
            md_file.write_text(report.content, encoding='utf-8')
            meta_file.write_text(
                json.dumps(report.dict(), indent=2, default=str),
                encoding='utf-8'
            )
            
            print(f"Saved report for commit {report.commit_sha} to {meta_file}")
            
        except Exception as e:
            print(f"Error saving report: {str(e)}")
            raise

    def get_report(self, repository: str, commit_sha: str) -> Optional[CommitReport]:
        """Retrieve a report from filesystem"""
        repo_dir = self.reports_dir / repository.replace('/', '_')
        if not repo_dir.exists():
            return None

        # Search in all date directories
        for date_dir in repo_dir.glob("*"):
            if not date_dir.is_dir():
                continue

            meta_file = date_dir / f"{commit_sha}.json"
            if meta_file.exists():
                meta_data = json.loads(meta_file.read_text(encoding='utf-8'))
                return CommitReport(**meta_data)

        return None

    def get_reports_by_date(self, repository: str, date: str) -> List[CommitReport]:
        """Get all reports for a specific date"""
        repo_dir = self.reports_dir / repository.replace('/', '_')
        date_dir = repo_dir / date
        
        if not date_dir.exists():
            return []

        reports = []
        for meta_file in date_dir.glob("*.json"):
            meta_data = json.loads(meta_file.read_text(encoding='utf-8'))
            reports.append(CommitReport(**meta_data))

        return sorted(reports, key=lambda r: r.created_at, reverse=True)