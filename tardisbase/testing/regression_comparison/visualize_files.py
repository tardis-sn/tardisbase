import pandas as pd
from pathlib import Path
from git import Repo
from IPython.display import display
from tardisbase.testing.regression_comparison.config import (
    FILE_CHANGE_SYMBOLS, SYMBOL_COLORS, SYMBOL_DESCRIPTIONS
)
from tardisbase.testing.regression_comparison.git_utils import get_commit_info

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

        self.file_transitions = {}  # {transition_key: {file_path: change_type}} e.g., {"4cc3a0-cb0155": {file: "+"}}
        self.file_details = {}  # {transition_key: {file_path: change_details}}
        self.all_files = set()  # All files that appear across all transitions
        self.changed_files = set()  # Files that changed in any transition
        self.unchanged_files = set()  # Files that never changed
        self.transition_columns = []  # List of transition column names (newer-older format)

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
        if len(self.commits) < 2:
            print("Need at least 2 commits to analyze transitions.")
            return

        print(f"Analyzing {len(self.commits)} commits ({len(self.commits)-1} transitions)...")

        # Generate transition columns (newer-older format)
        self.transition_columns = [f"{self.commits[i][:6]}-{self.commits[i-1][:6]}"
                                  for i in range(1, len(self.commits))]

        for i in range(1, len(self.commits)):
            older_commit = self.commits[i-1]
            newer_commit = self.commits[i]
            transition_key = f"{newer_commit[:6]}-{older_commit[:6]}"

            print(f"Processing transition {i}/{len(self.commits)-1}: {transition_key}")

            # Use GitPython for change detection
            changes = self._get_changes_with_git(older_commit, newer_commit)

            # Store changes with transition key
            self.file_transitions[transition_key] = changes
            self.all_files.update(changes.keys())

            # Store file details for this transition
            if transition_key not in self.file_details:
                self.file_details[transition_key] = {}

            for file_path, change_type in changes.items():
                self.file_details[transition_key][file_path] = SYMBOL_DESCRIPTIONS.get(
                    change_type, "Unknown change"
                )

        # Separate changed and unchanged files using transition data
        self.all_files, self.changed_files, self.unchanged_files = self._categorize_files_from_transitions()

        print(f"Found {len(self.all_files)} total files across all transitions.")
        print(f"Changed files: {len(self.changed_files)}")
        print(f"Unchanged files: {len(self.unchanged_files)}")
        print(f"All .h5 files found: {sorted([f for f in self.all_files if f.endswith(('.h5', '.hdf5'))])}")


    def _categorize_files_from_transitions(self):
        all_files = set()
        changed_files = set()

        # Collect all files
        for changes in self.file_transitions.values():
            all_files.update(changes.keys())

        unchanged_files = set()
        return all_files, changed_files, unchanged_files

    def _get_changes_with_git(self, older_commit, newer_commit):
        older_files = self._get_h5_files_in_commit(older_commit)
        newer_files = self._get_h5_files_in_commit(newer_commit)
        all_files = older_files | newer_files

        changes = {}
        for file_path in all_files:
            in_older = file_path in older_files
            in_newer = file_path in newer_files

            if not in_older and not in_newer:
                changes[file_path] = "−"
            elif not in_older and in_newer:
                changes[file_path] = "A"
            elif in_older and not in_newer:
                changes[file_path] = "D"
            elif self._is_file_modified(file_path, older_commit, newer_commit):
                changes[file_path] = "M"
            else:
                changes[file_path] = "•"

        return changes

    def _get_h5_files_in_commit(self, commit_hash):
        files = set()
        try:
            tree_output = self.repo.git.execute(['git', 'ls-tree', '-r', '--name-only', commit_hash])
            for filepath in tree_output.split('\n'):
                filepath = filepath.strip()
                if filepath and filepath.endswith(('.h5', '.hdf5')):
                    files.add(filepath)
        except Exception as e:
            print(f"Warning: Could not list files in commit {commit_hash[:8]}: {e}")
        return files

    def _is_file_modified(self, file_path, older_commit, newer_commit):
        try:
            diff_output = self.repo.git.diff(f'{older_commit}..{newer_commit}', '--', file_path)
            return bool(diff_output.strip())
        except Exception:
            return False

    def print_matrix(self):
        """Print file change analysis as clean DataFrames with better visual distinction."""
        if not self.file_transitions:
            print("No analysis done. Run analyze_commits() first.")
            return

        # Show commit information first
        self.print_commit_info()

        # Use transition columns instead of individual commits
        self._print_dataframe_matrix()

    def _create_file_data_row(self, file_path):
        row = {'Files': file_path}
        for transition_key in self.transition_columns:
            change_type = self.file_transitions.get(transition_key, {}).get(file_path, "−")
            row[transition_key] = change_type
        return row

    def _display_styled_dataframe(self, df):
        display(df)

    def _print_dataframe_matrix(self):
        # All Files
        all_data = [self._create_file_data_row(file_path)
                   for file_path in sorted(self.all_files)]

        if all_data:
            df = pd.DataFrame(all_data)
            print(f"\nFile Changes Matrix ({len(self.all_files)} files):")
            print("=" * 60)
            self._display_styled_dataframe(df)
        else:
            print("\nNo files found across the analyzed transitions.")

    def _print_legend(self):
        """Print the legend for file change symbols."""
        print(f"\nLegend:")
        print("─" * 30)
        for symbol, color in self.symbol_colors.items():
            description = self.legend_descriptions.get(symbol, "unknown")
            print(f"  {symbol} = {description} ({color})")