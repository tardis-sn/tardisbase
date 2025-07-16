from pathlib import Path
import logging
from git import Repo
from tardisbase.testing.regression_comparison import CONFIG
from tardisbase.testing.regression_comparison.config import ANSI_COLORS

logger = logging.getLogger(__name__)


def color_print(text, color):
    """
    Print text to the console with ANSI color formatting.

    This function provides colored console output using ANSI escape codes,
    making it easier to distinguish different types of messages in terminal output.
    The text is automatically reset to default color after printing.

    Parameters
    ----------
    text : str
        The text string to be printed with color formatting.
    color : str
        The color name for the text. Supported colors are:
        'red', 'green', 'yellow', 'blue', 'gold', 'grey'. If an unsupported color
        is provided, the text will be printed without color formatting.

    Notes
    -----
    Uses centralized ANSI color codes from config.py to avoid duplication.
    """
    print(f"{ANSI_COLORS.get(color, '')}{text}{ANSI_COLORS['reset']}")

def get_relative_path(path, base):
    """
    Calculate the relative path from a base directory to a target path.

    This function computes the relative path representation of a target path
    with respect to a base directory, returning the result as a string.

    Parameters
    ----------
    path : str or Path
        The target path for which to calculate the relative path.
        Can be either an absolute or relative path.
    base : str or Path
        The base directory from which to calculate the relative path.
        Should typically be an absolute path for consistent results.

    Returns
    -------
    str
        The relative path from base to path as a string.

    Raises
    ------
    ValueError
        If the path is not relative to the base directory (i.e., they don't
        share a common root or the path is outside the base directory tree).

    Notes
    -----
    This function uses pathlib.Path.relative_to() internally, which requires
    that the target path be within the base directory hierarchy. If the paths
    are on different drives (Windows) or don't share a common ancestor,
    a ValueError will be raised.
    """
    return str(Path(path).relative_to(base))

def get_last_n_commits(n=2, repo_path=None):
    """
    Get the last n commits from a git repository using GitPython.

    Parameters
    ----------
    n : int, optional
        Number of commits to retrieve, by default 2
    repo_path : str or Path, optional
        Path to the repository. If None, uses CONFIG["regression_data_repo"]

    Returns
    -------
    list
        List of commit hashes (strings)

    Raises
    ------
    ValueError
        If repository not found or git operations fail
    """
    if repo_path is None:
        repo_path = CONFIG["regression_data_repo"]

    try:
        if not Path(repo_path).exists():
            raise ValueError(f"Regression data repository not found at {repo_path}")

        repo = Repo(repo_path)
        commits = list(repo.iter_commits(max_count=n))
        return [commit.hexsha for commit in commits]

    except Exception as e:
        raise ValueError(f"Unable to get git commits: {str(e)}")