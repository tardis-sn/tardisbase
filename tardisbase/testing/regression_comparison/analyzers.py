from pathlib import Path
from tardisbase.testing.regression_comparison.util import color_print
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class DiffAnalyzer:
    """
    A class for analyzing and displaying differences between directory structures.

    This class provides methods to visualize directory differences using tree-like
    displays with colored output and detailed file comparison reports.

    Parameters
    ----------
    file_manager : tardisbase.testing.regression_comparison.file_manager.FileManager
        A file manager object that handles file operations and provides access
        to temporary directory paths.

    Attributes
    ----------
    file_manager : object
        The file manager instance used for path operations.
    """

    def __init__(self, file_manager):
        self.file_manager = file_manager

    def display_diff_tree(self, dcmp, prefix=""):
        """
        Display a tree-like visualization of directory differences.

        This method recursively traverses directory comparison objects and
        displays added, removed, and modified files/directories using colored
        symbols in a tree structure.

        Parameters
        ----------
        dcmp : filecmp.dircmp
            A directory comparison object from the filecmp module containing
            the comparison results between two directories.
        prefix : str, optional
            String prefix for indentation in the tree display, by default ''.
            Used internally for recursive calls to maintain proper indentation.

        Notes
        -----
        Uses the following symbols:\n
        - '−' (red) for items only in the left directory\n
        - '+' (green) for items only in the right directory\n
        - '✱' (yellow) for files that differ between directories\n
        - '├' (blue) for common subdirectories\n
        - '│ ' for tree indentation in subdirectories\n
        """
        for item in sorted(dcmp.left_only):
            path = Path(dcmp.left) / item
            self._print_item(f"{prefix}−", item, "red", path.is_dir())

        for item in sorted(dcmp.right_only):
            path = Path(dcmp.right) / item
            self._print_item(f"{prefix}+", item, "green", path.is_dir())

        for item in sorted(dcmp.diff_files):
            self._print_item(f"{prefix}✱", item, "yellow")

        for item in sorted(dcmp.common_dirs):
            self._print_item(f"{prefix}├", item, "blue", True)
            subdir = getattr(dcmp, "subdirs")[item]
            self.display_diff_tree(subdir, prefix + "│ ")

    def _print_item(self, symbol, item, color, is_dir=False):
        """
        Print a single item with colored formatting.

        Parameters
        ----------
        symbol : str
            The symbol to display before the item name (e.g., '−', '+', '✱').
        item : str
            The name of the file or directory item.
        color : str
            The color name for the output (e.g., 'red', 'green', 'yellow', 'blue').
        is_dir : bool, optional
            Whether the item is a directory, by default False.
            If True, appends '/' to the item name.
        """
        dir_symbol = "/" if is_dir else ""
        color_print(f"{symbol} {item}{dir_symbol}", color)

    def print_diff_files(self, dcmp):
        """
        Print detailed information about file differences between directories.

        Parameters
        ----------
        dcmp : filecmp.dircmp
            A directory comparison object containing the results of comparing
            two directory structures.
        """
        dcmp.right = Path(dcmp.right)
        dcmp.left = Path(dcmp.left)

        self._print_new_files(dcmp.right_only, dcmp.right, "ref1")
        self._print_new_files(dcmp.left_only, dcmp.left, "ref2")
        self._print_modified_files(dcmp)

        for sub_dcmp in dcmp.subdirs.values():
            self.print_diff_files(sub_dcmp)

    def _print_new_files(self, files, path, ref):
        """
        Print information about new files found in one directory but not the other.

        Parameters
        ----------
        files : list
            List of file names that are present in only one of the compared directories.
        path : Path
            The path to the directory containing the new files.
        ref : str
            Reference name for the directory (e.g., "ref1", "ref2") used in output.
        """
        for item in files:
            if Path(path, item).is_file():
                print(f"New file detected inside {ref}: {item}")
                print(f"Path: {Path(path, item)}")
                print()

    def _print_modified_files(self, dcmp):
        """
        Print information about files that exist in both directories but differ.

        Parameters
        ----------
        dcmp : filecmp.dircmp
            Directory comparison object containing information about files
            that have the same name but different content.
        """
        for name in dcmp.diff_files:
            print(f"Modified file found {name}")
            left = self._get_relative_path(dcmp.left)
            right = self._get_relative_path(dcmp.right)
            if left == right:
                print(f"Path: {left}")
            print()

    def _get_relative_path(self, path):
        """
        Get the relative path of a given path with respect to the temporary directory.

        Parameters
        ----------
        path : str or Path
            The absolute path to convert to a relative path.

        Returns
        -------
        str
            The relative path string if the path is within temp_dir,
            otherwise returns the full path as a string.
        """
        try:
            return str(Path(path).relative_to(self.file_manager.temp_dir))
        except ValueError:
            # If the path is not relative to temp_dir, return the full path
            return str(path)


