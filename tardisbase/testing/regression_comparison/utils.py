import subprocess
from pathlib import Path

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

def get_last_two_commits():
    try:
        result = subprocess.run(['git', 'log', '--format=%H', '-n', '2'], 
                              capture_output=True, 
                              text=True, 
                              check=True)
        commits = result.stdout.strip().split('\n')
        if len(commits) >= 2:
            return commits[1], commits[0]
        return None, None
    except (subprocess.SubprocessError, subprocess.CalledProcessError):
        print("Error: Unable to get git commits.")
        return None, None