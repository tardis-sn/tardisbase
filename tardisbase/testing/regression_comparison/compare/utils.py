import shutil
import subprocess
import tempfile
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Configuration settings
CONFIG = {
    'compare_path': '.',  # Default to current directory
    'temp_dir_prefix': 'ref_compare_',
    'regression_data_repo': '/path/to/regression_data'
}

# Constants
COLORS = {
    'red': '\033[91m',
    'green': '\033[92m',
    'yellow': '\033[93m',
    'blue': '\033[94m',
    'reset': '\033[0m'
}

FLOAT_UNCERTAINTY = 1e-14

# Utility functions
def color_print(text: str, color: str) -> None:
    print(f"{COLORS.get(color, '')}{text}{COLORS['reset']}")

def get_relative_path(path: Path | str, base: Path | str) -> str:
    return str(Path(path).relative_to(base))

def get_last_two_commits(repo_path: str | Path | None = None) -> tuple[str | None, str | None]:
    if repo_path is None:
        repo_path = CONFIG['regression_data_repo']
    try:
        if not Path(repo_path).exists():
            logger.error(f"Regression data repository not found at {repo_path}")
            return None, None
        
        result = subprocess.run(
            ['git', '-C', str(repo_path), 'log', '--format=%H', '-n', '2'],
            capture_output=True,
            text=True,
            check=True
        )
        commits = result.stdout.strip().split('\n')
        if len(commits) >= 2:
            return commits[1], commits[0]
        return None, None
    except (subprocess.SubprocessError, subprocess.CalledProcessError):
        logger.error("Unable to get git commits.")
        return None, None

class FileManager:
    def __init__(self, repo_path: str | Path | None = None):
        self.temp_dir = None
        self.repo_path = Path(repo_path) if repo_path else Path(CONFIG['compare_path'])

    def setup(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix=CONFIG['temp_dir_prefix']))
        print(f'Created temporary directory at {self.temp_dir}')

    def teardown(self) -> None:
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            print(f'Removed temporary directory {self.temp_dir}')
        self.temp_dir = None

    def get_temp_path(self, filename: str) -> str:
        return str(self.temp_dir / filename)

    def copy_file(self, source: str | Path, destination: str | Path) -> None:
        shutil.copy2(source, self.get_temp_path(destination))

class FileSetup:
    def __init__(self, file_manager: FileManager, ref1_hash: str | None, ref2_hash: str | None):
        self.file_manager = file_manager
        self.ref1_hash = ref1_hash
        self.ref2_hash = ref2_hash
        self.repo_path = file_manager.repo_path

    def setup(self) -> None:
        for ref_id, ref_hash in enumerate([self.ref1_hash, self.ref2_hash], 1):
            ref_dir = self.file_manager.get_temp_path(f"ref{ref_id}")
            os.makedirs(ref_dir, exist_ok=True)
            if ref_hash:
                self._copy_data_from_hash(ref_hash, ref_dir)
            else:
                subprocess.run(f'cp -r {self.repo_path}/* {ref_dir}', shell=True)

    def _copy_data_from_hash(self, ref_hash: str, ref_dir: str | Path) -> None:
        git_cmd = [
            'git', '-C', str(self.repo_path),
            'archive', ref_hash, '|',
            'tar', '-x', '-C', str(ref_dir)
        ]
        subprocess.run(' '.join(git_cmd), shell=True) 