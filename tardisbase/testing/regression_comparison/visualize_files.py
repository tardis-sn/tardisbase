import pandas as pd
from pathlib import Path
from git import Repo
from IPython.display import display
from tardisbase.testing.regression_comparison.config import (
    FILE_CHANGE_SYMBOLS, SYMBOL_COLORS, SYMBOL_DESCRIPTIONS,
    style_symbol_function
)
from tardisbase.testing.regression_comparison.git_utils import (
    get_commit_info, safe_checkout, compare_commits_with_dircmp
)
from tardisbase.testing.regression_comparison.file_utils import (
    get_h5_files, categorize_files
)

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

        # Use shared styling configuration from constants
        self.symbols = FILE_CHANGE_SYMBOLS
        self.symbol_colors = SYMBOL_COLORS
        self.legend_descriptions = SYMBOL_DESCRIPTIONS

    def print_commit_info(self):
        """Print commit information table before the analysis."""
        commit_data = []

        # Determine the type for the heading
        commit_type = ("Generated Commits from TARDIS" if self.tardis_commits
                      else "Direct Regression Data Commits")

        # Build commit data directly in the loop
        for i, commit_hash in enumerate(self.commits):
            info = get_commit_info(commit_hash, repo=self.repo)

            if self.tardis_commits:
                # Case 2: TARDIS commits provided - get TARDIS commit message
                tardis_commit_hash = self.tardis_commits[i]
                tardis_info = get_commit_info(tardis_commit_hash, repo=self.tardis_repo)
                description = f"Regression data for {tardis_info['message']}"
            else:
                # Case 1: Direct regression data commits
                description = f"Regression data for {info['message']}"

            commit_data.append({
                'Commit #': i + 1,
                'Regression Hash': info['hash'],
                'Description': description,
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

        for i, commit_hash in enumerate(self.commits):
            print(f"Processing commit {i+1}/{len(self.commits)}: {commit_hash[:8]}")

            if i == 0:
                # First commit - all files are "unchanged"
                safe_checkout(self.repo, commit_hash)
                current_files = get_h5_files(self.regression_repo_path, relative_to=self.regression_repo_path)
                self.file_changes[commit_hash] = {f: '•' for f in current_files}
                self.all_files.update(current_files)
            else:
                # Compare with previous commit using the shared utilities
                changes, _ = compare_commits_with_dircmp(
                    self.commits[i-1],
                    commit_hash,
                    self.regression_repo_path
                )
                self.file_changes[commit_hash] = changes
                self.all_files.update(changes.keys())

                # Store file details for this commit
                if commit_hash not in self.file_details:
                    self.file_details[commit_hash] = {}

                for file_path, change_type in changes.items():
                    self.file_details[commit_hash][file_path] = SYMBOL_DESCRIPTIONS.get(
                        change_type, "Unknown change"
                    )

        self.repo.git.checkout(original_head)

        # Separate changed and unchanged files
        self.all_files, self.changed_files, self.unchanged_files = categorize_files(self.file_changes)

        print(f"Found {len(self.all_files)} total files across all commits.")
        print(f"Changed files: {len(self.changed_files)}")
        print(f"Unchanged files: {len(self.unchanged_files)}")

    def print_matrix(self):
        """Print file change analysis as clean DataFrames with better visual distinction."""
        if not self.file_changes:
            print("No analysis done. Run analyze_commits() first.")
            return

        # Show commit information first
        self.print_commit_info()

        short_commits = [commit[:6] for commit in self.commits]
        self._print_dataframe_matrix(short_commits)

    def _create_file_data_row(self, file_path, file_set):
        """Create a data row for a file in the matrix."""
        row = {'Files': file_path}
        for commit in self.commits:
            commit_short = commit[:6]
            if file_set == self.unchanged_files:
                # For unchanged files, always use the unchanged symbol
                row[commit_short] = self.symbols['unchanged']
            elif commit in self.file_changes and file_path in self.file_changes[commit]:
                # File has a recorded change for this commit
                symbol = self.file_changes[commit][file_path]
                row[commit_short] = self.symbols.get(symbol, symbol)
            else:
                # File doesn't exist in this commit
                row[commit_short] = self.symbols['not_present']
        return row

    def _display_styled_dataframe(self, df, short_commits):
        """Apply styling to a dataframe and display it."""
        styled_df = df.style.map(style_symbol_function, subset=short_commits)
        display(styled_df)

    def _print_dataframe_matrix(self, short_commits):
        """Print using pandas DataFrames with colored symbols."""
        # Changed Files
        if self.changed_files:
            changed_data = [self._create_file_data_row(file_path, self.changed_files)
                           for file_path in sorted(self.changed_files)]

            changed_df = pd.DataFrame(changed_data)
            print(f"\nChanged Files Matrix ({len(self.changed_files)} files):")
            print("=" * 60)
            self._display_styled_dataframe(changed_df, short_commits)
        else:
            print("\nNo files changed across the analyzed commits.")

        # Unchanged Files
        if self.unchanged_files:
            unchanged_data = [self._create_file_data_row(file_path, self.unchanged_files)
                             for file_path in sorted(self.unchanged_files)]

            unchanged_df = pd.DataFrame(unchanged_data)
            print(f"\nUnchanged Files Table ({len(self.unchanged_files)} files):")
            print("=" * 60)
            self._display_styled_dataframe(unchanged_df, short_commits)
        else:
            print("\nAll files changed across the analyzed commits.")

        # Print legend
        self._print_legend()

    def _print_legend(self):
        """Print the legend for file change symbols."""
        print(f"\nLegend:")
        print("─" * 30)
        for symbol, color in self.symbol_colors.items():
            description = self.legend_descriptions.get(symbol, "unknown")
            print(f"  {symbol} = {description} ({color})")