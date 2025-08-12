import subprocess
import tempfile
import os
import logging
from pathlib import Path
import tomllib

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def run_command_with_logging(cmd, success_message="", error_message="Command failed", **kwargs):
    """
    Run subprocess with consistent logging and error handling.
    
    Parameters
    ----------
    cmd : list
        Command to execute
    success_message : str, optional
        Message to log on success
    error_message : str, optional
        Base error message for failures
    **kwargs
        Additional arguments passed to subprocess.run()
        
    Returns
    -------
    tuple
        (success: bool, result: subprocess.CompletedProcess)
    """
    if success_message:
        logger.info(success_message)
    
    result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    
    if result.returncode != 0:
        logger.error(f"{error_message}: {result.stderr}")
        return False, result
    
    return True, result

def create_conda_env(env_name, lockfile_path, conda_manager="conda", force_recreate=False):
    """
    Create a conda environment from a lockfile.

    Parameters
    ----------
    env_name : str
        Name of the conda environment to create.
    lockfile_path : str or Path
        Path to the conda lockfile.
    conda_manager : str, optional
        Conda manager to use ('conda' or 'mamba'), by default "conda".
    force_recreate : bool, optional
        Whether to remove existing environment before creating, by default False.

    Returns
    -------
    bool
        True if environment creation succeeded, False otherwise.
    """
    # Check if environment already exists
    check_cmd = [conda_manager, "env", "list"]
    success, result = run_command_with_logging(
        check_cmd, 
        success_message=f"Checking if environment {env_name} exists...",
        error_message="Error checking environments"
    )
    
    if not success:
        return False

    env_exists = False
    env_lines = result.stdout.split('\n')
    for line in env_lines:
        if line.strip().startswith(env_name + ' '):
            env_exists = True
            break

    if env_exists and force_recreate:
        remove_cmd = [conda_manager, "env", "remove", "--name", env_name, "-y"]
        success, _ = run_command_with_logging(
            remove_cmd,
            success_message=f"Environment {env_name} exists, removing it for recreation...",
            error_message="Error removing environment"
        )
        if not success:
            return False
    elif env_exists:
        logger.info(f"Environment {env_name} already exists, skipping creation.")
        return True

    # Environment doesn't exist (or was removed), create it
    cmd = [conda_manager, "create", "--name", env_name, "--file", str(lockfile_path), "-y"]
    success, _ = run_command_with_logging(
        cmd,
        success_message=f"Creating conda environment: {' '.join(cmd)}",
        error_message="Error creating environment"
    )
    return success

def get_lockfile_for_commit(tardis_repo, commit_hash):
    """
    Get conda lockfile content for a specific commit and save temporarily.

    Parameters
    ----------
    tardis_repo : git.Repo
        Git repository object for TARDIS.
    commit_hash : str
        Hash of the commit to get lockfile from.

    Returns
    -------
    str or None
        Path to temporary lockfile, or None if lockfile not found.
    """
    try:
        from git.exc import GitCommandError
    except ImportError:
        raise ImportError("GitPython is required. Install with: pip install gitpython")
    
    try:
        # Use git show to get the lockfile content without checking out
        result = tardis_repo.git.show(f"{commit_hash}:conda-linux-64.lock")

        # Create a temporary file with the lockfile content
        temp_lockfile = tempfile.NamedTemporaryFile(mode='w', suffix='.lock', delete=False)
        temp_lockfile.write(result)
        temp_lockfile.close()

        return temp_lockfile.name
    except GitCommandError as e:
        logger.warning(f"Could not get lockfile for commit {commit_hash}: {e}")
        return None

def run_pytest_with_marker(marker_expr, test_path, regression_path, tardis_path, env_name, conda_manager):
    """
    Run pytest with specific marker expression.

    Parameters
    ----------
    marker_expr : str
        Pytest marker expression to filter tests.
    test_path : str
        Path to the test file or directory.
    regression_path : str or Path
        Path to regression data directory.
    tardis_path : str or Path
        Path to TARDIS repository.
    env_name : str or None
        Name of conda environment to use.
    conda_manager : str
        Conda manager to use ('conda' or 'mamba').

    Returns
    -------
    subprocess.CompletedProcess
        Result of the pytest command execution.
    """
    # Build base pytest command
    pytest_args = [
        "python", "-m", "pytest",
        test_path,
        f"--tardis-regression-data={regression_path}",
        "--generate-reference",
        "--disable-warnings",
        "-m", marker_expr
    ]

    # Prepend conda command
    env_flag = "-p" if "/" in env_name else "-n"
    cmd = [conda_manager, "run", env_flag, env_name] + pytest_args

    logger.info(f"Running {marker_expr} tests: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        check=False,  # Don't raise exception on non-zero exit code
        capture_output=True,
        text=True,
        cwd=tardis_path
    )
    return result

