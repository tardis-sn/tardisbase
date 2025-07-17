import pandas as pd
from pathlib import Path
from git import Repo
from IPython.display import display

class FileChangeMatrixVisualizer:
    """
    Visualizes file changes across commits in a matrix format.
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
        self.tardis_commits = tardis_commits
        self.tardis_repo_path = Path(tardis_repo_path) if tardis_repo_path else None

        self.repo = Repo(self.regression_repo_path)
        self.tardis_repo = None
        if self.tardis_repo_path and self.tardis_repo_path.exists():
            try:
                self.tardis_repo = Repo(self.tardis_repo_path)
            except:
                print(f"Warning: Could not access TARDIS repository at {self.tardis_repo_path}")

        self.file_transitions = {}
        self.all_files = set()
        self.transition_columns = []


    def print_commit_info(self):
        """Print commit information table before the analysis."""
        commit_data = []

        commit_type = ("Generated Commits from TARDIS" if self.tardis_commits
                      else "Direct Regression Data Commits")

        for i, commit_hash in enumerate(self.commits):
            commit = self.repo.commit(commit_hash)
            description = f"Regression data for --{commit.message.strip().split('\n')[0][:60]}"

            commit_data.append({
                'Commit #': i + 1,
                'Regression Hash': commit_hash[:8],
                'Description': description,
                'Date': commit.committed_datetime.strftime('%Y-%m-%d %H:%M')
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

        self.transition_columns = [f"{self.commits[i][:6]}-{self.commits[i-1][:6]}"
                                  for i in range(1, len(self.commits))]

        for i in range(1, len(self.commits)):
            older_commit = self.commits[i-1]
            newer_commit = self.commits[i]
            transition_key = f"{newer_commit[:6]}-{older_commit[:6]}"

            print(f"Processing transition {i}/{len(self.commits)-1}: {transition_key}")

            changes = self._get_changes_with_git(older_commit, newer_commit)
            self.file_transitions[transition_key] = changes
            self.all_files.update(changes.keys())

        print(f"Found {len(self.all_files)} total files across all transitions.")
        print(f"All .h5 files found: {sorted([f for f in self.all_files if f.endswith(('.h5', '.hdf5'))])}")


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
        """Print file change analysis as clean DataFrames."""
        if not self.file_transitions:
            print("No analysis done. Run analyze_commits() first.")
            return

        self.print_commit_info()
        self._print_dataframe_matrix()

    def _create_file_data_row(self, file_path):
        row = {'Files': file_path}
        for transition_key in self.transition_columns:
            change_type = self.file_transitions.get(transition_key, {}).get(file_path, "−")
            row[transition_key] = change_type
        return row

    def _print_dataframe_matrix(self):
        all_data = [self._create_file_data_row(file_path)
                   for file_path in sorted(self.all_files)]

        if all_data:
            df = pd.DataFrame(all_data)
            print(f"\nFile Changes Matrix ({len(self.all_files)} files):")
            print("=" * 60)
            display(df)
        else:
            print("\nNo files found across the analyzed transitions.")