class HDFComparator:
    """
    A class for comparing HDF5 files and analyzing differences between datasets.

    This class provides functionality to compare HDF5 files, identify differences
    in keys and data, and display statistical summaries and visualizations of
    the differences found.

    Parameters
    ----------
    print_path : bool, optional
        Whether to print file paths in the output, by default False.
    """

    def __init__(self, print_path=False):
        self.print_path = print_path

    def summarise_changes_hdf(self, name, path1, path2):
        """
        Compare two HDF5 files and summarize the differences between them.

        This method performs a comparison of HDF5 files, analyzing
        both structural differences (different keys) and data differences
        (same keys with different values).

        Parameters
        ----------
        name : str
            The name of the HDF5 file to compare (should exist in both paths).
        path1 : str or Path
            Path to the first directory containing the HDF5 file.
        path2 : str or Path
            Path to the second directory containing the HDF5 file.

        Returns
        -------
        dict or None
            A dictionary containing comparison results if differences are found:

            - 'different_keys' : int
                Number of keys that differ between the files
            - 'identical_keys' : int
                Number of keys that are completely identical
            - 'identical_keys_diff_data' : int
                Number of keys with same name but different data
            - 'identical_name_different_data_dfs' : dict
                Dictionary mapping key names to difference DataFrames
            - 'ref1_keys' : list
                List of all keys in the first file
            - 'ref2_keys' : list
                List of all keys in the second file
            - 'added_keys' : list
                Keys present only in the second file
            - 'deleted_keys' : list
                Keys present only in the first file

            Returns None if no differences are found.

        Notes
        -----
        The method prints detailed summaries and visualizations when differences
        are detected. For data differences, it calculates relative differences
        as (ref1 - ref2) / ref1 and displays heatmaps.
        """
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
                    identical_name_different_data_dfs[item] = (
                        ref1[item] - ref2[item]
                    ) / ref1[item]
                    self._compare_and_display_differences(
                        ref1[item], ref2[item], item, name, path1, path2
                    )
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
            print(
                f"Number of keys with different names in ref1 and ref2: {different_keys}"
            )
            if added_keys:
                print(f"Keys added in ref2(k2-k1): {sorted(added_keys)}")
            if deleted_keys:
                print(f"Keys deleted from ref1(k1-k2): {sorted(deleted_keys)}")
            print(
                f"Number of keys with same name but different data in ref1 and ref2: {len(identical_name_different_data)}"
            )
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
            "deleted_keys": list(deleted_keys),
        }

    def _compare_and_display_differences(self, df1, df2, item, name, path1, path2):
        """
        Compare two DataFrames and display detailed difference analysis.

        This method calculates both absolute and relative differences between
        DataFrames and provides warnings for significant differences that exceed
        floating-point precision limits.

        Parameters
        ----------
        df1 : pandas.DataFrame
            The first DataFrame to compare.
        df2 : pandas.DataFrame
            The second DataFrame to compare.
        item : str
            The key name of the item being compared.
        name : str
            The name of the HDF5 file containing the data.
        path1 : str or Path
            Path to the first file.
        path2 : str or Path
            Path to the second file.

        Notes
        -----
        The method uses a floating-point uncertainty threshold of 1e-14 to
        distinguish between numerical precision errors and actual differences.
        When significant differences are detected, warnings are logged with
        the maximum relative difference percentage.
        """
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
            print(
                f"Visualising {'Absolute' if diff_type == 'abs' else 'Relative'} Differences"
            )
            self._display_difference(diff)

        if self.print_path:
            if path1 != path2:
                print(f"Path1: {path1}")
                print(f"Path2: {path2}")
            else:
                print(f"Path: {path1}")

    def _display_difference(self, diff):
        """
        Display a formatted visualization of DataFrame differences.

        This method creates a styled DataFrame showing mean and maximum
        difference values with a red color gradient background for
        easy visual interpretation.

        Parameters
        ----------
        diff : pandas.DataFrame or pandas.Series
            The difference data to visualize. Can be either absolute or
            relative differences calculated from DataFrame comparisons.

        Notes
        -----
        The output uses pandas styling with:
        - Scientific notation formatting (2 significant digits)
        - Red color gradient background ('Reds' colormap)
        - Automatic handling of Series and MultiIndex data structures

        For MultiIndex DataFrames, the index is reset before processing.
        Series data is converted to a single-row DataFrame.
        """
        with pd.option_context("display.max_rows", 100, "display.max_columns", 10):
            if isinstance(diff, pd.Series):
                diff = pd.DataFrame([diff.mean(), diff.max()], index=["mean", "max"])
            elif isinstance(diff.index, pd.core.indexes.multi.MultiIndex):
                diff = diff.reset_index(drop=True)

            diff = pd.DataFrame([diff.mean(), diff.max()], index=["mean", "max"])
            display(diff.style.format("{:.2g}".format).background_gradient(cmap="Reds"))
