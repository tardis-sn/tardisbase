"""
Shared file utilities for regression comparison modules.

This module provides centralized file operations to reduce code duplication
across the regression comparison package.
"""

import logging
from pathlib import Path
from tardisbase.testing.regression_comparison.config import ERROR_MESSAGES
from tardisbase.testing.regression_comparison.git_utils import is_file_modified, get_file_change_details


logger = logging.getLogger(__name__)


def get_h5_files(path, relative_to=None):
    """
    Get all .h5 and .hdf5 files from a given path.

    This function centralizes the file discovery logic used in multiple modules.

    Parameters
    ----------
    path : str or Path
        Path to search for HDF5 files
    relative_to : str or Path, optional
        Base path to make paths relative to. If None, returns absolute paths

    Returns
    -------
    set
        Set of file paths (relative or absolute)
    """
    files = set()
    path = Path(path)

    if not path.exists():
        logger.warning(ERROR_MESSAGES["file_not_found"].format(file=str(path)))
        return files

    try:
        for file_path in path.rglob("*.h5"):
            if file_path.suffix in (".h5", ".hdf5"):
                if relative_to:
                    try:
                        rel_path = file_path.relative_to(relative_to)
                        files.add(str(rel_path))
                    except ValueError:
                        # If the path is not relative to the base, use the full path
                        files.add(str(file_path))
                else:
                    files.add(str(file_path))

        # Also search for .hdf5 extension explicitly
        for file_path in path.rglob("*.hdf5"):
            if relative_to:
                try:
                    rel_path = file_path.relative_to(relative_to)
                    files.add(str(rel_path))
                except ValueError:
                    files.add(str(file_path))
            else:
                files.add(str(file_path))

    except Exception as e:
        logger.error(f"Error discovering HDF5 files in {path}: {str(e)}")

    return files


def discover_and_compare_h5_files(ref1_path, ref2_path=None, callback=None):
    """
    Discover HDF5 files and optionally compare them between two directories.

    This function centralizes the HDF5 file discovery and comparison logic
    used in compare.py. It supports both single directory cataloging and
    two-directory comparison.

    Parameters
    ----------
    ref1_path : str or Path
        First reference directory path
    ref2_path : str or Path, optional
        Second reference directory path. If None, only catalogs ref1_path
    callback : callable, optional
        Function to call for each matching file pair. Should accept
        (filename, path1, path2) arguments

    Returns
    -------
    list
        List of discovered HDF5 files (relative paths)
    """
    import os

    ref1_path = Path(ref1_path)
    discovered_files = []

    if ref2_path and callback:
        # Compare files in both directories (compare.py style)
        ref2_path = Path(ref2_path)
        for root, _, files in os.walk(ref1_path):
            for file in files:
                file_path = Path(file)
                if file_path.suffix in (".h5", ".hdf5"):
                    rel_path = Path(root).relative_to(ref1_path)
                    ref2_file_path = ref2_path / rel_path / file
                    if ref2_file_path.exists():
                        callback(file, root, ref2_file_path.parent)
                        discovered_files.append(str(rel_path / file))
    else:
        # Single directory cataloging
        for root, _, files in os.walk(ref1_path):
            for file in files:
                file_path = Path(file)
                if file_path.suffix in (".h5", ".hdf5"):
                    rel_path = Path(root).relative_to(ref1_path)
                    full_rel_path = rel_path / file
                    discovered_files.append(str(full_rel_path))
                    if not ref2_path:  # Only print if cataloging mode
                        print(f"Found HDF5 file: {Path(root) / file}")

        # Handle ref2_path cataloging if provided but no callback
        if ref2_path and not callback:
            ref2_path = Path(ref2_path)
            print("Second directory HDF5 files:")
            for root, _, files in os.walk(ref2_path):
                for file in files:
                    file_path = Path(file)
                    if file_path.suffix in (".h5", ".hdf5"):
                        print(f"Found HDF5 file: {Path(root) / file}")

    return discovered_files


