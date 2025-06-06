import os
import numpy as np
from pathlib import Path
from filecmp import dircmp

from tardisbase.testing.regression_comparison.compare.utils import FileManager, FileSetup, get_relative_path
from tardisbase.testing.regression_comparison.compare.analyzers import DiffAnalyzer, HDFComparator
from tardisbase.testing.regression_comparison.compare.visualization import SpectrumSolverComparator, generate_comparison_graph

class ReferenceComparer:

    def __init__(self, ref1_hash: str | None = None, ref2_hash: str | None = None,
                 print_path: bool = False, repo_path: str | Path | None = None):
        assert not ((ref1_hash is None) and (ref2_hash is None)), "One hash can not be None"
        self.ref1_hash = ref1_hash
        self.ref2_hash = ref2_hash
        self.print_path = print_path
        self.repo_path = repo_path
        self.test_table_dict = {}
        self.file_manager = FileManager(repo_path)
        self.file_setup = None
        self.diff_analyzer = None
        self.hdf_comparator = None

    def setup(self) -> None:
        self.file_manager.setup()
        self.file_setup = FileSetup(self.file_manager, self.ref1_hash, self.ref2_hash)
        self.diff_analyzer = DiffAnalyzer(self.file_manager)
        self.hdf_comparator = HDFComparator(print_path=self.print_path)
        self.file_setup.setup()
        self.ref1_path = self.file_manager.get_temp_path("ref1")
        self.ref2_path = self.file_manager.get_temp_path("ref2")
        self.dcmp = dircmp(self.ref1_path, self.ref2_path)

    def teardown(self) -> None:
        self.file_manager.teardown()

    def compare(self, print_diff: bool = False) -> None:
        if print_diff:
            self.diff_analyzer.print_diff_files(self.dcmp)
        self.compare_hdf_files()
        
        for name, results in self.test_table_dict.items():
            ref1_keys = set(results.get("ref1_keys", []))
            ref2_keys = set(results.get("ref2_keys", []))
            results["added_keys"] = list(ref2_keys - ref1_keys)
            results["deleted_keys"] = list(ref1_keys - ref2_keys)

    def compare_hdf_files(self) -> None:
        for root, _, files in os.walk(self.ref1_path):
            for file in files:
                file_path = Path(file)
                if file_path.suffix in ('.h5', '.hdf5'):
                    rel_path = Path(root).relative_to(self.ref1_path)
                    ref2_file_path = self.ref2_path / rel_path / file
                    if ref2_file_path.exists():
                        self.summarise_changes_hdf(file, root, ref2_file_path.parent)

    def summarise_changes_hdf(self, name: str, path1: str | Path, path2: str | Path) -> None:
        self.test_table_dict[name] = {
            "path": get_relative_path(path1, self.file_manager.temp_dir / "ref1")
        }
        results = self.hdf_comparator.summarise_changes_hdf(name, path1, path2)
        self.test_table_dict[name].update(results)
        
        self.test_table_dict[name]["ref1_keys"] = results.get("ref1_keys", [])
        self.test_table_dict[name]["ref2_keys"] = results.get("ref2_keys", [])

    def display_hdf_comparison_results(self) -> None:
        for name, results in self.test_table_dict.items():
            print(f"Results for {name}:")
            for key, value in results.items():
                print(f"  {key}: {value}")
            print()

    def get_temp_dir(self) -> Path:
        return self.file_manager.temp_dir

    def generate_graph(self, option: str) -> None:
        print("Generating graph with updated hovertemplate")
        if option not in ["different keys same name", "different keys"]:
            raise ValueError("Invalid option. Choose 'different keys same name' or 'different keys'.")

        data = []
        for name, results in self.test_table_dict.items():
            if option == "different keys same name":
                value = results.get("identical_keys_diff_data", 0)
                if value > 0:
                    diff_data = results["identical_name_different_data_dfs"]
                    keys = list(diff_data.keys())
                    rel_diffs = []
                    for key in keys:
                        df = diff_data[key]
                        try:
                            values = df.abs().fillna(0).values
                            max_diff = float(np.nanmax(values))
                            if not np.isfinite(max_diff):
                                max_diff = 0.0
                        except Exception as e:
                            print(f"Error calculating diff for key {key}: {e}")
                            max_diff = 0.0
                        rel_diffs.append(max_diff)
                    data.append((name, value, keys, rel_diffs))
            else:  # "different keys"
                value = results.get("different_keys", 0)
                if value > 0:
                    added = list(results.get("added_keys", []))
                    deleted = list(results.get("deleted_keys", []))
                    data.append((name, value, added, deleted))

        generate_comparison_graph(data, option, self.ref1_hash, self.ref2_hash)

    def compare_testspectrumsolver_hdf(self, custom_ref1_path: str | Path | None = None,
                                     custom_ref2_path: str | Path | None = None) -> None:
        ref1_path = custom_ref1_path or Path(self.ref1_path) / "tardis/spectrum/tests/test_spectrum_solver/test_spectrum_solver/TestSpectrumSolver.h5"
        ref2_path = custom_ref2_path or Path(self.ref2_path) / "tardis/spectrum/tests/test_spectrum_solver/test_spectrum_solver/TestSpectrumSolver.h5"

        plot_dir = None
        if os.environ.get('SAVE_COMP_IMG') == '1':
            short_ref1 = self.ref1_hash[:6] if self.ref1_hash else "current"
            short_ref2 = self.ref2_hash[:6] if self.ref2_hash else "current"
            plot_dir = Path(f"comparison_plots_{short_ref2}_new_{short_ref1}_old")
            plot_dir.mkdir(exist_ok=True)
        
        comparator = SpectrumSolverComparator(ref1_path, ref2_path, plot_dir)
        comparator.setup()
        comparator.plot_matplotlib()
        comparator.plot_plotly()