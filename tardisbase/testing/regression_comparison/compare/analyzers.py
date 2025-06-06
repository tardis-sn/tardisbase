from filecmp import dircmp
from pathlib import Path
import numpy as np
import pandas as pd
import logging

from tardisbase.testing.regression_comparison.compare.utils import color_print, get_relative_path, FileManager, FLOAT_UNCERTAINTY

logger = logging.getLogger(__name__)

class DiffAnalyzer:

    def __init__(self, file_manager: FileManager):
        self.file_manager = file_manager

    def display_diff_tree(self, dcmp: dircmp, prefix: str = '') -> None:
        for item in sorted(dcmp.left_only):
            path = Path(dcmp.left) / item
            self._print_item(f'{prefix}−', item, 'red', path.is_dir())

        for item in sorted(dcmp.right_only):
            path = Path(dcmp.right) / item
            self._print_item(f'{prefix}+', item, 'green', path.is_dir())

        for item in sorted(dcmp.diff_files):
            self._print_item(f'{prefix}✱', item, 'yellow')

        for item in sorted(dcmp.common_dirs):
            self._print_item(f'{prefix}├', item, 'blue', True)
            subdir = getattr(dcmp, 'subdirs')[item]
            self.display_diff_tree(subdir, prefix + '│ ')

    def _print_item(self, symbol: str, item: str, color: str, is_dir: bool = False) -> None:
        dir_symbol = '/' if is_dir else ''
        color_print(f"{symbol} {item}{dir_symbol}", color)

    def print_diff_files(self, dcmp: dircmp) -> None:
        dcmp.right = Path(dcmp.right)
        dcmp.left = Path(dcmp.left)
        
        self._print_new_files(dcmp.right_only, dcmp.right, "ref1")
        self._print_new_files(dcmp.left_only, dcmp.left, "ref2")
        self._print_modified_files(dcmp)

        for sub_dcmp in dcmp.subdirs.values():
            self.print_diff_files(sub_dcmp)

    def _print_new_files(self, files: list[str], path: Path, ref: str) -> None:
        for item in files:
            if Path(path, item).is_file():
                print(f"New file detected inside {ref}: {item}")
                print(f"Path: {Path(path, item)}")
                print()

    def _print_modified_files(self, dcmp: dircmp) -> None:
        for name in dcmp.diff_files:
            print(f"Modified file found {name}")
            left = self._get_relative_path(dcmp.left)
            right = self._get_relative_path(dcmp.right)
            if left == right:
                print(f"Path: {left}")
            print()

    def _get_relative_path(self, path: Path | str) -> str:
        try:
            return get_relative_path(path, self.file_manager.temp_dir)
        except ValueError:
            return str(path)

class HDFComparator:

    def __init__(self, print_path: bool = False):
        self.print_path = print_path

    def summarise_changes_hdf(self, name: str, path1: str | Path, path2: str | Path) -> dict:
        ref1 = pd.HDFStore(Path(path1) / name)
        ref2 = pd.HDFStore(Path(path2) / name)
        k1, k2 = set(ref1.keys()), set(ref2.keys())
        
        different_keys = len(k1 ^ k2)
        identical_items = []
        identical_name_different_data = []
        identical_name_different_data_dfs = {}

        added_keys = k2 - k1
        deleted_keys = k1 - k2

        for item in k1 & k2:
            try:
                if ref1[item].equals(ref2[item]):
                    identical_items.append(item)
                else:
                    identical_name_different_data.append(item)
                    identical_name_different_data_dfs[item] = (ref1[item] - ref2[item]) / ref1[item]
                    self._compare_and_display_differences(ref1[item], ref2[item], item, name, path1, path2)
            except Exception as e:
                logger.error(f"Error comparing item: {item}")
                logger.error(str(e))

        ref1.close()
        ref2.close()

        if different_keys > 0 or len(identical_name_different_data) > 0:
            self._print_summary(name, k1, k2, different_keys, added_keys, deleted_keys, 
                              identical_name_different_data, identical_items)

        return {
            "different_keys": different_keys,
            "identical_keys": len(identical_items),
            "identical_keys_diff_data": len(identical_name_different_data),
            "identical_name_different_data_dfs": identical_name_different_data_dfs,
            "ref1_keys": list(k1),
            "ref2_keys": list(k2),
            "added_keys": list(added_keys),
            "deleted_keys": list(deleted_keys)
        }

    def _compare_and_display_differences(self, df1: pd.DataFrame, df2: pd.DataFrame, 
                                       item: str, name: str, path1: Path, path2: Path) -> None:
        abs_diff = np.fabs(df1 - df2)
        rel_diff = abs_diff / np.maximum(np.fabs(df1), np.fabs(df2))
        max_rel_diff = np.nanmax(rel_diff) 

        if max_rel_diff > FLOAT_UNCERTAINTY:
            logger.warning(
                f"Significant difference detected in {name}, key={item}\n"
                f"Maximum relative difference: {max_rel_diff:.2e} "
                f"(Versions differ by {max_rel_diff*100:.2e}%)"
            )

        print(f"Displaying heatmap for key {item} in file {name} \r")
        for diff_type, diff in zip(["abs", "rel"], [abs_diff, rel_diff]):
            print(f"Visualising {'Absolute' if diff_type == 'abs' else 'Relative'} Differences")
            self._display_difference(diff)

        if self.print_path:
            if path1 != path2:
                print(f"Path1: {path1}")
                print(f"Path2: {path2}")
            else:
                print(f"Path: {path1}")

    def _display_difference(self, diff: pd.DataFrame | pd.Series) -> None:
        with pd.option_context('display.max_rows', 100, 'display.max_columns', 10):
            if isinstance(diff, pd.Series):
                diff = pd.DataFrame([diff.mean(), diff.max()], index=['mean', 'max'])
            elif isinstance(diff.index, pd.core.indexes.multi.MultiIndex):
                diff = diff.reset_index(drop=True)
            
            diff = pd.DataFrame([diff.mean(), diff.max()], index=['mean', 'max'])
            display(diff.style.format('{:.2g}'.format).background_gradient(cmap='Reds'))
            
    def _print_summary(self, name: str, k1: set, k2: set, different_keys: int,
                      added_keys: set, deleted_keys: set, identical_name_different_data: list,
                      identical_items: list) -> None:
        """Print comparison summary."""
        print("\n" + "=" * 50)
        print(f"Summary for {name}:")
        print(f"Total number of keys- in ref1: {len(k1)}, in ref2: {len(k2)}")
        print(f"Number of keys with different names in ref1 and ref2: {different_keys}")
        if added_keys:
            print(f"Keys added in ref2(k2-k1): {sorted(added_keys)}")
        if deleted_keys:
            print(f"Keys deleted from ref1(k1-k2): {sorted(deleted_keys)}")
        print(f"Number of keys with same name but different data in ref1 and ref2: {len(identical_name_different_data)}")
        print(f"Number of totally same keys: {len(identical_items)}")
        print("=" * 50)
        print() 