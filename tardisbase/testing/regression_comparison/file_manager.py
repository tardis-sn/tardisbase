import shutil
import tempfile
from pathlib import Path
import os
from git import Repo
from tardisbase.testing.regression_comparison import CONFIG


class FileManager:
    """
    A class for managing temporary directories and file operations for regression data comparisons.

    This class provides a interface for creating and managing temporary
    directories, handling file copying operations, and maintaining consistent path
    management across the comparison workflow.

    Parameters
    ----------
    repo_path : str or Path, optional
        Path to the repository containing regression data, by default None.
        If None, uses the path specified in CONFIG['compare_path'].
    """

    def __init__(self, repo_path=None):
        self.temp_dir = None
        self.repo_path = Path(repo_path) if repo_path else Path(CONFIG["compare_path"])

    def setup(self):
        """
        Create a temporary directory for file operations.

        This method creates a new temporary directory using the configured prefix
        and stores its path for use in subsequent operations. The directory name
        includes a prefix specified in CONFIG['temp_dir_prefix'].

        Notes
        -----
        The temporary directory path is stored in self.temp_dir and can be
        accessed using get_temp_path() for subdirectory operations. The directory
        should be cleaned up using teardown() when no longer needed.

        Prints the path of the created temporary directory for logging purposes.
        """
        self.temp_dir = Path(tempfile.mkdtemp(prefix=CONFIG["temp_dir_prefix"]))
        print(f"Created temporary directory at {self.temp_dir}")

    def teardown(self):
        """
        Remove the temporary directory and clean up resources.

        This method safely removes the temporary directory and all its contents,
        resetting the temp_dir attribute to None. It includes safety checks to
        ensure the directory exists before attempting removal.

        Notes
        -----
        This method should be called after completing all file operations to
        ensure proper cleanup of temporary resources. It safely handles cases
        where the temporary directory doesn't exist or has already been removed.

        Prints confirmation of directory removal for logging purposes.
        """
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            print(f"Removed temporary directory {self.temp_dir}")
        self.temp_dir = None

    def get_temp_path(self, filename):
        """
        Get the full path to a file or directory within the temporary directory.

        Parameters
        ----------
        filename : str
            Name of the file or subdirectory within the temporary directory.

        Returns
        -------
        str
            Full path to the specified file or directory within temp_dir.

        Notes
        -----
        This method assumes that setup() has been called and temp_dir is available.
        """
        return str(self.temp_dir / filename)

    def copy_file(self, source, destination):
        """
        Copy a file to the temporary directory with metadata preservation.

        This method copies a file from the source location to a destination
        within the temporary directory, preserving file metadata including
        timestamps and permissions.

        Parameters
        ----------
        source : str or Path
            Path to the source file to be copied.
        destination : str
            Relative path for the destination file within the temporary directory.
            The file will be copied to temp_dir/destination.

        Notes
        -----
        Uses shutil.copy2() to preserve file metadata including access and
        modification times. The destination path is automatically resolved
        relative to the temporary directory using get_temp_path().
        """
        shutil.copy2(source, self.get_temp_path(destination))


class FileSetup:
    """
    A class for setting up reference files from git commits for comparison.

    This class handles the extraction and setup of reference data from specific
    git commits or the current repository state, organizing them into separate
    directories for comparison operations.

    Parameters
    ----------
    file_manager : FileManager
        An instance of FileManager that provides temporary directory management.
    ref1_hash : str or None
        Git commit hash for the first reference dataset.
        If None, the current repository state will be used.
    ref2_hash : str or None
        Git commit hash for the second reference dataset.
        If None, the current repository state will be used.
    """

    def __init__(self, file_manager, ref1_hash, ref2_hash):
        self.file_manager = file_manager
        self.ref1_hash = ref1_hash
        self.ref2_hash = ref2_hash
        self.repo_path = file_manager.repo_path

    def setup(self):
        """
        Set up reference directories with data from specified git commits.

        This method creates separate directories (ref1, ref2) within the temporary
        directory and populates them with data from the specified git commits.
        If a commit hash is None, the current repository state is used instead.

        Notes
        -----
        The method creates two reference directories:
        - ref1: Contains data from ref1_hash commit (or current state if None)
        - ref2: Contains data from ref2_hash commit (or current state if None)

        For git commits, uses git checkout and shutil to copy files.
        For current state, copies all files from the repository directory.
        """
        for ref_id, ref_hash in enumerate([self.ref1_hash, self.ref2_hash], 1):
            ref_dir = self.file_manager.get_temp_path(f"ref{ref_id}")
            os.makedirs(ref_dir, exist_ok=True)
            if ref_hash:
                self._copy_data_from_hash(ref_hash, ref_dir)
            else:
                # Copy all files from repository directory using shutil
                for item in Path(self.repo_path).iterdir():
                    if item.is_file():
                        shutil.copy2(item, ref_dir)
                    elif item.is_dir() and not item.name.startswith('.'):
                        shutil.copytree(item, Path(ref_dir) / item.name, dirs_exist_ok=True)

    def _copy_data_from_hash(self, ref_hash, ref_dir):
        """
        Extract and copy data from a specific git commit to a directory.

        This method checks out the specified commit and copies all files
        to the target directory using shutil operations.

        Parameters
        ----------
        ref_hash : str
            Git commit hash to extract data from.
        ref_dir : str or Path
            Target directory where the commit files will be copied.

        Notes
        -----
        Uses git checkout to switch to the specified commit, copies all files
        using shutil, then restores the original HEAD. This approach is simple
        and reliable.
        """
        try:
            repo = Repo(self.repo_path)
            original_head = repo.head.commit
            repo.git.checkout(ref_hash)

            # Copy all files
            for item in Path(self.repo_path).iterdir():
                if item.is_file() and not item.name.startswith('.'):
                    shutil.copy2(item, ref_dir)
                elif item.is_dir() and not item.name.startswith('.'):
                    shutil.copytree(item, Path(ref_dir) / item.name, dirs_exist_ok=True)

            # Restore original head
            repo.git.checkout(original_head)

        except Exception as e:
            print(f"Error extracting files from commit {ref_hash}: {str(e)}")