def extract_h5_changes_from_dircmp(dcmp, base_path=""):
    """
    Extract HDF5 file changes from dircmp results.

    This function centralizes the dircmp-based file change detection
    logic used in visualize_files.py.

    Parameters
    ----------
    dcmp : filecmp.dircmp
        Directory comparison object
    base_path : str, optional
        Base path for building relative file paths

    Returns
    -------
    dict
        Dictionary mapping file paths to change types (+, -, *, •)
    """
    import os

    changes = {}

    def process_dcmp_level(dcmp_obj, current_base_path=""):
        # Added files (only in right/current)
        for f in dcmp_obj.right_only:
            if f.endswith(('.h5', '.hdf5')):
                file_path = os.path.join(current_base_path, f) if current_base_path else f
                changes[file_path] = '+'

        # Deleted files (only in left/previous)
        for f in dcmp_obj.left_only:
            if f.endswith(('.h5', '.hdf5')):
                file_path = os.path.join(current_base_path, f) if current_base_path else f
                changes[file_path] = '-'

        # Modified files
        for f in dcmp_obj.diff_files:
            if f.endswith(('.h5', '.hdf5')):
                file_path = os.path.join(current_base_path, f) if current_base_path else f
                changes[file_path] = '*'

        # Unchanged files
        for f in dcmp_obj.same_files:
            if f.endswith(('.h5', '.hdf5')):
                file_path = os.path.join(current_base_path, f) if current_base_path else f
                changes[file_path] = '•'

        # Recurse into subdirectories
        for subdir, sub_dcmp in dcmp_obj.subdirs.items():
            sub_path = os.path.join(current_base_path, subdir) if current_base_path else subdir
            process_dcmp_level(sub_dcmp, sub_path)

    process_dcmp_level(dcmp, base_path)
    return changes


def categorize_files(file_changes):
    """
    Categorize files into changed and unchanged based on change types.
    
    This function centralizes the file categorization logic used in multiple modules.
    
    Parameters
    ----------
    file_changes : dict
        Dictionary mapping commits to dictionaries of file paths and change types
        
    Returns
    -------
    tuple
        (all_files, changed_files, unchanged_files) sets
    """
    all_files = set()
    changed_files = set()
    
    # Collect all files and identify changed ones
    for changes in file_changes.values():
        all_files.update(changes.keys())
        for file_path, change_type in changes.items():
            if change_type in ['+', '-', '*']:  # Added, deleted, or modified
                changed_files.add(file_path)
    
    # Remaining files are unchanged
    unchanged_files = all_files - changed_files
    
    return all_files, changed_files, unchanged_files


def compare_file_sets(prev_files, current_files, prev_commit, current_commit, repo_path, is_modified_func=None):
    """
    Compare two sets of files to determine changes.
    
    This function centralizes the file comparison logic used in multiple modules.
    
    Parameters
    ----------
    prev_files : set
        Set of files from the previous commit
    current_files : set
        Set of files from the current commit
    prev_commit : str
        Previous commit hash
    current_commit : str
        Current commit hash
    repo_path : str or Path
        Path to the repository
    is_modified_func : callable, optional
        Function to check if a file was modified. If None, uses git_utils.is_file_modified
        
    Returns
    -------
    dict
        Dictionary mapping file paths to change types
    dict
        Dictionary mapping file paths to change details
    """
    
    if is_modified_func is None:
        is_modified_func = lambda f: is_file_modified(f, prev_commit, current_commit, repo_path)
    
    changes = {}
    details = {}
    all_files = prev_files | current_files
    
    for file_path in all_files:
        if file_path not in prev_files:
            # File was added
            changes[file_path] = '+'
            details[file_path] = "File added"
        elif file_path not in current_files:
            # File was deleted
            changes[file_path] = '-'
            details[file_path] = "File deleted"
        elif is_modified_func(file_path):
            # File was modified
            changes[file_path] = '*'
            details[file_path] = get_file_change_details(file_path, prev_commit, current_commit, repo_path)
        else:
            # File is unchanged
            changes[file_path] = '•'
            details[file_path] = "No changes"
    
    return changes, details
