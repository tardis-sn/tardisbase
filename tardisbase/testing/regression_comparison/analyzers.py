from pathlib import Path
from tardisbase.testing.regression_comparison.util import color_print
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class DiffAnalyzer:
    def __init__(self, file_manager):
        self.file_manager = file_manager

    def display_diff_tree(self, dcmp, prefix=''):
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

    def _print_item(self, symbol, item, color, is_dir=False):
        dir_symbol = '/' if is_dir else ''
        color_print(f"{symbol} {item}{dir_symbol}", color)

    def print_diff_files(self, dcmp):
        dcmp.right = Path(dcmp.right)
        dcmp.left = Path(dcmp.left)
        
        self._print_new_files(dcmp.right_only, dcmp.right, "ref1")
        self._print_new_files(dcmp.left_only, dcmp.left, "ref2")
        self._print_modified_files(dcmp)

        for sub_dcmp in dcmp.subdirs.values():
            self.print_diff_files(sub_dcmp)

    def _print_new_files(self, files, path, ref):
        for item in files:
            if Path(path, item).is_file():
                print(f"New file detected inside {ref}: {item}")
                print(f"Path: {Path(path, item)}")
                print()

    def _print_modified_files(self, dcmp):
        for name in dcmp.diff_files:
            print(f"Modified file found {name}")
            left = self._get_relative_path(dcmp.left)
            right = self._get_relative_path(dcmp.right)
            if left == right:
                print(f"Path: {left}")
            print()

    def _get_relative_path(self, path):
        try:
            return str(Path(path).relative_to(self.file_manager.temp_dir))
        except ValueError:
            # If the path is not relative to temp_dir, return the full path
            return str(path)

class HDFComparator:
    def __init__(self, print_path=False):
        self.print_path = print_path

    def summarise_changes_hdf(self, name, path1, path2):
        ref1 = pd.HDFStore(Path(path1) / name)
        ref2 = pd.HDFStore(Path(path2) / name)
        k1, k2 = set(ref1.keys()), set(ref2.keys())
        
        different_keys = len(k1 ^ k2)
        identical_items = []
        identical_name_different_data = []
        identical_name_different_data_dfs = {}

        # Calculate added and deleted keys
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
                print(f"Error comparing item: {item}")
                print(e)

        ref1.close()
        ref2.close()

        # Only return results if there are differences
        if different_keys > 0 or len(identical_name_different_data) > 0:
            print("\n" + "=" * 50)  # Add a separator line
            print(f"Summary for {name}:")
            print(f"Total number of keys- in ref1: {len(k1)}, in ref2: {len(k2)}")
            print(f"Number of keys with different names in ref1 and ref2: {different_keys}")
            if added_keys:
                print(f"Keys added in ref2(k2-k1): {sorted(added_keys)}")
            if deleted_keys:
                print(f"Keys deleted from ref1(k1-k2): {sorted(deleted_keys)}")
            print(f"Number of keys with same name but different data in ref1 and ref2: {len(identical_name_different_data)}")
            print(f"Number of totally same keys: {len(identical_items)}")
            print("=" * 50)  # Add another separator line after the summary
            print()

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

    def _compare_and_display_differences(self, df1, df2, item, name, path1, path2):
        abs_diff = np.fabs(df1 - df2)
        rel_diff = abs_diff / np.maximum(np.fabs(df1), np.fabs(df2))

        # Check for differences larger than floating point uncertainty
        FLOAT_UNCERTAINTY = 1e-14
        max_rel_diff = np.nanmax(rel_diff)  # Using nanmax to handle NaN values

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


    def _display_difference(self, diff):
        with pd.option_context('display.max_rows', 100, 'display.max_columns', 10):
            if isinstance(diff, pd.Series):
                diff = pd.DataFrame([diff.mean(), diff.max()], index=['mean', 'max'])
            elif isinstance(diff.index, pd.core.indexes.multi.MultiIndex):
                diff = diff.reset_index(drop=True)
            
            diff = pd.DataFrame([diff.mean(), diff.max()], index=['mean', 'max'])
            display(diff.style.format('{:.2g}'.format).background_gradient(cmap='Reds'))
