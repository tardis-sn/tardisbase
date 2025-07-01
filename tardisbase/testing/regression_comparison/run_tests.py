import subprocess
from pathlib import Path
from git import Repo

def create_conda_env(env_name, lockfile_path):
    cmd = ["conda", "create", "--name", env_name, "--file", str(lockfile_path), "-y"]
    print(f"Creating conda environment: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error creating environment: {result.stderr}")
        return False
    return True

def install_tardis_in_env(env_name, tardis_path):
    cmd = ["conda", "run", "-n", env_name, "pip", "install", "-e", str(tardis_path)]
    print(f"Installing TARDIS in environment: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error installing TARDIS: {result.stderr}")
        return False
    return True

def run_tests(tardis_repo_path, regression_data_repo_path, branch, target_file, commits_input=None, n=10, test_path="tardis/spectrum/tests/test_spectrum_solver.py", use_conda=False):
    tardis_path = Path(tardis_repo_path)
    regression_path = Path(regression_data_repo_path)
    target_file_path = regression_path / target_file
    lockfile_path = tardis_path / "conda-linux-64.lock"

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
                try:
                    commit = tardis_repo.commit(commit_hash)
                    commits.append(commit)
                except Exception as e:
                    print(f"Error finding commit {commit_hash}: {e}")
                    continue
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
        tardis_repo.git.checkout(commit.hexsha)
        tardis_repo.git.reset('--hard')
        tardis_repo.git.clean('-fd')

        env_name = None
        if use_conda:
            # Create unique environment name for this commit
            env_name = f"tardis-test-{commit.hexsha[:8]}"
            print(f"Creating conda environment: {env_name}")
            
            if not create_conda_env(env_name, lockfile_path):
                print(f"Failed to create conda environment for commit {commit.hexsha}")
                continue
            
            if not install_tardis_in_env(env_name, tardis_path):
                print(f"Failed to install TARDIS in environment for commit {commit.hexsha}")
                continue

        # Prepare pytest command
        if use_conda and env_name:
            cmd = [
                "conda", "run", "-n", env_name,
                "python", "-m", "pytest",
                test_path,
                f"--tardis-regression-data={regression_path}",
                "--generate-reference",
                "-x",
                "--disable-warnings"
            ]
        else:
            cmd = [
                "python", "-m", "pytest",
                test_path,
                f"--tardis-regression-data={regression_path}",
                "--generate-reference",
                "-x",
                "--disable-warnings"
            ]
        
        print(f"Running pytest command: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                cwd=tardis_path 
            )
            print("Pytest stdout:")
            print(result.stdout)
            print("Pytest stderr:")
            print(result.stderr)

            if not target_file_path.exists():
                print(f"Error: HDF5 file {target_file_path} was not generated.")
                continue

            regression_repo.git.add(A=True)
            regression_commit = regression_repo.index.commit(f"Regression data for tardis commit {i}")
            regression_commits.append(regression_commit.hexsha)
            processed_commits.append(commit.hexsha)
            
        except subprocess.CalledProcessError as e:
            print(f"Error running pytest for commit {commit.hexsha}: {e}")
            print("Pytest stdout:")
            print(e.stdout)
            print("Pytest stderr:")
            print(e.stderr)
            continue

    print("\nProcessed Tardis Commits:")
    for hash in processed_commits:
        print(hash)

    print("\nRegression Data Commits:")
    for hash in regression_commits:
        print(hash)

    return processed_commits, regression_commits, original_head, str(target_file_path)