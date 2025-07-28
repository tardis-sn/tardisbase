import subprocess
import tempfile
import os
from pathlib import Path
from git import Repo
from git.exc import GitCommandError

try:
    import tomllib
except ImportError:
    import tomli as tomllib

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
    print(f"Checking if environment {env_name} exists...")
    result = subprocess.run(check_cmd, capture_output=True, text=True)

    env_exists = False
    if result.returncode == 0:
        # Parse the output to see if our environment exists
        env_lines = result.stdout.split('\n')
        for line in env_lines:
            if line.strip().startswith(env_name + ' '):
                env_exists = True
                break

    if env_exists:
        if force_recreate:
            print(f"Environment {env_name} exists, removing it for recreation...")
            remove_cmd = [conda_manager, "env", "remove", "--name", env_name, "-y"]
            remove_result = subprocess.run(remove_cmd, capture_output=True, text=True)
            if remove_result.returncode != 0:
                print(f"Error removing environment: {remove_result.stderr}")
                return False
        else:
            print(f"Environment {env_name} already exists, skipping creation.")
            return True

    # Environment doesn't exist (or was removed), create it
    cmd = [conda_manager, "create", "--name", env_name, "--file", str(lockfile_path), "-y"]
    print(f"Creating conda environment: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error creating environment: {result.stderr}")
        return False
    return True

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
        # Use git show to get the lockfile content without checking out
        result = tardis_repo.git.show(f"{commit_hash}:conda-linux-64.lock")

        # Create a temporary file with the lockfile content
        temp_lockfile = tempfile.NamedTemporaryFile(mode='w', suffix='.lock', delete=False)
        temp_lockfile.write(result)
        temp_lockfile.close()

        return temp_lockfile.name
    except GitCommandError as e:
        print(f"Warning: Could not get lockfile for commit {commit_hash}: {e}")
        return None