def get_all_optional_dependencies(tardis_path):
    """
    Get all available optional dependencies from pyproject.toml.

    Parameters
    ----------
    tardis_path : str or Path
        Path to TARDIS repository containing pyproject.toml.

    Returns
    -------
    list of str
        List of optional dependency group names.
    """
    pyproject_path = Path(tardis_path) / "pyproject.toml"
    if not pyproject_path.exists():
        return []

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    return list(data.get("project", {}).get("optional-dependencies", {}).keys())

def install_tardis_in_env(env_name, tardis_path=None, conda_manager="conda"):
    """
    Install TARDIS with optional dependencies in conda environment.

    Parameters
    ----------
    env_name : str
        Name or path of the conda environment.
    tardis_path : str or Path, optional
        Path to TARDIS repository, by default None.
    conda_manager : str, optional
        Conda manager to use ('conda' or 'mamba'), by default "conda".

    Returns
    -------
    bool
        True if installation succeeded, False otherwise.
    """
    # Determine if env_name is a path or name
    env_flag = "-p" if "/" in env_name else "-n"

    # Get all available optional dependencies
    all_extras = get_all_optional_dependencies(tardis_path)

    if all_extras:
        # Try installing with all optional dependencies first
        extras_str = f"[{','.join(all_extras)}]"
        cmd = [conda_manager, "run", env_flag, env_name, "pip", "install", "-e", f"{tardis_path}{extras_str}"]
        
        success, _ = run_command_with_logging(
            cmd,
            success_message=f"Installing TARDIS with all extras {all_extras}: {' '.join(cmd)}",
            error_message="Error installing TARDIS with extras"
        )
        
        if success:
            return True

    # Fall back to installing just TARDIS
    cmd = [conda_manager, "run", env_flag, env_name, "pip", "install", "-e", str(tardis_path)]
    success, _ = run_command_with_logging(
        cmd,
        success_message=f"Fallback - Installing TARDIS in environment: {' '.join(cmd)}",
        error_message="Error installing TARDIS (fallback)"
    )
    return success

def setup_environment_for_commit(commit, tardis_repo, tardis_path, conda_manager, default_curr_env, force_recreate):
    
    env_name = None

    # Create unique environment for this commit
    env_name = f"tardis-test-{commit.hexsha[:8]}"
    logger.info(f"Creating conda environment: {env_name}")
    
    # Get the lockfile for this specific commit
    temp_lockfile_path = get_lockfile_for_commit(tardis_repo, commit.hexsha)
    
    if temp_lockfile_path is None:
        logger.error(f"Could not get lockfile for commit {commit.hexsha}")
        return handle_fallback(default_curr_env)
    
    # Try to create the environment
    env_creation_success = create_conda_env(env_name, temp_lockfile_path, conda_manager, force_recreate=force_recreate)
    
    # Clean up temporary lockfile (regardless of success/failure)
    if temp_lockfile_path:
        os.unlink(temp_lockfile_path)
    
    if not env_creation_success:
        logger.error(f"Failed to create conda environment for commit {commit.hexsha}")
        return handle_fallback(default_curr_env)
    
    # Install TARDIS in the newly created environment
    if not install_tardis_in_env(env_name, tardis_path, conda_manager):
        logger.error(f"Failed to install TARDIS in environment for commit {commit.hexsha}")
        return handle_fallback(default_curr_env)
    
    return True, env_name

def handle_fallback(default_curr_env):
    if default_curr_env:
        logger.info(f"Falling back to provided default environment: {default_curr_env}")
        return True, default_curr_env
    else:
        logger.error("No default environment provided, skipping commit")
        return False, None

