from filecmp import dircmp
from pathlib import Path
import os
import numpy as np
import plotly.graph_objects as go
import random
import plotly.colors as pc
from tardisbase.testing.regression_comparison.util import get_relative_path
from tardisbase.testing.regression_comparison.file_manager import FileManager, FileSetup
from tardisbase.testing.regression_comparison.analyzers import (
    DiffAnalyzer,
    HDFComparator,
)
from tardisbase.testing.regression_comparison.visualization import (
    SpectrumSolverComparator,
)
from tardisbase.testing.regression_comparison.file_utils import discover_and_compare_h5_files
from tardisbase.testing.regression_comparison import CONFIG
import logging
from tardisbase.testing.regression_comparison.run_tests import run_tests

logger = logging.getLogger(__name__)


class ReferenceComparer:
    """
    A class for comparing reference data between two regression data commits or direct paths.

    This class provides functionality to compare HDF5 files, generate visualizations,
    and analyze differences between two regression data repo commits or direct directory paths.
    It supports directory comparison, HDF5 file analysis, and plot generation.

    Parameters
    ----------
    ref1_hash : str, optional
        Git commit hash for the first reference dataset, by default None.
        Cannot be used together with refpath1.
    ref2_hash : str, optional
        Git commit hash for the second reference dataset, by default None.
        Cannot be used together with refpath2.
    refpath1 : str or Path, optional
        Direct path to the first reference directory, by default None.
        Cannot be used together with ref1_hash.
    refpath2 : str or Path, optional
        Direct path to the second reference directory, by default None.
        Cannot be used together with ref2_hash.
    print_path : bool, optional
        Whether to print file paths in comparison output, by default False.
    repo_path : str or Path, optional
        Path to the repository containing reference data, by default None.
        If None, uses the path specified in CONFIG['compare_path'].
        Only used when using git hashes.

    Raises
    ------
    AssertionError
        If neither git hashes nor direct paths are provided, or if both are provided.
    """

    def __init__(
        self,
        ref1_hash=None,
        ref2_hash=None,
        refpath1=None,
        refpath2=None,
        print_path=False,
        repo_path=None,
        tardis_repo_path=None,
        branch="master",
        n=2,
        target_file="tardis/spectrum/tests/test_spectrum_solver/test_spectrum_solver/TestSpectrumSolver.h5",
        commits_input=None,
        auto_generate_reference=True,
    ):
        # Validation: Either use git hashes OR direct paths, not both
        using_git = (ref1_hash is not None) or (ref2_hash is not None)
        using_paths = (refpath1 is not None) or (refpath2 is not None)

        assert not (
            using_git and using_paths
        ), "Cannot use both git hashes and direct paths"
        assert (
            using_git or using_paths
        ), "Must provide either git hashes or direct paths"

        if using_git:
            assert not (
                (ref1_hash is None) and (ref2_hash is None)
            ), "At least one git hash must be provided"

        if using_paths:
            assert not (
                (refpath1 is None) and (refpath2 is None)
            ), "At least one direct path must be provided"

        self.ref1_hash = ref1_hash
        self.ref2_hash = ref2_hash
        self.refpath1 = Path(refpath1) if refpath1 else None
        self.refpath2 = Path(refpath2) if refpath2 else None
        self.print_path = print_path
        self.repo_path = Path(repo_path) if repo_path else Path(CONFIG["compare_path"])
        self.test_table_dict = {}

        # Initialize components
        self.using_git = using_git
        self.file_manager = FileManager(repo_path) if using_git else None
        self.file_setup = None
        self.diff_analyzer = None
        self.hdf_comparator = None

        # Store reference generation parameters
        self.tardis_repo_path = tardis_repo_path
        self.branch = branch
        self.n = n
        self.target_file = target_file
        self.commits_input = commits_input
        self.auto_generate_reference = auto_generate_reference

        # Initialize reference generation results
        self.processed_commits = None
        self.regression_commits = None
        self.original_head = None
        self.target_file_path = None

        # Auto-generate reference if n > 2 and auto_generate_reference is True
        if self.auto_generate_reference and n > 2 and tardis_repo_path:
            self.generate_reference(auto_mode=True)

    def setup(self):
        """
        Set up all necessary components for reference comparison.

        This method initializes the file manager (if using git), sets up reference files,
        creates analyzer and comparator instances, and establishes directory
        comparison objects. Must be called before performing any comparisons.

        Notes
        -----
        After calling this method, the following attributes will be available:
        - ref1_path : Path to the first reference directory
        - ref2_path : Path to the second reference directory
        - dcmp : Directory comparison object
        - file_setup : Configured FileSetup instance
        - diff_analyzer : Configured DiffAnalyzer instance
        - hdf_comparator : Configured HDFComparator instance
        """
        if self.using_git:
            # Git-based setup
            self.file_manager.setup()
            self.file_setup = FileSetup(
                self.file_manager, self.ref1_hash, self.ref2_hash
            )
            self.diff_analyzer = DiffAnalyzer(self.file_manager)
            self.hdf_comparator = HDFComparator(print_path=self.print_path)
            self.file_setup.setup()
            self.ref1_path = self.file_manager.get_temp_path("ref1")
            self.ref2_path = self.file_manager.get_temp_path("ref2")
        else:
            # Direct path setup
            self.ref1_path = str(self.refpath1) if self.refpath1 else None
            self.ref2_path = str(self.refpath2) if self.refpath2 else None

            # Validate that paths exist
            if self.ref1_path and not Path(self.ref1_path).exists():
                raise FileNotFoundError(
                    f"Reference path 1 does not exist: {self.ref1_path}"
                )
            if self.ref2_path and not Path(self.ref2_path).exists():
                raise FileNotFoundError(
                    f"Reference path 2 does not exist: {self.ref2_path}"
                )

        # Initialize common components
        self.hdf_comparator = HDFComparator(print_path=self.print_path)

        # Set up directory comparison if both paths are available
        if self.ref1_path and self.ref2_path:
            self.dcmp = dircmp(self.ref1_path, self.ref2_path)
        else:
            self.dcmp = None

    def teardown(self):
        """
        Clean up temporary files and directories created during comparison.

        This method should be called after completing all operations
        to ensure proper cleanup of resources. Only needed when using git hashes.
        """
        if self.using_git and self.file_manager:
            self.file_manager.teardown()

    def generate_reference(
        self,
        tardis_repo_path=None,
        branch=None,
        n=None,
        target_file=None,
        commits_input=None,
        auto_mode=False,
    ):
        # Use stored parameters if auto_mode is True and parameters are None
        if auto_mode:
            tardis_repo_path = tardis_repo_path or self.tardis_repo_path
            branch = branch or self.branch
            n = n or self.n
            target_file = target_file or self.target_file
            commits_input = commits_input or self.commits_input

        # Validate required parameters
        if not tardis_repo_path:
            print("Error: tardis_repo_path is required")
            return None, None, None, None

        if n <= 2:
            print("Skipping generate_reference: n <= 2, using standard comparison mode")
            return None, None, None, None

        tardis_path = Path(tardis_repo_path)
        regression_path = Path(self.repo_path)
        target_file_path = regression_path / target_file

        print(f"Starting generate_reference with n={n}")
        print(f"Tardis repo: {tardis_path}")
        print(f"Regression data repo: {regression_path}")
        print(f"Target file: {target_file}")

        # Process commits using the existing git_utils function
        processed_commits, regression_commits, original_head, target_file_path = run_tests(
            tardis_repo_path=tardis_path,
            regression_data_repo_path=regression_path,
            branch=branch,
            target_file=target_file,
            commits_input=commits_input,
            n=n
        )

        print(f"Generated {len(processed_commits)} tardis commits and {len(regression_commits)} regression commits")
        
        # Store the results for potential use in comparison
        self.processed_commits = processed_commits
        self.regression_commits = regression_commits
        self.original_head = original_head
        self.target_file_path = target_file_path

        return processed_commits, regression_commits, original_head, target_file_path

    def compare(self, print_diff=False):
        """
        Perform comparison between regression datasets.

        This method executes the main comparison workflow, including optional
        directory difference printing and HDF5 file comparison. It updates
        the internal test_table_dict with comparison results.

        Parameters
        ----------
        print_diff : bool, optional
            Whether to print detailed directory differences, by default False.
            If True, displays a tree-like view of file differences.
            Only available when using git hashes and both references are available.
        """
        if print_diff and self.diff_analyzer and self.dcmp:
            self.diff_analyzer.print_diff_files(self.dcmp)
        elif print_diff and not self.using_git:
            print("Warning: print_diff is only available when using git hashes")

        self.compare_hdf_files()

        # Update test_table_dict with added and deleted keys
        for name, results in self.test_table_dict.items():
            ref1_keys = set(results.get("ref1_keys", []))
            ref2_keys = set(results.get("ref2_keys", []))
            results["added_keys"] = list(ref2_keys - ref1_keys)
            results["deleted_keys"] = list(ref1_keys - ref2_keys)

    def compare_hdf_files(self):
        """
        Discover and compare all HDF5 files in the reference directories.

        This method uses the centralized file discovery utility to recursively
        walk through the reference directories, identify HDF5 files (.h5, .hdf5),
        and compare them. When both paths are available, it compares files that
        exist in both directories. When only one path is available, it lists all
        HDF5 files in that directory.
        """
        if self.ref1_path and self.ref2_path:
            # Compare files in both directories using centralized utility
            discover_and_compare_h5_files(
                self.ref1_path,
                self.ref2_path,
                callback=self.summarise_changes_hdf
            )
        elif self.ref1_path:
            # Only ref1 available - just catalog the files
            print("Only ref1_path provided. Cataloging HDF5 files:")
            discover_and_compare_h5_files(self.ref1_path)
        elif self.ref2_path:
            # Only ref2 available - just catalog the files
            print("Only ref2_path provided. Cataloging HDF5 files:")
            discover_and_compare_h5_files(self.ref2_path)

    def summarise_changes_hdf(self, name, path1, path2):
        """
        Analyze and store changes for a specific HDF5 file pair.

        This method performs detailed comparison of an HDF5 file between two
        reference directories and stores the results in the internal test_table_dict.

        Parameters
        ----------
        name : str
            Name of the HDF5 file to compare.
        path1 : str or Path
            Path to the directory containing the first reference file.
        path2 : str or Path
            Path to the directory containing the second reference file.

        Notes
        -----
        The results are stored in test_table_dict[name] and include:
        - Relative path information (when using git)
        - All comparison results from HDFComparator
        - Lists of keys from both reference files
        - Summary statistics about differences
        """
        if self.using_git:
            self.test_table_dict[name] = {
                "path": get_relative_path(path1, self.file_manager.temp_dir / "ref1")
            }
        else:
            self.test_table_dict[name] = {
                "path": str(
                    Path(path1).relative_to(self.ref1_path) if self.ref1_path else path1
                )
            }

        results = self.hdf_comparator.summarise_changes_hdf(name, path1, path2)
        self.test_table_dict[name].update(results)

        # Store keys for both references
        self.test_table_dict[name]["ref1_keys"] = results.get("ref1_keys", [])
        self.test_table_dict[name]["ref2_keys"] = results.get("ref2_keys", [])

    def display_hdf_comparison_results(self):
        """
        Print a formatted summary of all HDF5 comparison results.

        This method provides a comprehensive overview of comparison results
        for all HDF5 files that were analyzed, displaying key-value pairs
        for each file's comparison statistics.

        Notes
        -----
        The output includes information such as:\n
        - Number of different keys\n
        - Identical keys count\n
        - Keys with same name but different data\n
        - File paths and reference key lists\n
        """
        for name, results in self.test_table_dict.items():
            print(f"Results for {name}:")
            for key, value in results.items():
                print(f"  {key}: {value}")
            print()

    def get_temp_dir(self):
        """
        Get the temporary directory path used for file operations.

        Returns
        -------
        Path or None
            The temporary directory path managed by the file manager when using git,
            or None when using direct paths.
        """
        return self.file_manager.temp_dir if self.using_git else None

    def generate_graph(self, option):
        """
        Generate interactive visualizations of comparison results.

        This method creates Plotly bar charts to visualize differences between
        reference datasets, supporting two types of comparisons: keys with same
        names but different data, and structural key differences.

        Parameters
        ----------
        option : str
            Type of comparison to visualize. Must be one of:
            - "different keys same name" : Shows keys with identical names but different data
            - "different keys" : Shows structural differences (added/deleted keys)

        Returns
        -------
        plotly.graph_objects.Figure or None
            Interactive Plotly figure showing the comparison results.
            Returns None if no data matches the specified option.

        Raises
        ------
        ValueError
            If option is not one of the supported values.

        Notes
        -----
        For "different keys same name" option:
        - Bar colors represent relative difference magnitude using blue color scale
        - Hover information includes maximum relative differences and percentages
        - Handles NaN and infinite values gracefully

        For "different keys" option:
        - Green bars represent added keys
        - Red bars represent deleted keys
        - Random color variations within each category for distinction

        If the environment variable SAVE_COMP_IMG is set to '1', the plot will
        be saved as a high-resolution PNG file in a comparison_plots directory.
        """
        print("Generating graph with updated hovertemplate")
        if option not in ["different keys same name", "different keys"]:
            raise ValueError(
                "Invalid option. Choose 'different keys same name' or 'different keys'."
            )

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
                            logger.warning(f"Error calculating diff for key {key}: {e}")
                            max_diff = 0.0
                        rel_diffs.append(max_diff)
                    data.append((name, value, keys, rel_diffs))
            else:  # "different keys"
                value = results.get("different_keys", 0)
                if value > 0:
                    added = list(results.get("added_keys", []))
                    deleted = list(results.get("deleted_keys", []))
                    data.append((name, value, added, deleted))

        if not data:
            return None

        fig = go.Figure()

        # Extract filenames from the full paths
        filenames = [item[0].split("/")[-1] for item in data]

        for item in data:
            name = item[0]
            if option == "different keys same name":
                _, value, keys, rel_diffs = item
                if rel_diffs:
                    # Handle potential NaN or infinite values
                    finite_diffs = [diff for diff in rel_diffs if np.isfinite(diff)]
                    if finite_diffs:
                        max_diff = max(finite_diffs)
                        # Ensure we don't divide by zero and handle NaN/infinite values
                        normalized_diffs = [
                            min(
                                1.0,
                                (
                                    diff / max_diff
                                    if np.isfinite(diff) and max_diff > 0
                                    else 0.0
                                ),
                            )
                            for diff in rel_diffs
                        ]
                        colors = [
                            pc.sample_colorscale("Blues", diff)[0]
                            for diff in normalized_diffs
                        ]
                    else:
                        colors = ["rgb(220, 220, 255)"] * len(keys)
                else:
                    colors = ["rgb(220, 220, 255)"] * len(keys)
                    rel_diffs = [0] * len(keys)  # Set all differences to 0

                fig.add_trace(
                    go.Bar(
                        y=[name] * len(keys),
                        x=[1] * len(keys),
                        orientation="h",
                        name=name,
                        text=keys,
                        customdata=rel_diffs,
                        marker_color=colors,
                        hoverinfo="text",
                        hovertext=[
                            f"{name}<br>Key: {key}<br>Max relative difference: {diff:.2e}<br>(Versions differ by {diff:.1%})"
                            for key, diff in zip(keys, rel_diffs)
                        ],
                    )
                )
            else:  # "different keys"
                _, _, added, deleted = item
                colors_added = [f"rgb(0, {random.randint(100, 255)}, 0)" for _ in added]
                colors_deleted = [
                    f"rgb({random.randint(100, 255)}, 0, 0)" for _ in deleted
                ]
                fig.add_trace(
                    go.Bar(
                        y=[name] * len(added),
                        x=[1] * len(added),
                        orientation="h",
                        name=f"{name} (Added)",
                        text=added,
                        hovertemplate="%{y}<br>Added Key: %{text}<extra></extra>",
                        marker_color=colors_added,
                    )
                )
                fig.add_trace(
                    go.Bar(
                        y=[name] * len(deleted),
                        x=[1] * len(deleted),
                        orientation="h",
                        name=f"{name} (Deleted)",
                        text=deleted,
                        hovertemplate="%{y}<br>Deleted Key: %{text}<extra></extra>",
                        marker_color=colors_deleted,
                    )
                )

        fig.update_layout(
            title=f"{'Different Keys with Same Name' if option == 'different keys same name' else 'Different Keys'} Comparison",
            barmode="stack",
            height=max(300, len(data) * 40),  # Adjust height based on number of files
            xaxis_title="Number of Keys",
            yaxis=dict(
                title="",
                tickmode="array",
                tickvals=list(range(len(filenames))),
                ticktext=filenames,
                showgrid=False,
            ),
            showlegend=False,
            bargap=0.1,
            bargroupgap=0.05,
            margin=dict(l=200),  # Increase left margin to accommodate longer filenames
        )

        # Remove the text on the right side of the bars
        fig.update_traces(textposition="none")

        # Add a color bar to show the scale
        if any(item[3] for item in data if option == "different keys same name"):
            fig.update_layout(
                coloraxis_colorbar=dict(
                    title="Relative Difference",
                    tickvals=[0, 0.5, 1],
                    ticktext=["Low", "Medium", "High"],
                    lenmode="fraction",
                    len=0.75,
                )
            )

        if fig and os.environ.get("SAVE_COMP_IMG") == "1":
            if self.using_git:
                # Create shortened commit hashes
                short_ref1 = self.ref1_hash[:6] if self.ref1_hash else "current"
                short_ref2 = self.ref2_hash[:6] if self.ref2_hash else "current"
                plot_dir = Path(f"comparison_plots_{short_ref2}_new_{short_ref1}_old")
            else:
                # Use directory names for direct paths
                ref1_name = Path(self.ref1_path).name if self.ref1_path else "ref1"
                ref2_name = Path(self.ref2_path).name if self.ref2_path else "ref2"
                plot_dir = Path(f"comparison_plots_{ref2_name}_vs_{ref1_name}")

            plot_dir.mkdir(exist_ok=True)

            # Save high-res image in the new directory
            plot_type = "diff_keys" if option == "different keys" else "same_name_diff"
            filename = plot_dir / f"{plot_type}.png"
            fig.write_image(str(filename), scale=4, width=1200, height=800)
            print(f"Saved plot to {filename}")

        return fig

    def compare_testspectrumsolver_hdf(
        self, custom_ref1_path=None, custom_ref2_path=None
    ):
        """
        Perform comparison for TestSpectrumSolver HDF5 files.

        Parameters
        ----------
        custom_ref1_path : str or Path, optional
            Custom path to the first TestSpectrumSolver.h5 file, by default None.
            If None, uses the standard path within ref1_path directory (git mode) or
            the direct ref1_path (direct path mode).
        custom_ref2_path : str or Path, optional
            Custom path to the second TestSpectrumSolver.h5 file, by default None.
            If None, uses the standard path within ref2_path directory (git mode) or
            the direct ref2_path (direct path mode).

        Notes
        -----
        The method automatically creates visualization output directories when
        the SAVE_COMP_IMG environment variable is set to '1'. The comparison
        generates specialized plots tailored for spectrum solver data analysis.

        Standard file paths (when custom paths are not provided):\n
        - git mode: ``tardis/spectrum/tests/test_spectrum_solver/test_spectrum_solver/TestSpectrumSolver.h5``\n
        - direct path mode: uses ref1_path and ref2_path directly\n

        """
        if custom_ref1_path:
            ref1_path = custom_ref1_path
        elif self.using_git:
            ref1_path = (
                Path(self.ref1_path)
                / "tardis/spectrum/tests/test_spectrum_solver/test_spectrum_solver/TestSpectrumSolver.h5"
            )
        else:
            ref1_path = self.ref1_path

        if custom_ref2_path:
            ref2_path = custom_ref2_path
        elif self.using_git:
            ref2_path = (
                Path(self.ref2_path)
                / "tardis/spectrum/tests/test_spectrum_solver/test_spectrum_solver/TestSpectrumSolver.h5"
            )
        else:
            ref2_path = self.ref2_path

        # Create plot directory first
        plot_dir = None
        if os.environ.get("SAVE_COMP_IMG") == "1":
            if self.using_git:
                short_ref1 = self.ref1_hash[:6] if self.ref1_hash else "current"
                short_ref2 = self.ref2_hash[:6] if self.ref2_hash else "current"
                plot_dir = Path(f"comparison_plots_{short_ref2}_new_{short_ref1}_old")
            else:
                ref1_name = Path(self.ref1_path).name if self.ref1_path else "ref1"
                ref2_name = Path(self.ref2_path).name if self.ref2_path else "ref2"
                plot_dir = Path(f"spectrum_plots_{ref2_name}_vs_{ref1_name}")
            plot_dir.mkdir(exist_ok=True)

        # Pass plot_dir to SpectrumSolverComparator
        comparator = SpectrumSolverComparator(ref1_path, ref2_path, plot_dir)
        comparator.setup()
        comparator.plot_matplotlib()
        comparator.plot_plotly()
