import subprocess
from pathlib import Path
import logging
from tardisbase.testing.regression_comparison import CONFIG

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
        'red', 'green', 'yellow', 'blue'. If an unsupported color
        is provided, the text will be printed without color formatting.

    Notes
    -----
    The function uses ANSI escape codes for coloring:
    - Red: \\033[91m
    - Green: \\033[92m
    - Yellow: \\033[93m
    - Blue: \\033[94m
    - Reset: \\033[0m
    """
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "reset": "\033[0m",
    }
    print(f"{colors.get(color, '')}{text}{colors['reset']}")


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


def get_last_two_commits(repo_path=None):
    """
    Retrieve the last two commit hashes from a git repository.

    This function queries a git repository to get the two most recent commit
    hashes, which is useful for regression testing between consecutive commits
    or comparing the current state with the previous commit.

    Parameters
    ----------
    repo_path : str or Path, optional
        Path to the git repository to query, by default None.
        If None, uses the path specified in CONFIG['regression_data_repo'].
        The path should point to a valid git repository root or any directory
        within a git repository.

    Returns
    -------
    tuple of (str, str) or (None, None)
        A tuple containing (older_commit, newer_commit) where:
        - older_commit : The second-to-last commit hash (parent commit)
        - newer_commit : The most recent commit hash (HEAD)

        Returns (None, None) if:
        - The repository doesn't exist at the specified path
        - Git command execution fails
        - The repository has fewer than 2 commits
        - Any subprocess or git-related error occurs

    Notes
    -----
    The function uses 'git log --format=%H -n 2' to retrieve commit hashes.
    This command returns the full SHA-1 hashes of the commits in reverse
    chronological order (newest first).

    Error handling includes:
    - Repository existence checking
    - Subprocess error catching
    - Git command failure handling
    - Logging of errors for debugging purposes

    The function is designed to fail, returning (None, None)
    instead of raising exceptions, making it suitable for use in automated
    testing workflows where missing repositories or git errors should not
    halt execution.
    """
    if repo_path is None:
        repo_path = CONFIG["regression_data_repo"]

    try:
        if not Path(repo_path).exists():
            logger.error(f"Regression data repository not found at {repo_path}")
            return None, None

        result = subprocess.run(
            ["git", "-C", str(repo_path), "log", "--format=%H", "-n", "2"],
            capture_output=True,
            text=True,
            check=True,
        )

        commits = result.stdout.strip().split("\n")
        if len(commits) >= 2:
            return commits[1], commits[0]

        return None, None

    except (subprocess.SubprocessError, subprocess.CalledProcessError):
        logger.error("Unable to get git commits.")
        return None, None
