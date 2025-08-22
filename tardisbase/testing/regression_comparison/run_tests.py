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
        (result_status: bool, process_result: subprocess.CompletedProcess)
    """
    if success_message:
        logger.info(success_message)
    
    result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    
    result_status = True
    if result.returncode != 0:
        cmd_str = ' '.join(cmd)
        logger.error(f"{error_message}")
        logger.error(f"Command: {cmd_str}")
        logger.error(f"Return code: {result.returncode}")
        
        # Log last 10 lines of stdout if available
        if result.stdout.strip():
            stdout_lines = result.stdout.strip().split('\n')
            last_stdout = stdout_lines[-10:] if len(stdout_lines) > 10 else stdout_lines
            logger.error(f"Last {len(last_stdout)} lines of stdout:")
            for line in last_stdout:
                logger.error(f"  {line}")
        
        # Log last 10 lines of stderr if available  
        if result.stderr.strip():
            stderr_lines = result.stderr.strip().split('\n')
            last_stderr = stderr_lines[-10:] if len(stderr_lines) > 10 else stderr_lines
            logger.error(f"Last {len(last_stderr)} lines of stderr:")
            for line in last_stderr:
                logger.error(f"  {line}")
        
        result_status = False
    else:
        # Command succeeded - log last 3 lines of stdout to show what happened
        if result.stdout.strip():
            stdout_lines = result.stdout.strip().split('\n')
            last_success_stdout = stdout_lines[-3:] if len(stdout_lines) > 3 else stdout_lines
            logger.info(f"Command completed successfully. Last {len(last_success_stdout)} lines of output:")
            for line in last_success_stdout:
                logger.info(f"  {line}")
    
    return result_status, result

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
    success = False
    env_exists = False
    create_env = False

    # Check if environment already exists
    check_cmd = [conda_manager, "env", "list"]
    environ_found, result = run_command_with_logging(
        check_cmd, 
        success_message=f"Checking if environment {env_name} exists...",
        error_message="Error checking environments"
    )
    
    if environ_found:
        # Parse environment list to check if env exists
        env_exists = any(
            line.strip().startswith(env_name + ' ') 
            for line in result.stdout.split('\n')
        )

    if env_exists and force_recreate:
        # Remove existing environment for recreation
        remove_cmd = [conda_manager, "env", "remove", "--name", env_name, "-y"]
        del_environ, _ = run_command_with_logging(
            remove_cmd,
            success_message=f"Environment {env_name} exists, removing it for recreation...",
            error_message="Error removing environment"
        )
        if del_environ:
            create_env = True
    elif env_exists:
        logger.info(f"Environment {env_name} already exists, skipping creation.")
        success = True
    else:
        create_env = True

    if create_env:
        # Create new environment
        cmd = [conda_manager, "create", "--name", env_name, "--file", str(lockfile_path), "-y"]
        create_env_proc, _ = run_command_with_logging(
            cmd,
            success_message=f"Creating conda environment: {' '.join(cmd)}",
            error_message="Error creating environment"
        )
        success = create_env_proc
    
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
    temp_lockfile_path = None
    
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

        temp_lockfile_path = temp_lockfile.name
    except GitCommandError as e:
        logger.warning(f"Could not get lockfile for commit {commit_hash}: {e}")

    return temp_lockfile_path

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
    # Build pytest command
    pytest_args = [
        "python", "-m", "pytest", test_path,
        f"--tardis-regression-data={regression_path}",
        "--generate-reference", "--disable-warnings",
        "-m", marker_expr
    ]

    # Prepend conda command with appropriate env flag
    env_flag = "-p" if "/" in env_name else "-n"
    cmd = [conda_manager, "run", env_flag, env_name] + pytest_args

    logger.info(f"Running {marker_expr} tests: {' '.join(cmd)}")
    return subprocess.run(
        cmd, check=False, capture_output=True, text=True, cwd=tardis_path
    )

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
    optional_dependencies = []
    
    pyproject_path = Path(tardis_path) / "pyproject.toml"
    if pyproject_path.exists():
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)

        optional_dependencies = list(data.get("project", {}).get("optional-dependencies", {}).keys())
    
    return optional_dependencies

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
    success = False
    
    # Determine if env_name is a path or name
    env_flag = "-p" if "/" in env_name else "-n"

    # Get all available optional dependencies
    all_extras = get_all_optional_dependencies(tardis_path)

    if all_extras:
        # Try installing with all optional dependencies first
        extras_str = f"[{','.join(all_extras)}]"
        cmd = [conda_manager, "run", env_flag, env_name, "pip", "install", "-e", f"{tardis_path}{extras_str}"]
        
        install_tardis_extra, _ = run_command_with_logging(
            cmd,
            success_message=f"Installing TARDIS with all extras {all_extras}: {' '.join(cmd)}",
            error_message="Error installing TARDIS with extras"
        )
        
        if install_tardis_extra:
            success = True

    if not success:
        # Fall back to installing just TARDIS
        cmd = [conda_manager, "run", env_flag, env_name, "pip", "install", "-e", str(tardis_path)]
        install_tardis_no_extra, _ = run_command_with_logging(
            cmd,
            success_message=f"Fallback - Installing TARDIS in environment: {' '.join(cmd)}",
            error_message="Error installing TARDIS (fallback)"
        )
        success = install_tardis_no_extra
    
    return success

def setup_environment_for_commit(commit, tardis_repo, tardis_path, conda_manager, default_curr_env, force_recreate):
    """
    Set up conda environment for a specific commit.

    Returns
    -------
    tuple
        (success: bool, env_name: str or None)
    """
    setup_success = False
    final_env_name = None
    temp_lockfile_path = None
    
    env_name = f"tardis-test-{commit.hexsha[:8]}"
    logger.info(f"Creating conda environment: {env_name}")
    
    # Get the lockfile for this specific commit
    temp_lockfile_path = get_lockfile_for_commit(tardis_repo, commit.hexsha)
    
    if temp_lockfile_path is None:
        logger.error(f"Could not get lockfile for commit {commit.hexsha}")
        setup_success, final_env_name = handle_fallback(default_curr_env)
    else:
        # Try to create the environment
        env_creation_success = create_conda_env(
            env_name, temp_lockfile_path, conda_manager, force_recreate=force_recreate
        )
        
        if not env_creation_success:
            logger.error(f"Failed to create conda environment for commit {commit.hexsha}")
            setup_success, final_env_name = handle_fallback(default_curr_env)
        else:
            # Install TARDIS in the newly created environment
            tardis_install_success = install_tardis_in_env(env_name, tardis_path, conda_manager)
            if not tardis_install_success:
                logger.error(f"Failed to install TARDIS in environment for commit {commit.hexsha}")
                setup_success, final_env_name = handle_fallback(default_curr_env)
            else:
                setup_success = True
                final_env_name = env_name
        
        # Clean up temporary lockfile
        os.unlink(temp_lockfile_path)
    
    return setup_success, final_env_name

def handle_fallback(default_curr_env):
    """Handle fallback to default environment."""
    success = False
    env_name = None
    
    if default_curr_env:
        logger.info(f"Falling back to provided default environment: {default_curr_env}")
        success = True
        env_name = default_curr_env
    else:
        logger.error("No default environment provided, skipping commit")
    
    return success, env_name

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
        else:
            success, env_name = handle_fallback(default_curr_env)
            
        if success:
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
                    logger.warning(f"Return code: {result.returncode}")
                    if result.stdout.strip():
                        logger.info(f"Stdout: {result.stdout.strip()}")
                    if result.stderr.strip():
                        logger.error(f"Stderr: {result.stderr.strip()}")

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