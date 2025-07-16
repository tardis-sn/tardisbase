"""
Shared git utilities for regression comparison modules.

This module provides centralized git operations to reduce code duplication
across the regression comparison package.
"""

import logging
from pathlib import Path
from git import Repo
from tardisbase.testing.regression_comparison.config import ERROR_MESSAGES
from tardisbase.testing.regression_comparison.file_manager import FileManager, FileSetup
from tardisbase.testing.regression_comparison.file_utils import extract_h5_changes_from_dircmp
from filecmp import dircmp
import tempfile
import os

logger = logging.getLogger(__name__)


def get_commit_info(commit_hash, repo_path=None, repo=None):
    """
    Get commit information (message, author, date) with improved error handling.
    
    Parameters
    ----------
    commit_hash : str
        The commit hash to get information for
    repo_path : str or Path, optional
        Path to the repository. Used if repo is None
    repo : git.Repo, optional
        Git repository object. If None, creates one from repo_path
        
    Returns
    -------
    dict
        Dictionary containing commit information
    """
    if repo is None and repo_path is not None:
        repo = Repo(repo_path)
    elif repo is None:
        raise ValueError("Either repo or repo_path must be provided")

    try:
        commit = repo.commit(commit_hash)
        return {
            'hash': commit_hash[:8],
            'message': commit.message.strip().split('\n')[0][:60],  # First line, max 60 chars
            'author': commit.author.name,
            'date': commit.committed_datetime.strftime('%Y-%m-%d %H:%M')
        }
    except Exception as e:
        error_msg = ERROR_MESSAGES["commit_info_failed"].format(commit=commit_hash[:8], error=str(e))
        logger.warning(error_msg)
        return {
            'hash': commit_hash[:8],
            'message': 'Unable to fetch commit info',
            'author': 'Unknown',
            'date': 'Unknown'
        }


def is_file_modified(file_path, prev_commit, current_commit, repo_path):
    """
    Check if file was modified between commits using GitPython with improved error handling.

    Parameters
    ----------
    file_path : str
        Path to the file to check
    prev_commit : str
        Previous commit hash
    current_commit : str
        Current commit hash
    repo_path : str or Path
        Path to the repository

    Returns
    -------
    bool
        True if file was modified, False otherwise
    """
    try:
        repo = Repo(repo_path)
        # Use GitPython's diff functionality instead of subprocess
        diff_output = repo.git.diff(
            f'{prev_commit}..{current_commit}',
            '--', file_path
        )
        return bool(diff_output.strip())  # Empty output means no diff
    except Exception as e:
        error_msg = ERROR_MESSAGES["git_diff_failed"].format(
            file=file_path,
            commit1=prev_commit[:8],
            commit2=current_commit[:8],
            error=str(e)
        )
        logger.warning(error_msg)
        return True  # Assume modified if git diff fails


def get_file_change_details(file_path, prev_commit, current_commit, repo_path):
    """
    Get detailed information about what changed in a file with improved error handling.

    Parameters
    ----------
    file_path : str
        Path to the file
    prev_commit : str
        Previous commit hash
    current_commit : str
        Current commit hash
    repo_path : str or Path
        Path to the repository

    Returns
    -------
    str
        Description of the changes
    """
    try:
        repo = Repo(repo_path)
        # Use GitPython's diff functionality with --stat option
        diff_stats = repo.git.diff(
            '--stat',
            f'{prev_commit}..{current_commit}',
            '--', file_path
        )

        if diff_stats.strip():
            return diff_stats.strip()
        else:
            return "File changed (no diff details available)"
    except Exception as e:
        error_msg = ERROR_MESSAGES["git_diff_failed"].format(
            file=file_path,
            commit1=prev_commit[:8],
            commit2=current_commit[:8],
            error=str(e)
        )
        logger.warning(error_msg)
        return "File changed (error getting details)"


def safe_checkout(repo, commit_hash):
    """
    Safely checkout a commit with error handling.
    
    Parameters
    ----------
    repo : git.Repo
        Git repository object
    commit_hash : str
        Commit hash to checkout
        
    Returns
    -------
    bool
        True if checkout was successful, False otherwise
    """
    try:
        repo.git.checkout(commit_hash)
        return True
    except Exception as e:
        error_msg = ERROR_MESSAGES["git_checkout_failed"].format(commit=commit_hash[:8], error=str(e))
        logger.error(error_msg)
        return False


def extract_commit_files(commit_hash, target_dir, repo_path):
    """
    Extract files from a commit to a target directory using GitPython archive.

    This function reuses the logic from FileSetup._copy_data_from_hash().

    Parameters
    ----------
    commit_hash : str
        Commit hash to extract files from
    target_dir : str or Path
        Target directory to extract files to
    repo_path : str or Path
        Path to the repository

    Returns
    -------
    bool
        True if extraction was successful, False otherwise
    """
    try:
        repo = Repo(repo_path)
        # Use GitPython to create archive and extract with subprocess for piping
        # This is more reliable than shell=True approach
        import subprocess
        import tempfile

        with tempfile.NamedTemporaryFile(suffix='.tar', delete=False) as temp_file:
            # Create archive to temporary file
            repo.git.archive(commit_hash, format='tar', output=temp_file.name)

            # Extract the archive to target directory
            subprocess.run(['tar', '-x', '-f', temp_file.name, '-C', str(target_dir)], check=True)

            # Clean up temporary file
            Path(temp_file.name).unlink()

        return True
    except Exception as e:
        logger.error(f"Failed to extract files from commit {commit_hash[:8]}: {str(e)}")
        return False


def compare_commits_with_dircmp(prev_commit_hash, current_commit_hash, repo_path, file_manager=None):
    """
    Compare two commits using dircmp and return file changes.

    This function centralizes the commit comparison logic used in visualize_files.py.
    It extracts both commits to temporary directories and uses dircmp for comparison.

    Parameters
    ----------
    prev_commit_hash : str
        Previous commit hash
    current_commit_hash : str
        Current commit hash
    repo_path : str or Path
        Path to the repository
    file_manager : FileManager, optional
        File manager instance. If None, creates a temporary one

    Returns
    -------
    dict
        Dictionary mapping file paths to change types
    filecmp.dircmp
        Directory comparison object for further analysis
    """

    # Use provided file manager or create temporary one
    if file_manager is None:
        temp_file_manager = FileManager(repo_path)
        temp_file_manager.setup()
        cleanup_needed = True
    else:
        temp_file_manager = file_manager
        cleanup_needed = False

    try:
        # Create temporary directories for both commits
        prev_dir = Path(temp_file_manager.get_temp_path("prev_commit"))
        current_dir = Path(temp_file_manager.get_temp_path("current_commit"))
        os.makedirs(prev_dir, exist_ok=True)
        os.makedirs(current_dir, exist_ok=True)

        # Use FileSetup to extract commit data
        file_setup = FileSetup(temp_file_manager, prev_commit_hash, current_commit_hash)
        file_setup._copy_data_from_hash(prev_commit_hash, prev_dir)
        file_setup._copy_data_from_hash(current_commit_hash, current_dir)

        # Use dircmp to compare directories
        dcmp = dircmp(str(prev_dir), str(current_dir))

        # Extract changes from dircmp results
        changes = extract_h5_changes_from_dircmp(dcmp)

        return changes, dcmp

    finally:
        if cleanup_needed:
            temp_file_manager.teardown()