def run_pytest_with_marker(marker_expr, phase_name, test_path, regression_path, tardis_path, use_conda, env_name, conda_manager):
    """
    Run pytest with specific marker expression.

    Parameters
    ----------
    marker_expr : str
        Pytest marker expression to filter tests.
    phase_name : str
        Descriptive name for the test phase.
    test_path : str
        Path to the test file or directory.
    regression_path : str or Path
        Path to regression data directory.
    tardis_path : str or Path
        Path to TARDIS repository.
    use_conda : bool
        Whether to use conda environment.
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

    # Prepend conda command if needed
    if use_conda and env_name:
        env_flag = "-p" if "/" in env_name else "-n"
        cmd = [conda_manager, "run", env_flag, env_name] + pytest_args
    else:
        cmd = pytest_args

    print(f"Running {phase_name} tests: {' '.join(cmd)}")
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
        print(f"Installing TARDIS with all extras {all_extras}: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return True
        else:
            print(f"Error installing TARDIS with extras: {result.stderr}")

    # Fall back to installing just TARDIS
    cmd = [conda_manager, "run", env_flag, env_name, "pip", "install", "-e", str(tardis_path)]
    print(f"Fallback - Installing TARDIS in environment: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error installing TARDIS (fallback): {result.stderr}")
        return False
    return True


def run_tests(tardis_repo_path, regression_data_repo_path, branch, commits_input=None, n=10, test_path="tardis/spectrum/tests/test_spectrum_solver.py", use_conda=False, conda_manager="conda", default_curr_env=None, force_recreate=False):
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

    commits_input : str, list, or int, optional
        Specific commits to test or number of commits, by default None.
    n : int, optional
        Number of recent commits to test, by default 10.
    test_path : str, optional
        Path to test file, by default "tardis/spectrum/tests/test_spectrum_solver.py".
    use_conda : bool, optional
        Whether to use conda environments, by default False.
    conda_manager : str, optional
        Conda manager to use ('conda' or 'mamba'), by default "conda".
    default_curr_env : str, optional
        Default environment to fall back to, by default None.
    force_recreate : bool, optional
        Whether to force recreate conda environments, by default False.

    Returns
    -------
    tuple
        (processed_commits, regression_commits, original_head)
        Lists of commit hashes and original head commit.
    """
    tardis_path = Path(tardis_repo_path)
    regression_path = Path(regression_data_repo_path)

    tardis_repo = Repo(tardis_path)
    regression_repo = Repo(regression_path)

    original_head = regression_repo.head.commit.hexsha
    print(f"Original HEAD of regression data repo: {original_head}")

    if commits_input:
        if isinstance(commits_input, str):
            commits_input = [commits_input]
        elif isinstance(commits_input, int):
            n = commits_input  
            commits_input = None

        if commits_input:
            n = len(commits_input)
            commits = []
            for commit_hash in commits_input:
                commit = tardis_repo.commit(commit_hash)
                commits.append(commit)
        else:
            commits = list(tardis_repo.iter_commits(branch, max_count=n))
            commits.reverse()
    else:
        commits = list(tardis_repo.iter_commits(branch, max_count=n))
        commits.reverse()

    processed_commits = []
    regression_commits = []

    for i, commit in enumerate(commits, 1):
        print(f"Processing commit {i}/{n}: {commit.hexsha}")

        env_name = None
        temp_lockfile_path = None
        if use_conda:
            # Create unique environment for this commit
            env_name = f"tardis-test-{commit.hexsha[:8]}"
            print(f"Creating conda environment: {env_name}")

            # Get the lockfile for this specific commit
            temp_lockfile_path = get_lockfile_for_commit(tardis_repo, commit.hexsha)

            if temp_lockfile_path is None:
                print(f"Could not get lockfile for commit {commit.hexsha}")
                if default_curr_env:
                    print(f"Falling back to provided default environment: {default_curr_env}")
                    env_name = default_curr_env
                else:
                    print(f"No default environment provided, skipping commit")
                    continue
            else:
                # Try to create the environment
                env_creation_success = create_conda_env(env_name, temp_lockfile_path, conda_manager, force_recreate=force_recreate)

                # Clean up temporary lockfile (regardless of success/failure)
                if temp_lockfile_path and temp_lockfile_path != str(tardis_path / "conda-linux-64.lock"):
                    os.unlink(temp_lockfile_path)

                if not env_creation_success:
                    print(f"Failed to create conda environment for commit {commit.hexsha}")
                    if default_curr_env:
                        print(f"Falling back to provided default environment: {default_curr_env}")
                        env_name = default_curr_env
                    else:
                        print(f"No default environment provided, skipping commit")
                        continue
                else:
                    # Install TARDIS in the newly created environment
                    if not install_tardis_in_env(env_name, tardis_path, conda_manager):
                        print(f"Failed to install TARDIS in environment for commit {commit.hexsha}")
                        if default_curr_env:
                            print(f"Falling back to provided default environment: {default_curr_env}")
                            env_name = default_curr_env
                        else:
                            print(f"No default environment provided, skipping commit")
                            continue

        # Now checkout the commit for running tests (after environment creation)
        tardis_repo.git.checkout(commit.hexsha)
        tardis_repo.git.reset('--hard')
        tardis_repo.git.clean('-fd')

        # Run "not continuum" tests
        print(f"\n=== Phase 1: Running 'not continuum' tests for commit {commit.hexsha} ===")
        result1 = run_pytest_with_marker("not continuum", "Not continuum", test_path, regression_path, tardis_path, use_conda, env_name, conda_manager)

        # Run "continuum" tests
        print(f"\n=== Phase 2: Running 'continuum' tests for commit {commit.hexsha} ===")
        result2 = run_pytest_with_marker("continuum", "Continuum", test_path, regression_path, tardis_path, use_conda, env_name, conda_manager)

        # Check if either phase had failures but still generated data
        if result1.returncode != 0:
            print(f"Warning: 'not continuum' tests had failures for commit {commit.hexsha}")
            print("Stdout:", result1.stdout)
            print("Stderr:", result1.stderr)

        if result2.returncode != 0:
            print(f"Warning: 'continuum' tests had failures for commit {commit.hexsha}")
            print("Stdout:", result2.stdout)
            print("Stderr:", result2.stderr)



        # Even if tests failed, if regression data was generated, commit it
        regression_repo.git.add(A=True)
        regression_commit = regression_repo.index.commit(f"Regression data for tardis commit {i}")
        regression_commits.append(regression_commit.hexsha)
        processed_commits.append(commit.hexsha)

        if result1.returncode == 0 and result2.returncode == 0:
            print(f"All tests passed for commit {commit.hexsha}")
        else:
            print(f"Tests completed with some failures for commit {commit.hexsha}, but regression data was generated")

    print("\nProcessed Tardis Commits:")
    for hash in processed_commits:
        print(hash)

    print("\nRegression Data Commits:")
    for hash in regression_commits:
        print(hash)

    return processed_commits, regression_commits, original_head