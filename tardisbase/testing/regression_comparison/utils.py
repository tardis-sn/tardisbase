import subprocess
from pathlib import Path
import logging
from tardisbase.testing.regression_comparison import CONFIG

logger = logging.getLogger(__name__)

def color_print(text, color):
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'reset': '\033[0m'
    }
    print(f"{colors.get(color, '')}{text}{colors['reset']}")

def get_relative_path(path, base):
    return str(Path(path).relative_to(base))

def get_last_two_commits(repo_path=None):
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