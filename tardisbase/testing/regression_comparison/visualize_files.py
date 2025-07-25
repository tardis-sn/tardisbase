import pandas as pd
from pathlib import Path
from git import Repo
import subprocess
import tempfile
import shutil
from tardisbase.testing.regression_comparison import CONFIG

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
    compare_function : str, optional
        Comparison method to use. Options: 'git_diff', 'cmd_diff'.
        Default is 'git_diff'.
    diff_command : str, optional
        Command-line diff tool to use when compare_function='cmd_diff'.
        Default is 'diff'.
    """

    def __init__(self, regression_repo_path, commits, tardis_commits=None, tardis_repo_path=None, file_extensions=None, compare_function="git_diff", diff_command="diff"):
        self.regression_repo_path = Path(regression_repo_path)
        self.commits = commits
        self.tardis_commits = tardis_commits
        self.tardis_repo_path = Path(tardis_repo_path) if tardis_repo_path else None
        self.file_extensions = file_extensions
        self.compare_function = compare_function
        self.diff_command = diff_command

        # Validate compare_function
        available_functions = ["git_diff", "cmd_diff"]
        if self.compare_function not in available_functions:
            raise ValueError(f"Invalid compare_function '{self.compare_function}'. Available options: {available_functions}")

        self.repo = Repo(self.regression_repo_path)
        self.tardis_repo = None
        if self.tardis_repo_path and self.tardis_repo_path.exists():
            self.tardis_repo = Repo(self.tardis_repo_path)

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


    def extract_file_from_commit(self, commit_hash, file_path, temp_dir, suffix):
        """
        Extract a single file from a git commit to temporary location.

        Parameters
        ----------
        commit_hash : str
            Git commit hash to extract file from.
        file_path : str
            Path to the file within the commit.
        temp_dir : str or Path
            Temporary directory to extract file to.
        suffix : str
            Suffix to add to the extracted filename.

        Returns
        -------
        str
            Path to the extracted file.
        """
        output_path = Path(temp_dir) / f"{Path(file_path).name}_{suffix}"

        # Use git show to extract file content
        file_content = self.repo.git.show(f"{commit_hash}:{file_path}")
        # Write as binary to handle both text and binary files properly
        with open(output_path, 'wb') as f:
            if isinstance(file_content, str):
                f.write(file_content.encode('utf-8'))
            else:
                f.write(file_content)

        return str(output_path)


    def cmd_diff_compare(self, file_path, older_commit, newer_commit):
        """
        Compare files using command-line diff tool.

        Parameters
        ----------
        file_path : str
            Path to the file to compare.
        older_commit : str
            Older commit hash.
        newer_commit : str
            Newer commit hash.

        Returns
        -------
        bool
            True if files differ, False if identical.

        """
        temp_dir = tempfile.mkdtemp(prefix=CONFIG.get("temp_dir_prefix", "file_compare_"))
        try:
            older_file = self.extract_file_from_commit(older_commit, file_path, temp_dir, "older")
            newer_file = self.extract_file_from_commit(newer_commit, file_path, temp_dir, "newer")

            # Run command-line diff
            result = subprocess.run([self.diff_command, older_file, newer_file],
                                    capture_output=True, text=True)
            return result.returncode != 0  # Non-zero means files differ
        finally:
            shutil.rmtree(temp_dir)


    def is_file_modified(self, file_path, older_commit, newer_commit):
        """
        Check if a file was modified between two commits.

        Uses the configured comparison function (git_diff or cmd_diff) to determine
        if the file content differs between the two commits.

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

        Raises
        ------
        ValueError
            If an invalid comparison function is configured.
        FileNotFoundError
            If cmd_diff is used but the diff command is not available.
        subprocess.CalledProcessError
            If file extraction fails when using cmd_diff.
        """
        if self.compare_function == "git_diff":
            diff_output = self.repo.git.diff(f'{older_commit}..{newer_commit}', '--', file_path)
            return bool(diff_output.strip())
        elif self.compare_function == "cmd_diff":
            return self.cmd_diff_compare(file_path, older_commit, newer_commit)
        else:
            # This should not happen due to validation in __init__, but just in case
            available_functions = ["git_diff", "cmd_diff"]
            raise ValueError(f"Invalid compare_function '{self.compare_function}'. Available options: {available_functions}")


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

            # Use TARDIS commit message if available, otherwise use regression commit message
            if self.tardis_commits and i < len(self.tardis_commits) and self.tardis_repo:
                tardis_commit = self.tardis_repo.commit(self.tardis_commits[i])
                description = f"Regression data for --{tardis_commit.message.strip().split('\n')[0][:60]}"
            else:
                description = f"{commit.message.strip().split('\n')[0][:60]}"

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
