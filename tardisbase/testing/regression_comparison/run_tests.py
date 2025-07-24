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
    """Get the conda lockfile content for a specific commit and save it temporarily."""
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
    """Helper function to run pytest"""
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
    """Get all available optional dependencies from pyproject.toml"""
    pyproject_path = Path(tardis_path) / "pyproject.toml"
    if not pyproject_path.exists():
        return []

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    return list(data.get("project", {}).get("optional-dependencies", {}).keys())

def install_tardis_in_env(env_name, tardis_path=None, conda_manager="conda"):
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


def run_tests(tardis_repo_path, regression_data_repo_path, branch, target_file=None, commits_input=None, n=10, test_path="tardis/spectrum/tests/test_spectrum_solver.py", use_conda=False, conda_manager="conda", default_curr_env=None, force_recreate=False):
    tardis_path = Path(tardis_repo_path)
    regression_path = Path(regression_data_repo_path)
    target_file_path = regression_path / target_file if target_file else None

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
                if not create_conda_env(env_name, temp_lockfile_path, conda_manager, force_recreate=force_recreate):
                    print(f"Failed to create conda environment for commit {commit.hexsha}")
                    # Clean up temporary lockfile
                    if temp_lockfile_path and temp_lockfile_path != str(tardis_path / "conda-linux-64.lock"):
                            os.unlink(temp_lockfile_path)

                    if default_curr_env:
                        print(f"Falling back to provided default environment: {default_curr_env}")
                        env_name = default_curr_env
                    else:
                        print(f"No default environment provided, skipping commit")
                        continue
                else:
                    # Environment created successfully, clean up temporary lockfile
                    if temp_lockfile_path and temp_lockfile_path != str(tardis_path / "conda-linux-64.lock"):
                            os.unlink(temp_lockfile_path)

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

        try:
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

            # Validate target file if specified
            if target_file_path and not target_file_path.exists():
                print(f"Error: HDF5 file {target_file_path} was not generated.")
                continue

            # Even if tests failed, if regression data was generated, commit it
            regression_repo.git.add(A=True)
            regression_commit = regression_repo.index.commit(f"Regression data for tardis commit {i}")
            regression_commits.append(regression_commit.hexsha)
            processed_commits.append(commit.hexsha)

            if result1.returncode == 0 and result2.returncode == 0:
                print(f"All tests passed for commit {commit.hexsha}")
            else:
                print(f"Tests completed with some failures for commit {commit.hexsha}, but regression data was generated")

        except Exception as e:
            print(f"Error running pytest for commit {commit.hexsha}: {e}")
            continue

    print("\nProcessed Tardis Commits:")
    for hash in processed_commits:
        print(hash)

    print("\nRegression Data Commits:")
    for hash in regression_commits:
        print(hash)

    return processed_commits, regression_commits, original_head, str(target_file_path) if target_file_path else None