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