def run_tests(tardis_repo_path, regression_data_repo_path, branch, commits_input=None, n=10, test_path="tardis/spectrum/tests/test_spectrum_solver.py", conda_manager="conda", default_curr_env=None, force_recreate=False, use_new_envs=True):
    """
    Run pytest across multiple TARDIS commits.

    Parameters
    ----------
    tardis_repo_path : str or Path
        Path to TARDIS repository.
    regression_data_repo_path : str or Path
        Path to regression data repository.
    branch : str
        Branch name to iterate commits from.

    commits_input : str, list, or optional
        Specific commits to test or number of commits, by default None.
    n : int, optional
        Number of recent commits to test, by default 10.
    test_path : str, optional
        Path to test file, by default "tardis/spectrum/tests/test_spectrum_solver.py".
    conda_manager : str, optional
        Conda manager to use ('conda' or 'mamba'), by default "conda".
    default_curr_env : str, optional
        Default environment to fall back to, by default None.
    force_recreate : bool, optional
        Whether to force recreate conda environments, by default False.
    use_new_envs : bool, optional
        Whether to use new environments for each commit, by default True.

    Returns
    -------
    tuple
        (processed_commits, regression_commits, original_head)
        Lists of commit hashes and original head commit.
    """
    try:
        from git import Repo
    except ImportError:
        raise ImportError("GitPython is required. Install with: pip install gitpython")
    
    tardis_path = Path(tardis_repo_path)
    regression_path = Path(regression_data_repo_path)

    tardis_repo = Repo(tardis_path)
    regression_repo = Repo(regression_path)

    original_head = regression_repo.head.commit.hexsha
    logger.info(f"Original HEAD of regression data repo: {original_head}")

    if commits_input:
        if isinstance(commits_input, str):
            commits_input = [commits_input]
        
        n = len(commits_input)
        commits = []
        for commit_hash in commits_input:
            commit = tardis_repo.commit(commit_hash)
            commits.append(commit)
    else:
        commits = list(tardis_repo.iter_commits(branch, max_count=n))
        commits.reverse()

    processed_commits = []
    regression_commits = []

    for i, commit in enumerate(commits, 1):
        logger.info(f"Processing commit {i}/{n}: {commit.hexsha}")

        if use_new_envs:
            success, env_name = setup_environment_for_commit(commit, tardis_repo, tardis_path, conda_manager, default_curr_env, force_recreate)
            
            if not success:
                continue
        else:
            success, env_name = handle_fallback(default_curr_env)
            
            if not success:
                continue

        # Now checkout the commit for running tests (after environment creation)
        tardis_repo.git.checkout(commit.hexsha)
        tardis_repo.git.reset('--hard')
        tardis_repo.git.clean('-fd')

        # Define test phases
        test_phases = [
            ("not continuum", "Phase 1"),
            ("continuum", "Phase 2")
        ]

        results = []
        for marker, phase_name in test_phases:
            logger.info(f"\n=== {phase_name}: Running '{marker}' tests for commit {commit.hexsha} ===")
            result = run_pytest_with_marker(marker, test_path, regression_path, tardis_path, env_name, conda_manager)
            results.append(result)
            
            if result.returncode != 0:
                logger.warning(f"'{marker}' tests had failures for commit {commit.hexsha}")
                logger.info(f"Stdout: {result.stdout}")
                logger.error(f"Stderr: {result.stderr}")

        # Even if tests failed, if regression data was generated, commit it
        regression_repo.git.add(A=True)
        # Check if anything was actually staged
        if not regression_repo.git.diff('--cached', '--name-only').strip():
            raise Exception(f"No data to add - git add was empty for commit {commit.hexsha}")

        regression_commit = regression_repo.index.commit(f"Regression data for tardis commit {i}")
        regression_commits.append(regression_commit.hexsha)
        processed_commits.append(commit.hexsha)

        # Check overall success
        if all(result.returncode == 0 for result in results):
            logger.info(f"All tests passed for commit {commit.hexsha}")
        else:
            logger.warning(f"Tests completed with some failures for commit {commit.hexsha}, but regression data was generated")

    logger.info("\nProcessed Tardis Commits:")
    for hash in processed_commits:
        logger.info(hash)

    logger.info("\nRegression Data Commits:")
    for hash in regression_commits:
        logger.info(hash)

    return processed_commits, regression_commits, original_head