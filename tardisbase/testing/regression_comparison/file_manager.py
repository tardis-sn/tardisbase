import shutil
import subprocess
import tempfile
from pathlib import Path
import os
from __init__ import CONFIG

class FileManager:
    def __init__(self, repo_path=None):
        self.temp_dir = None
        self.repo_path = Path(repo_path) if repo_path else Path(CONFIG['compare_path'])

    def setup(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix=CONFIG['temp_dir_prefix']))
        print(f'Created temporary directory at {self.temp_dir}')

    def teardown(self):
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            print(f'Removed temporary directory {self.temp_dir}')
        self.temp_dir = None

    def get_temp_path(self, filename):
        return str(self.temp_dir / filename)

    def copy_file(self, source, destination):
        shutil.copy2(source, self.get_temp_path(destination))

class FileSetup:
    def __init__(self, file_manager, ref1_hash, ref2_hash):
        self.file_manager = file_manager
        self.ref1_hash = ref1_hash
        self.ref2_hash = ref2_hash
        self.repo_path = file_manager.repo_path

    def setup(self):
        for ref_id, ref_hash in enumerate([self.ref1_hash, self.ref2_hash], 1):
            ref_dir = self.file_manager.get_temp_path(f"ref{ref_id}")
            os.makedirs(ref_dir, exist_ok=True)
            if ref_hash:
                self._copy_data_from_hash(ref_hash, ref_dir)
            else:
                subprocess.run(f'cp -r {self.repo_path}/* {ref_dir}', shell=True)

    def _copy_data_from_hash(self, ref_hash, ref_dir):
        git_cmd = ['git', '-C', str(self.repo_path), 'archive', ref_hash, '|', 'tar', '-x', '-C', str(ref_dir)]
        subprocess.run(' '.join(git_cmd), shell=True)