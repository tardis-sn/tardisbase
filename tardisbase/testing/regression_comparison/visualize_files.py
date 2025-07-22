import pandas as pd
from pathlib import Path
from git import Repo

class MultiCommitCompare:
    """
    Visualizes file changes across commits in a matrix format.

    This class analyzes changes to HDF5 files across multiple Git commits
    and displays the results in a tabular matrix format showing file
    transitions (added, deleted, modified, unchanged) between commits.

    Parameters
    ----------
    regression_repo_path : str or Path
        Path to the regression data repository.
    commits : list of str
        List of regression data commit hashes to analyze.
    tardis_commits : list of str, optional
        List of corresponding TARDIS commits (for case 2).
    tardis_repo_path : str or Path, optional
        Path to TARDIS repository (for getting TARDIS commit messages).
    file_extensions : tuple of str, optional
        File extensions to filter by (e.g., ('.h5', '.hdf5')).
        If None, analyzes all files.
    """

    def __init__(self, regression_repo_path, commits, tardis_commits=None, tardis_repo_path=None, file_extensions=None):
        self.regression_repo_path = Path(regression_repo_path)
        self.commits = commits
        self.tardis_commits = tardis_commits
        self.tardis_repo_path = Path(tardis_repo_path) if tardis_repo_path else None
        self.file_extensions = file_extensions

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


    def get_files_in_commit(self, commit_hash, file_extensions=None):
        """
        Extract files from a Git commit, optionally filtered by extensions.

        Parameters
        ----------
        commit_hash : str
            Git commit hash to analyze.
        file_extensions : tuple of str, optional
            File extensions to filter by (e.g., ('.h5', '.hdf5')).
            If None, returns all files.

        Returns
        -------
        set of str
            Set of file paths in the commit.
        """
        files = set()

        tree_output = self.repo.git.execute(['git', 'ls-tree', '-r', '--name-only', commit_hash])
        for filepath in tree_output.split('\n'):
            filepath = filepath.strip()
            if filepath:
                if file_extensions is None or filepath.endswith(file_extensions):
                    files.add(filepath)

        return files


    def is_file_modified(self, file_path, older_commit, newer_commit):
        """
        Check if a file was modified between two commits.

        Parameters
        ----------
        file_path : str
            Path to the file to check.
        older_commit : str
            Older commit hash.
        newer_commit : str
            Newer commit hash.

        Returns
        -------
        bool
            True if file was modified, False otherwise.
        """
        diff_output = self.repo.git.diff(f'{older_commit}..{newer_commit}', '--', file_path)
        return bool(diff_output.strip())


    def get_changes_with_git(self, older_commit, newer_commit):
        """
        Analyze file changes between two commits.

        Parameters
        ----------
        older_commit : str
            Older commit hash.
        newer_commit : str
            Newer commit hash.

        Returns
        -------
        dict of str : str
            File paths mapped to change symbols (A/D/M/•/−).
        """
        older_files = self.get_files_in_commit(older_commit, self.file_extensions)
        newer_files = self.get_files_in_commit(newer_commit, self.file_extensions)
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
            elif self.is_file_modified(file_path, older_commit, newer_commit):
                changes[file_path] = "M"
            else:
                changes[file_path] = "•"

        return changes


    def create_file_data_row(self, file_path):
        """
        Create a data row for the file change matrix.

        Parameters
        ----------
        file_path : str
            File path for the row.

        Returns
        -------
        dict of str : str
            Row data with file path and change symbols.
        """
        row = {'Files': file_path}
        for transition_key in self.transition_columns:
            change_type = self.file_transitions.get(transition_key, {}).get(file_path, "−")
            row[transition_key] = change_type
        return row


    def get_dataframe_matrix(self):
        """
        Get the file change matrix as a DataFrame.

        Returns
        -------
        tuple of (pandas.Series, pandas.DataFrame) or (None, None)
            Legend series and matrix DataFrame, or None if no files found.
        """
        all_data = [self.create_file_data_row(file_path)
                   for file_path in sorted(self.all_files)]

        if all_data:
            df = pd.DataFrame(all_data)

            # Create legend as pandas Series
            legend_data = {
                'A': 'Added',
                'D': 'Deleted',
                'M': 'Modified',
                '•': 'Unchanged',
                '−': 'Not-Present'
            }
            legend_series = pd.Series(legend_data, name='Legend')

            return legend_series, df
        else:
            return None, None


    def get_commit_info(self):
        """
        Get commit information table.

        Returns
        -------
        pandas.DataFrame
            DataFrame containing commit information.
        """
        commit_data = []

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
        return df

    def get_commit_type(self):
        """
        Get the commit type description.

        Returns
        -------
        str
            Description of commit type.
        """
        return ("Generated Commits from TARDIS" if self.tardis_commits
                else "Direct Regression Data Commits")


    def analyze_commits(self):
        """
        Analyze file changes across all commits.

        Notes
        -----
        Requires at least 2 commits. Populates transition_columns,
        file_transitions, and all_files attributes.
        """
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

            changes = self.get_changes_with_git(older_commit, newer_commit)
            self.file_transitions[transition_key] = changes
            self.all_files.update(changes.keys())

        print(f"Found {len(self.all_files)} total files across all transitions.")


    def get_analysis_results(self):
        """
        Get complete file change analysis results.

        Returns
        -------
        tuple of (pandas.DataFrame, pandas.Series, pandas.DataFrame) or None
            Commit info DataFrame, legend Series, and matrix DataFrame.
            Returns None if no analysis has been done.

        Notes
        -----
        Must be called after analyze_commits().
        """
        if not self.file_transitions:
            return None

        commit_info = self.get_commit_info()
        legend, matrix = self.get_dataframe_matrix()
        return commit_info, legend, matrix
