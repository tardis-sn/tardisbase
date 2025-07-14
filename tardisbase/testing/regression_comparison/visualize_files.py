import pandas as pd
from pathlib import Path
from git import Repo
import subprocess
from IPython.display import display

class FileChangeMatrixVisualizer:
    """
    Visualizes file changes across commits in a matrix format.

    Automatically detects which files changed across the analyzed commits and shows:
    - Changed files matrix: Shows which files were added (+), deleted (-), modified (*), or unchanged (•)
    - Unchanged files table: Shows files that remained unchanged across all commits
    """

    def __init__(self, regression_repo_path, commits, tardis_commits=None, tardis_repo_path=None):
        """
        Initialize the visualizer.

        Args:
            regression_repo_path: Path to regression data repository
            commits: List of regression data commit hashes to analyze
            tardis_commits: Optional list of corresponding TARDIS commits (for case 2)
            tardis_repo_path: Optional path to TARDIS repository (for getting TARDIS commit messages)
        """
        self.regression_repo_path = Path(regression_repo_path)
        self.commits = commits
        self.tardis_commits = tardis_commits  # For case 2: TARDIS commits that generated the regression data
        self.tardis_repo_path = Path(tardis_repo_path) if tardis_repo_path else None

        self.repo = Repo(self.regression_repo_path)
        self.tardis_repo = None
        if self.tardis_repo_path and self.tardis_repo_path.exists():
            try:
                self.tardis_repo = Repo(self.tardis_repo_path)
            except:
                print(f"Warning: Could not access TARDIS repository at {self.tardis_repo_path}")

        self.file_changes = {}  # {commit: {file_path: change_type}}
        self.file_details = {}  # {commit: {file_path: change_details}}
        self.all_files = set()  # All files that appear across all commits
        self.changed_files = set()  # Files that changed in any commit
        self.unchanged_files = set()  # Files that never changed

    def _get_commit_info(self, commit_hash, repo=None):
        """Get commit information (message, author, date)."""
        if repo is None:
            repo = self.repo

        try:
            commit = repo.commit(commit_hash)
            return {
                'hash': commit_hash[:8],
                'message': commit.message.strip().split('\n')[0][:60],  # First line, max 60 chars
                'author': commit.author.name,
                'date': commit.committed_datetime.strftime('%Y-%m-%d %H:%M')
            }
        except:
            return {
                'hash': commit_hash[:8],
                'message': 'Unable to fetch commit info',
                'author': 'Unknown',
                'date': 'Unknown'
            }

    def _get_tardis_commit_info(self, tardis_commit_hash):
        """Get TARDIS commit information."""
        if self.tardis_repo:
            return self._get_commit_info(tardis_commit_hash, self.tardis_repo)
        else:
            return {
                'hash': tardis_commit_hash[:8],
                'message': f'TARDIS commit {tardis_commit_hash[:8]}',
                'author': 'Unknown',
                'date': 'Unknown'
            }

    def print_commit_info(self):
        """Print commit information table before the analysis."""
        commit_data = []

        # Determine the type for the heading
        if self.tardis_commits:
            commit_type = "Generated Commits from TARDIS"
        else:
            commit_type = "Direct Regression Data Commits"

        for i, commit_hash in enumerate(self.commits):
            info = self._get_commit_info(commit_hash)

            if self.tardis_commits and i < len(self.tardis_commits):
                # Case 2: TARDIS commits provided - get TARDIS commit message
                tardis_commit_hash = self.tardis_commits[i]
                tardis_info = self._get_tardis_commit_info(tardis_commit_hash)
                commit_data.append({
                    'Commit #': i + 1,
                    'Regression Hash': info['hash'],
                    'Description': f"Regression data for {tardis_info['message']}",
                    'Date': info['date']
                })
            else:
                # Case 1: Direct regression data commits
                commit_data.append({
                    'Commit #': i + 1,
                    'Regression Hash': info['hash'],
                    'Description': f"Regression data for {info['message']}",
                    'Date': info['date']
                })

        df = pd.DataFrame(commit_data)

        print(f"\nCOMMIT INFORMATION ({len(self.commits)} commits) - {commit_type}:")
        print("=" * 80)

        display(df)

    def analyze_commits(self):
        """Analyze file changes across commits and separate changed vs unchanged files."""
        print(f"Analyzing {len(self.commits)} commits...")

        original_head = self.repo.head.commit.hexsha

        try:
            for i, commit_hash in enumerate(self.commits):
                print(f"Processing commit {i+1}/{len(self.commits)}: {commit_hash[:8]}")

                if i == 0:
                    # First commit - all files are "unchanged"
                    self.repo.git.checkout(commit_hash)
                    current_files = self._get_all_h5_files()
                    self.file_changes[commit_hash] = {f: '•' for f in current_files}
                    self.all_files.update(current_files)
                else:
                    # Compare with previous commit
                    changes = self._compare_commits(self.commits[i-1], commit_hash)
                    self.file_changes[commit_hash] = changes
                    self.all_files.update(changes.keys())

        finally:
            self.repo.git.checkout(original_head)

        # Separate changed and unchanged files
        self._categorize_files()

        print(f"Found {len(self.all_files)} total files across all commits.")
        print(f"Changed files: {len(self.changed_files)}")
        print(f"Unchanged files: {len(self.unchanged_files)}")

    def _get_all_h5_files(self):
        """Get all .h5 files in current commit."""
        files = set()
        for file_path in self.regression_repo_path.rglob("*.h5"):
            rel_path = file_path.relative_to(self.regression_repo_path)
            files.add(str(rel_path))
        return files

    def _categorize_files(self):
        """Separate files into changed and unchanged categories."""
        # Find files that changed in any commit
        for changes in self.file_changes.values():
            for file_path, change_type in changes.items():
                if change_type in ['+', '-', '*']:  # Added, deleted, or modified
                    self.changed_files.add(file_path)

        # Remaining files are unchanged
        self.unchanged_files = self.all_files - self.changed_files

    def _compare_commits(self, prev_commit_hash, current_commit_hash):
        """Compare two commits to find file changes."""
        # Get files in both commits
        self.repo.git.checkout(prev_commit_hash)
        prev_files = self._get_all_h5_files()

        self.repo.git.checkout(current_commit_hash)
        current_files = self._get_all_h5_files()

        changes = {}
        all_files = prev_files | current_files

        # Initialize details for this commit if not exists
        if current_commit_hash not in self.file_details:
            self.file_details[current_commit_hash] = {}

        for file_path in all_files:
            if file_path not in prev_files:
                changes[file_path] = '+'  # Added
                self.file_details[current_commit_hash][file_path] = "File added"
            elif file_path not in current_files:
                changes[file_path] = '-'  # Deleted
                self.file_details[current_commit_hash][file_path] = "File deleted"
            elif self._is_file_modified(file_path, prev_commit_hash, current_commit_hash):
                changes[file_path] = '*'  # Modified
                self.file_details[current_commit_hash][file_path] = self._get_file_change_details(file_path, prev_commit_hash, current_commit_hash)
            else:
                changes[file_path] = '•'  # Unchanged
                self.file_details[current_commit_hash][file_path] = "No changes"

        return changes

    def _is_file_modified(self, file_path, prev_commit, current_commit):
        """Check if file was modified between commits using git diff."""
        try:
            result = subprocess.run([
                'git', 'diff', '--quiet',
                f'{prev_commit}..{current_commit}',
                '--', file_path
            ], cwd=self.regression_repo_path, capture_output=True)
            return result.returncode != 0  # 0 = no diff, 1 = has diff
        except:
            return True  # Assume modified if git diff fails

    def _get_file_change_details(self, file_path, prev_commit, current_commit):
        """Get detailed information about what changed in a file."""
        try:
            # Get git diff stats
            result = subprocess.run([
                'git', 'diff', '--stat',
                f'{prev_commit}..{current_commit}',
                '--', file_path
            ], cwd=self.regression_repo_path, capture_output=True, text=True)

            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            else:
                return "File changed (no diff details available)"
        except:
            return "File changed (error getting details)"

    def print_matrix(self):
        """Print file change analysis as clean DataFrames with better visual distinction."""
        if not self.file_changes:
            print("No analysis done. Run analyze_commits() first.")
            return

        # Show commit information first
        self.print_commit_info()

        short_commits = [commit[:6] for commit in self.commits]
        symbols = {'•': '•', '+': '+', '-': '-', '*': '*', '∅': '∅'}
        symbol_colors = {'•': 'blue', '+': 'green', '-': 'red', '*': 'orange', '∅': 'grey'}

        self._print_dataframe_matrix(short_commits, symbols, symbol_colors)

    def _print_dataframe_matrix(self, short_commits, symbols, _):
        """Print using pandas DataFrames with colored symbols."""

        def style_symbol(val):
            """Apply color and bold styling to symbols."""
            color_map = {'•': 'blue', '*': 'gold', '+': 'green', '-': 'red', '∅': 'grey'}
            if val in color_map:
                return f'color: {color_map[val]}; font-weight: bold; font-size: 24px;'
            return ''

        # Display dataframes with styling
        # Changed Files
        if self.changed_files:
                changed_data = []
                for file_path in sorted(self.changed_files):
                    row = {'Files': file_path}
                    for commit in self.commits:
                        commit_short = commit[:6]
                        if commit in self.file_changes and file_path in self.file_changes[commit]:
                            # File has a recorded change for this commit
                            symbol = self.file_changes[commit][file_path]
                            row[commit_short] = symbols.get(symbol, symbol)
                        else:
                            # File doesn't exist in this commit
                            row[commit_short] = symbols['∅']
                    changed_data.append(row)

                changed_df = pd.DataFrame(changed_data)
                print(f"\nChanged Files Matrix ({len(self.changed_files)} files):")
                print("=" * 60)

                # Apply styling to symbol columns only
                short_commits = [commit[:6] for commit in self.commits]
                try:
                    styled_df = changed_df.style.map(style_symbol, subset=short_commits)
                    display(styled_df)
                except AttributeError:
                    styled_df = changed_df.style.applymap(style_symbol, subset=short_commits)
                    display(styled_df)
        else:
            print("\nNo files changed across the analyzed commits.")

        # Unchanged Files
        if self.unchanged_files:
                unchanged_data = [
                    {'Files': file_path, **{commit[:6]: symbols['•'] for commit in self.commits}}
                    for file_path in sorted(self.unchanged_files)
                ]

                unchanged_df = pd.DataFrame(unchanged_data)
                print(f"\nUnchanged Files Table ({len(self.unchanged_files)} files):")
                print("=" * 60)

                # Apply styling to symbol columns only
                try:
                    styled_df = unchanged_df.style.map(style_symbol, subset=short_commits)
                    display(styled_df)
                except AttributeError:
                    styled_df = unchanged_df.style.applymap(style_symbol, subset=short_commits)
                    display(styled_df)
        else:
            print("\nAll files changed across the analyzed commits.")

        # Simple legend with colors
        print(f"\nLegend:")
        print("─" * 30)
        legend_items = [('•', 'blue', 'unchanged'), ('*', 'gold', 'modified'), ('+', 'green', 'added'), ('-', 'red', 'deleted'), ('∅', 'grey', 'not present')]
        for symbol, color, description in legend_items:
            print(f"  {symbol} = {description} ({color})")

    def _print_text_matrix(self, short_commits, symbols):
        """Fallback text-based display."""

        def print_table(files, title):
            if not files:
                return
            print(f"\n{title} ({len(files)} files):")
            print("=" * 80)
            print(f"{'Files':<50}", end="")
            for commit in short_commits:
                print(f"  {commit:>8}", end="")
            print()
            print("─" * (50 + len(short_commits) * 10))

            for file_path in sorted(files):
                display_name = file_path if len(file_path) <= 47 else "..." + file_path[-44:]
                print(f"{display_name:<50}", end="")
                for commit in self.commits:
                    if files == self.unchanged_files:
                        symbol = symbols['•']
                    else:
                        change = self.file_changes.get(commit, {}).get(file_path, '•')
                        symbol = symbols.get(change, change)
                    print(f"  {symbol:>8}", end="")
                print()

        print_table(self.changed_files, "Changed Files Matrix") if self.changed_files else print("\nNo files changed across the analyzed commits.")
        print_table(self.unchanged_files, "Unchanged Files Table") if self.unchanged_files else print("\nAll files changed across the analyzed commits.")

        print(f"\nLegend:")
        print("─" * 30)
        for symbol, description in [('•', 'unchanged'), ('*', 'modified'), ('+', 'added'), ('-', 'deleted'), ('∅', 'not present')]:
            print(f"  {symbol} = {description}")