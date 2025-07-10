import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from plotly.subplots import make_subplots
from pathlib import Path
from git import Repo
from collections import defaultdict
import subprocess
from IPython.display import display


class SpectrumSolverComparator:
    """
    A class for comparing and visualizing spectrum solver data between two regression datasets.

    This class provides visualization capabilities for spectrum solver analysis,
    generating both matplotlib and Plotly plots that show luminosity comparisons and
    fractional residuals between two reference datasets. It supports multiple spectrum
    types including integrated, real packets, reabsorbed packets, and virtual packets.

    Parameters
    ----------
    ref1_path : str or Path
        Path to the first reference HDF5 file containing spectrum solver data.
        This file should contain the expected spectrum solver data structure.
    ref2_path : str or Path
        Path to the second reference HDF5 file containing spectrum solver data.
        This file should have the same structure as ref1_path for comparison.
    plot_dir : str, Path, or None, optional
        Directory path where plots should be saved when SAVE_COMP_IMG environment
        variable is set to '1', by default None. If None, plots are displayed
        but not saved to disk.
    Notes
    -----
    The class expects HDF5 files with spectrum solver data stored under the path:
    'simulation/spectrum_solver/{spectrum_type}/{wavelength|luminosity}'

    Each spectrum type should contain both wavelength and luminosity datasets
    as 1D arrays of the same length.
    """

    def __init__(self, ref1_path, ref2_path, plot_dir=None):
        self.ref1_path = ref1_path
        self.ref2_path = ref2_path
        self.plot_dir = plot_dir  # Add plot_dir parameter
        self.spectrum_keys = [
            "spectrum_integrated",
            "spectrum_real_packets",
            "spectrum_real_packets_reabsorbed",
            "spectrum_virtual_packets",
        ]
        self.data = {}

    def setup(self):
        """
        Load spectrum solver data from both reference HDF5 files.

        This method reads wavelength and luminosity data for all spectrum types
        from both reference files and stores them in the internal data structure.
        It handles missing files and keys with warning messages.

        Notes
        -----
        The method populates self.data with the following structure:
        data['Ref1'|'Ref2'][spectrum_key]['wavelength'|'luminosity'] = numpy.ndarray

        For each spectrum type, the method expects to find:
        - simulation/spectrum_solver/{spectrum_type}/wavelength
        - simulation/spectrum_solver/{spectrum_type}/luminosity

        Error handling includes:
        - FileNotFoundError: Warns if HDF5 files are missing
        - KeyError: Warns if expected spectrum data keys are not found

        After successful execution, all data is available as NumPy arrays
        for plotting and analysis operations.
        """
        for ref_name, file_path in [("Ref1", self.ref1_path), ("Ref2", self.ref2_path)]:
            self.data[ref_name] = {}
            try:
                with pd.HDFStore(file_path) as hdf:
                    for key in self.spectrum_keys:
                        full_key = f"simulation/spectrum_solver/{key}"
                        self.data[ref_name][key] = {
                            "wavelength": np.array(hdf[f"{full_key}/wavelength"]),
                            "luminosity": np.array(hdf[f"{full_key}/luminosity"]),
                        }
            except FileNotFoundError:
                print(f"Warning: File not found at {file_path}")
            except KeyError as e:
                print(f"Warning: Key {e} not found in {file_path}")

    def plot_matplotlib(self):
        """
        Generate comprehensive matplotlib plots comparing spectrum solver data.

        This method creates a 4x2 grid of subplots showing luminosity comparisons
        and fractional residuals for each spectrum type. Each spectrum type gets
        two vertically stacked subplots: luminosity comparison (top) and fractional
        residuals (bottom).

        Notes
        -----
        Plot structure:
        - Figure size: 20x20 inches for high-resolution output
        - Grid layout: 4 rows × 2 columns with height ratios [3,1,3,1]
        - Top subplots: Luminosity vs wavelength for both references
        - Bottom subplots: Fractional residuals (Ref2-Ref1)/Ref1 vs wavelength

        Visualization features:
        - Ref1 data: solid lines
        - Ref2 data: dashed lines
        - Residuals: purple lines with horizontal zero-reference line
        - Grid lines and legends for clarity
        - Shared x-axes between luminosity and residual plots

        Fractional residuals calculation:
        residuals = (luminosity_ref2 - luminosity_ref1) / luminosity_ref1

        Division by zero is handled by setting residuals to 0 where luminosity_ref1 = 0.

        File saving:
        If environment variable SAVE_COMP_IMG='1' and plot_dir is specified,
        saves high-resolution PNG (300 DPI) to plot_dir/spectrum.png.
        """
        fig = plt.figure(figsize=(20, 20))
        gs = fig.add_gridspec(4, 2, height_ratios=[3, 1, 3, 1], hspace=0.1, wspace=0.3)

        for idx, key in enumerate(self.spectrum_keys):
            row = (idx // 2) * 2
            col = idx % 2

            ax_luminosity = fig.add_subplot(gs[row, col])
            ax_residuals = fig.add_subplot(gs[row + 1, col], sharex=ax_luminosity)

            # Plot luminosity
            for ref_name, linestyle in [("Ref1", "-"), ("Ref2", "--")]:
                if key in self.data[ref_name]:
                    wavelength = self.data[ref_name][key]["wavelength"]
                    luminosity = self.data[ref_name][key]["luminosity"]
                    ax_luminosity.plot(
                        wavelength,
                        luminosity,
                        linestyle=linestyle,
                        label=f"{ref_name} Luminosity",
                    )

            ax_luminosity.set_ylabel("Luminosity")
            ax_luminosity.set_title(f"Luminosity for {key}")
            ax_luminosity.legend()
            ax_luminosity.grid(True)

            # Plot fractional residuals
            if key in self.data["Ref1"] and key in self.data["Ref2"]:
                wavelength = self.data["Ref1"][key]["wavelength"]
                luminosity_ref1 = self.data["Ref1"][key]["luminosity"]
                luminosity_ref2 = self.data["Ref2"][key]["luminosity"]

                # Calculate fractional residuals
                with np.errstate(divide="ignore", invalid="ignore"):
                    fractional_residuals = np.where(
                        luminosity_ref1 != 0,
                        (luminosity_ref2 - luminosity_ref1) / luminosity_ref1,
                        0,
                    )

                ax_residuals.plot(
                    wavelength,
                    fractional_residuals,
                    label="Fractional Residuals",
                    color="purple",
                )
                ax_residuals.axhline(
                    0, color="black", linestyle="--", linewidth=0.8
                )  # Add a horizontal line at y=0

            ax_residuals.set_xlabel("Wavelength")
            ax_residuals.set_ylabel("Fractional Residuals")
            ax_residuals.legend()
            ax_residuals.grid(True)

            # Remove x-axis labels from upper plot
            ax_luminosity.tick_params(axis="x", labelbottom=False)

            # Only show x-label for bottom plots
            if row != 2:
                ax_residuals.tick_params(axis="x", labelbottom=False)

        plt.suptitle(
            "Comparison of Spectrum Solvers with Fractional Residuals", fontsize=16
        )
        plt.tight_layout()
        plt.subplots_adjust(top=0.95)

        if os.environ.get("SAVE_COMP_IMG") == "1" and self.plot_dir:
            filename = self.plot_dir / "spectrum.png"
            plt.savefig(filename, dpi=300, bbox_inches="tight")
            print(f"Saved spectrum plot to {filename}")

        plt.show()

    def plot_plotly(self):
        """
        Generate interactive Plotly plots for spectrum solver data comparison.

        This method creates an interactive web-based visualization using Plotly
        with the same data structure as the matplotlib version but with enhanced
        interactivity, hover information, and modern styling.

        Notes
        -----
        Plot configuration:
        - Layout: 4 rows × 2 columns with height ratios [0.3, 0.15] repeated
        - Total dimensions: 1200px width × 900px height
        - Shared x-axes between luminosity and residual plots
        - Reduced spacing for compact visualization

        Visualization features:
        - Interactive hover tooltips with data values
        - Solid lines for Ref1, dashed lines for Ref2
        - Purple residual lines with horizontal zero-reference lines
        - Light blue background for enhanced readability
        - Grid lines and consistent axis labeling

        Subplot organization:
        - Rows 1,3: Luminosity plots for spectrum types
        - Rows 2,4: Corresponding fractional residual plots
        - Column 1: spectrum_integrated, spectrum_real_packets_reabsorbed
        - Column 2: spectrum_real_packets, spectrum_virtual_packets

        Interactive features:
        - Zoom and pan capabilities
        - Legend toggling for hiding/showing traces
        - Hover data inspection
        - Export capabilities (PNG, SVG, PDF)

        The plot automatically handles missing data gracefully and maintains
        consistent axis ranges across related subplots for easy comparison.
        """
        # Create figure with shared x-axes
        fig = make_subplots(
            rows=4,
            cols=2,
            subplot_titles=[
                "Luminosity for spectrum_integrated",
                "Luminosity for spectrum_real_packets",
                "Fractional Residuals",
                "Fractional Residuals",
                "Luminosity for spectrum_real_packets_reabsorbed",
                "Luminosity for spectrum_virtual_packets",
                "Fractional Residuals",
                "Fractional Residuals",
            ],
            vertical_spacing=0.07,
            horizontal_spacing=0.08,  # Reduced from 0.15
            row_heights=[0.3, 0.15] * 2,
            shared_xaxes=True,
        )

        # Plot each spectrum type and its residuals
        for idx, key in enumerate(self.spectrum_keys):
            plot_col = idx % 2 + 1
            plot_row = (idx // 2) * 2 + 1

            # Store x-range for shared axis
            x_range = None

            # Plot luminosity traces
            for ref_name, line_style in [("Ref1", "solid"), ("Ref2", "dash")]:
                if key in self.data[ref_name]:
                    wavelength = self.data[ref_name][key]["wavelength"]
                    luminosity = self.data[ref_name][key]["luminosity"]

                    if x_range is None:
                        x_range = [min(wavelength), max(wavelength)]

                    fig.add_trace(
                        go.Scatter(
                            x=wavelength,
                            y=luminosity,
                            mode="lines",
                            name=f"{ref_name} - {key}",
                            line=dict(dash=line_style),
                        ),
                        row=plot_row,
                        col=plot_col,
                    )

            # Plot residuals
            if key in self.data["Ref1"] and key in self.data["Ref2"]:
                wavelength = self.data["Ref1"][key]["wavelength"]
                luminosity_ref1 = self.data["Ref1"][key]["luminosity"]
                luminosity_ref2 = self.data["Ref2"][key]["luminosity"]

                with np.errstate(divide="ignore", invalid="ignore"):
                    fractional_residuals = np.where(
                        luminosity_ref1 != 0,
                        (luminosity_ref2 - luminosity_ref1) / luminosity_ref1,
                        0,
                    )

                fig.add_trace(
                    go.Scatter(
                        x=wavelength,
                        y=fractional_residuals,
                        mode="lines",
                        name=f"Residuals - {key}",
                        line=dict(color="purple"),
                    ),
                    row=plot_row + 1,
                    col=plot_col,
                )

                fig.add_hline(
                    y=0,
                    line=dict(color="black", dash="dash", width=0.8),
                    row=plot_row + 1,
                    col=plot_col,
                )

            # Update axes properties
            fig.update_xaxes(
                title_text="",
                showticklabels=False,
                row=plot_row,
                col=plot_col,
                gridcolor="lightgrey",
                showgrid=True,
                range=x_range,
            )

            # Show x-axis for bottom plots
            fig.update_xaxes(
                title_text="Wavelength",
                row=plot_row + 1,
                col=plot_col,
                gridcolor="lightgrey",
                showgrid=True,
                range=x_range,
            )

            fig.update_yaxes(
                title_text="Luminosity",
                row=plot_row,
                col=plot_col,
                gridcolor="lightgrey",
                showgrid=True,
            )
            fig.update_yaxes(
                title_text="Fractional Residuals",
                row=plot_row + 1,
                col=plot_col,
                gridcolor="lightgrey",
                showgrid=True,
            )

        # Update layout with minimal padding
        fig.update_layout(
            title="Comparison of Spectrum Solvers with Fractional Residuals",
            height=900,
            width=1200,
            showlegend=True,
            margin=dict(t=50, b=30, l=50, r=30),
            plot_bgcolor="rgba(240, 240, 255, 0.3)",
        )

        # Make subplot titles smaller and closer to plots
        for annotation in fig["layout"]["annotations"]:
            annotation["font"] = dict(size=10)
            annotation["y"] = annotation["y"] - 0.02

        fig.show()


class FileChangeMatrixVisualizer:
    """
    Visualizes file changes across commits in a matrix format.

    Automatically detects which files changed across the analyzed commits and shows:
    - Changed files matrix: Shows which files were added (+), deleted (-), modified (*), or unchanged (•)
    - Unchanged files table: Shows files that remained unchanged across all commits
    """

    def __init__(self, regression_repo_path, commits):
        self.regression_repo_path = Path(regression_repo_path)
        self.commits = commits

        self.repo = Repo(self.regression_repo_path)
        self.file_changes = {}  # {commit: {file_path: change_type}}
        self.file_details = {}  # {commit: {file_path: change_details}}
        self.all_files = set()  # All files that appear across all commits
        self.changed_files = set()  # Files that changed in any commit
        self.unchanged_files = set()  # Files that never changed

    def analyze_commits(self):
        """Analyze file changes across commits and separate changed vs unchanged files."""
        print(f"Analyzing {len(self.commits)} commits...")

        original_head = self.repo.head.commit.hexsha

        try:
            for i, commit_hash in enumerate(self.commits):
                print(f"Processing commit {i+1}/{len(self.commits)}: {commit_hash[:8]}")

                if i == 0:
                    # First commit - all files are "unchanged"
                    self.repo.git.checkout(commit_hash)
                    current_files = self._get_all_h5_files()
                    self.file_changes[commit_hash] = {f: '•' for f in current_files}
                    self.all_files.update(current_files)
                else:
                    # Compare with previous commit
                    changes = self._compare_commits(self.commits[i-1], commit_hash)
                    self.file_changes[commit_hash] = changes
                    self.all_files.update(changes.keys())

        finally:
            self.repo.git.checkout(original_head)

        # Separate changed and unchanged files
        self._categorize_files()

        print(f"Found {len(self.all_files)} total files across all commits.")
        print(f"Changed files: {len(self.changed_files)}")
        print(f"Unchanged files: {len(self.unchanged_files)}")

    def _get_all_h5_files(self):
        """Get all .h5 files in current commit."""
        files = set()
        for file_path in self.regression_repo_path.rglob("*.h5"):
            rel_path = file_path.relative_to(self.regression_repo_path)
            files.add(str(rel_path))
        return files

    def _categorize_files(self):
        """Separate files into changed and unchanged categories."""
        # Find files that changed in any commit
        for changes in self.file_changes.values():
            for file_path, change_type in changes.items():
                if change_type in ['+', '-', '*']:  # Added, deleted, or modified
                    self.changed_files.add(file_path)

        # Remaining files are unchanged
        self.unchanged_files = self.all_files - self.changed_files

    def _compare_commits(self, prev_commit_hash, current_commit_hash):
        """Compare two commits to find file changes."""
        # Get files in both commits
        self.repo.git.checkout(prev_commit_hash)
        prev_files = self._get_all_h5_files()

        self.repo.git.checkout(current_commit_hash)
        current_files = self._get_all_h5_files()

        changes = {}
        all_files = prev_files | current_files

        # Initialize details for this commit if not exists
        if current_commit_hash not in self.file_details:
            self.file_details[current_commit_hash] = {}

        for file_path in all_files:
            if file_path not in prev_files:
                changes[file_path] = '+'  # Added
                self.file_details[current_commit_hash][file_path] = "File added"
            elif file_path not in current_files:
                changes[file_path] = '-'  # Deleted
                self.file_details[current_commit_hash][file_path] = "File deleted"
            elif self._is_file_modified(file_path, prev_commit_hash, current_commit_hash):
                changes[file_path] = '*'  # Modified
                self.file_details[current_commit_hash][file_path] = self._get_file_change_details(file_path, prev_commit_hash, current_commit_hash)
            else:
                changes[file_path] = '•'  # Unchanged
                self.file_details[current_commit_hash][file_path] = "No changes"

        return changes

    def _is_file_modified(self, file_path, prev_commit, current_commit):
        """Check if file was modified between commits using git diff."""
        try:
            result = subprocess.run([
                'git', 'diff', '--quiet',
                f'{prev_commit}..{current_commit}',
                '--', file_path
            ], cwd=self.regression_repo_path, capture_output=True)
            return result.returncode != 0  # 0 = no diff, 1 = has diff
        except:
            return True  # Assume modified if git diff fails

    def _get_file_change_details(self, file_path, prev_commit, current_commit):
        """Get detailed information about what changed in a file."""
        try:
            # Get git diff stats
            result = subprocess.run([
                'git', 'diff', '--stat',
                f'{prev_commit}..{current_commit}',
                '--', file_path
            ], cwd=self.regression_repo_path, capture_output=True, text=True)

            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            else:
                return "File changed (no diff details available)"
        except:
            return "File changed (error getting details)"

    def print_matrix(self):
        """Print file change analysis as clean DataFrames with better visual distinction."""
        if not self.file_changes:
            print("No analysis done. Run analyze_commits() first.")
            return

        short_commits = [commit[:6] for commit in self.commits]
        symbols = {'•': '•', '+': '+', '-': '-', '*': '*', '∅': '∅'}
        symbol_colors = {'•': 'blue', '+': 'green', '-': 'red', '*': 'orange', '∅': 'grey'}

        self._print_dataframe_matrix(short_commits, symbols, symbol_colors)

    def _print_dataframe_matrix(self, short_commits, symbols, _):
        """Print using pandas DataFrames with colored symbols."""

        def style_symbol(val):
            """Apply color and bold styling to symbols."""
            color_map = {'•': 'blue', '*': 'gold', '+': 'green', '-': 'red', '∅': 'grey'}
            if val in color_map:
                return f'color: {color_map[val]}; font-weight: bold; font-size: 24px;'
            return ''

        # Set pandas options to show all rows and full column content
        with pd.option_context('display.max_rows', None, 'display.max_columns', None,
                              'display.max_colwidth', None, 'display.width', None):
            # Changed Files
            if self.changed_files:
                changed_data = []
                for file_path in sorted(self.changed_files):
                    row = {'Files': file_path}
                    for commit in self.commits:
                        commit_short = commit[:6]
                        if commit in self.file_changes and file_path in self.file_changes[commit]:
                            # File has a recorded change for this commit
                            symbol = self.file_changes[commit][file_path]
                            row[commit_short] = symbols.get(symbol, symbol)
                        else:
                            # File doesn't exist in this commit
                            row[commit_short] = symbols['∅']
                    changed_data.append(row)

                changed_df = pd.DataFrame(changed_data)
                print(f"\nChanged Files Matrix ({len(self.changed_files)} files):")
                print("=" * 60)

                # Apply styling to symbol columns only
                short_commits = [commit[:6] for commit in self.commits]
                try:
                    styled_df = changed_df.style.map(style_symbol, subset=short_commits)
                    display(styled_df)
                except AttributeError:
                    styled_df = changed_df.style.applymap(style_symbol, subset=short_commits)
                    display(styled_df)
            else:
                print("\nNo files changed across the analyzed commits.")

            # Unchanged Files
            if self.unchanged_files:
                unchanged_data = [
                    {'Files': file_path, **{commit[:6]: symbols['•'] for commit in self.commits}}
                    for file_path in sorted(self.unchanged_files)
                ]

                unchanged_df = pd.DataFrame(unchanged_data)
                print(f"\nUnchanged Files Table ({len(self.unchanged_files)} files):")
                print("=" * 60)

                # Apply styling to symbol columns only
                try:
                    styled_df = unchanged_df.style.map(style_symbol, subset=short_commits)
                    display(styled_df)
                except AttributeError:
                    styled_df = unchanged_df.style.applymap(style_symbol, subset=short_commits)
                    display(styled_df)
            else:
                print("\nAll files changed across the analyzed commits.")

        # Simple legend with colors
        print(f"\nLegend:")
        print("─" * 30)
        legend_items = [('•', 'blue', 'unchanged'), ('*', 'gold', 'modified'), ('+', 'green', 'added'), ('-', 'red', 'deleted'), ('∅', 'grey', 'not present')]
        for symbol, color, description in legend_items:
            print(f"  {symbol} = {description} ({color})")

    def _print_text_matrix(self, short_commits, symbols):
        """Fallback text-based display."""

        def print_table(files, title):
            if not files:
                return
            print(f"\n{title} ({len(files)} files):")
            print("=" * 80)
            print(f"{'Files':<50}", end="")
            for commit in short_commits:
                print(f"  {commit:>8}", end="")
            print()
            print("─" * (50 + len(short_commits) * 10))

            for file_path in sorted(files):
                display_name = file_path if len(file_path) <= 47 else "..." + file_path[-44:]
                print(f"{display_name:<50}", end="")
                for commit in self.commits:
                    if files == self.unchanged_files:
                        symbol = symbols['•']
                    else:
                        change = self.file_changes.get(commit, {}).get(file_path, '•')
                        symbol = symbols.get(change, change)
                    print(f"  {symbol:>8}", end="")
                print()

        print_table(self.changed_files, "Changed Files Matrix") if self.changed_files else print("\nNo files changed across the analyzed commits.")
        print_table(self.unchanged_files, "Unchanged Files Table") if self.unchanged_files else print("\nAll files changed across the analyzed commits.")

        print(f"\nLegend:")
        print("─" * 30)
        for symbol, description in [('•', 'unchanged'), ('*', 'modified'), ('+', 'added'), ('-', 'deleted'), ('∅', 'not present')]:
            print(f"  {symbol} = {description}")