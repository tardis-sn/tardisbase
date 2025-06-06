import os
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.colors as pc
import random
from plotly.subplots import make_subplots

class SpectrumSolverComparator:

    def __init__(self, ref1_path: str | Path, ref2_path: str | Path, plot_dir: Path | None = None):
        self.ref1_path = ref1_path
        self.ref2_path = ref2_path
        self.plot_dir = plot_dir
        self.spectrum_keys = [
            'spectrum_integrated',
            'spectrum_real_packets',
            'spectrum_real_packets_reabsorbed',
            'spectrum_virtual_packets'
        ]
        self.data = {}

    def setup(self) -> None:
        for ref_name, file_path in [('Ref1', self.ref1_path), ('Ref2', self.ref2_path)]:
            self.data[ref_name] = {}
            try:
                with pd.HDFStore(file_path) as hdf:
                    for key in self.spectrum_keys:
                        full_key = f"simulation/spectrum_solver/{key}"
                        self.data[ref_name][key] = {
                            'wavelength': np.array(hdf[f'{full_key}/wavelength']),
                            'luminosity': np.array(hdf[f'{full_key}/luminosity'])
                        }
            except FileNotFoundError:
                print(f"Warning: File not found at {file_path}")
            except KeyError as e:
                print(f"Warning: Key {e} not found in {file_path}")

    def plot_matplotlib(self) -> None:
        fig = plt.figure(figsize=(20, 20))
        gs = fig.add_gridspec(4, 2, height_ratios=[3, 1, 3, 1], hspace=0.1, wspace=0.3)

        for idx, key in enumerate(self.spectrum_keys):
            row = (idx // 2) * 2
            col = idx % 2
            
            ax_luminosity = fig.add_subplot(gs[row, col])
            ax_residuals = fig.add_subplot(gs[row+1, col], sharex=ax_luminosity)
            
            # Plot luminosity
            for ref_name, linestyle in [('Ref1', '-'), ('Ref2', '--')]:
                if key in self.data[ref_name]:
                    wavelength = self.data[ref_name][key]['wavelength']
                    luminosity = self.data[ref_name][key]['luminosity']
                    ax_luminosity.plot(wavelength, luminosity, linestyle=linestyle, 
                                     label=f'{ref_name} Luminosity')
            
            ax_luminosity.set_ylabel('Luminosity')
            ax_luminosity.set_title(f'Luminosity for {key}')
            ax_luminosity.legend()
            ax_luminosity.grid(True)
            
            # Plot fractional residuals
            if key in self.data['Ref1'] and key in self.data['Ref2']:
                wavelength = self.data['Ref1'][key]['wavelength']
                luminosity_ref1 = self.data['Ref1'][key]['luminosity']
                luminosity_ref2 = self.data['Ref2'][key]['luminosity']
                
                # Calculate fractional residuals
                with np.errstate(divide='ignore', invalid='ignore'):
                    fractional_residuals = np.where(
                        luminosity_ref1 != 0,
                        (luminosity_ref2 - luminosity_ref1) / luminosity_ref1,
                        0
                    )
                
                ax_residuals.plot(wavelength, fractional_residuals, 
                                label='Fractional Residuals', color='purple')
                ax_residuals.axhline(0, color='black', linestyle='--', linewidth=0.8)
            
            ax_residuals.set_xlabel('Wavelength')
            ax_residuals.set_ylabel('Fractional Residuals')
            ax_residuals.legend()
            ax_residuals.grid(True)
            
            # Remove x-axis labels from upper plot
            ax_luminosity.tick_params(axis='x', labelbottom=False)
            
            # Only show x-label for bottom plots
            if row != 2:
                ax_residuals.tick_params(axis='x', labelbottom=False)
        
        plt.suptitle('Comparison of Spectrum Solvers with Fractional Residuals', fontsize=16)
        plt.tight_layout()
        plt.subplots_adjust(top=0.95)

        if os.environ.get('SAVE_COMP_IMG') == '1' and self.plot_dir:
            filename = self.plot_dir / "spectrum.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"Saved spectrum plot to {filename}")
        
        plt.show()

    def plot_plotly(self) -> None:
        fig = make_subplots(
            rows=4,
            cols=2,
            subplot_titles=[
                'Luminosity for spectrum_integrated', 'Luminosity for spectrum_real_packets',
                'Fractional Residuals', 'Fractional Residuals',
                'Luminosity for spectrum_real_packets_reabsorbed', 'Luminosity for spectrum_virtual_packets',
                'Fractional Residuals', 'Fractional Residuals'
            ],
            vertical_spacing=0.07,
            horizontal_spacing=0.08,
            row_heights=[0.3, 0.15] * 2,
            shared_xaxes=True
        )

        for idx, key in enumerate(self.spectrum_keys):
            plot_col = idx % 2 + 1
            plot_row = (idx // 2) * 2 + 1
            
            x_range = None
            
            # Plot luminosity traces
            for ref_name, line_style in [('Ref1', 'solid'), ('Ref2', 'dash')]:
                if key in self.data[ref_name]:
                    wavelength = self.data[ref_name][key]['wavelength']
                    luminosity = self.data[ref_name][key]['luminosity']
                    
                    if x_range is None:
                        x_range = [min(wavelength), max(wavelength)]
                    
                    fig.add_trace(
                        go.Scatter(
                            x=wavelength,
                            y=luminosity,
                            mode='lines',
                            name=f'{ref_name} - {key}',
                            line=dict(dash=line_style),
                        ),
                        row=plot_row,
                        col=plot_col
                    )
            
            # Plot residuals
            if key in self.data['Ref1'] and key in self.data['Ref2']:
                wavelength = self.data['Ref1'][key]['wavelength']
                luminosity_ref1 = self.data['Ref1'][key]['luminosity']
                luminosity_ref2 = self.data['Ref2'][key]['luminosity']
                
                with np.errstate(divide='ignore', invalid='ignore'):
                    fractional_residuals = np.where(
                        luminosity_ref1 != 0,
                        (luminosity_ref2 - luminosity_ref1) / luminosity_ref1,
                        0
                    )
                
                fig.add_trace(
                    go.Scatter(
                        x=wavelength,
                        y=fractional_residuals,
                        mode='lines',
                        name=f'Residuals - {key}',
                        line=dict(color='purple'),
                    ),
                    row=plot_row + 1,
                    col=plot_col
                )
                
                fig.add_hline(
                    y=0,
                    line=dict(color='black', dash='dash', width=0.8),
                    row=plot_row + 1,
                    col=plot_col
                )

            # Update axes properties
            fig.update_xaxes(
                title_text="",
                showticklabels=False,
                row=plot_row,
                col=plot_col,
                gridcolor='lightgrey',
                showgrid=True,
                range=x_range
            )
            
            fig.update_xaxes(
                title_text="Wavelength",
                row=plot_row + 1,
                col=plot_col,
                gridcolor='lightgrey',
                showgrid=True,
                range=x_range
            )
            
            fig.update_yaxes(
                title_text="Luminosity",
                row=plot_row,
                col=plot_col,
                gridcolor='lightgrey',
                showgrid=True
            )
            fig.update_yaxes(
                title_text="Fractional Residuals",
                row=plot_row + 1,
                col=plot_col,
                gridcolor='lightgrey',
                showgrid=True
            )

        # Update layout
        fig.update_layout(
            title='Comparison of Spectrum Solvers with Fractional Residuals',
            height=900,
            width=1200,
            showlegend=True,
            margin=dict(t=50, b=30, l=50, r=30),
            plot_bgcolor='rgba(240, 240, 255, 0.3)',
        )

        # Make subplot titles smaller and closer to plots
        for annotation in fig['layout']['annotations']:
            annotation['font'] = dict(size=10)
            annotation['y'] = annotation['y'] - 0.02

        fig.show()

def generate_comparison_graph(data: list, option: str, ref1_hash: str | None = None,
                            ref2_hash: str | None = None) -> go.Figure | None:

    if not data:
        return None

    fig = go.Figure()

    # Extract filenames from the full paths
    filenames = [item[0].split('/')[-1] for item in data]

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
                        min(1.0, (diff / max_diff if np.isfinite(diff) and max_diff > 0 else 0.0))
                        for diff in rel_diffs
                    ]
                    colors = [pc.sample_colorscale('Blues', diff)[0] for diff in normalized_diffs]
                else:
                    colors = ['rgb(220, 220, 255)'] * len(keys)
            else:
                colors = ['rgb(220, 220, 255)'] * len(keys)
                rel_diffs = [0] * len(keys)  # Set all differences to 0

            fig.add_trace(go.Bar(
                y=[name] * len(keys),
                x=[1] * len(keys),
                orientation='h',
                name=name,
                text=keys,
                customdata=rel_diffs,
                marker_color=colors,
                hoverinfo='text',
                hovertext=[f"{name}<br>Key: {key}<br>Max relative difference: {diff:.2e}<br>(Versions differ by {diff:.1%})" 
                           for key, diff in zip(keys, rel_diffs)]
            ))
        else:  # "different keys"
            _, _, added, deleted = item
            colors_added = [f'rgb(0, {random.randint(100, 255)}, 0)' for _ in added]
            colors_deleted = [f'rgb({random.randint(100, 255)}, 0, 0)' for _ in deleted]
            fig.add_trace(go.Bar(
                y=[name] * len(added),
                x=[1] * len(added),
                orientation='h',
                name=f"{name} (Added)",
                text=added,
                hovertemplate='%{y}<br>Added Key: %{text}<extra></extra>',
                marker_color=colors_added
            ))
            fig.add_trace(go.Bar(
                y=[name] * len(deleted),
                x=[1] * len(deleted),
                orientation='h',
                name=f"{name} (Deleted)",
                text=deleted,
                hovertemplate='%{y}<br>Deleted Key: %{text}<extra></extra>',
                marker_color=colors_deleted
            ))

    fig.update_layout(
        title=f"{'Different Keys with Same Name' if option == 'different keys same name' else 'Different Keys'} Comparison",
        barmode='stack',
        height=max(300, len(data) * 40),  # Adjust height based on number of files
        xaxis_title="Number of Keys",
        yaxis=dict(
            title='',
            tickmode='array',
            tickvals=list(range(len(filenames))),
            ticktext=filenames,
            showgrid=False
        ),
        showlegend=False,
        bargap=0.1,
        bargroupgap=0.05,
        margin=dict(l=200)  # Increase left margin to accommodate longer filenames
    )

    # Remove the text on the right side of the bars
    fig.update_traces(textposition='none')

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

    if fig and os.environ.get('SAVE_COMP_IMG') == '1':
        # Create shortened commit hashes
        short_ref1 = ref1_hash[:6] if ref1_hash else "current"
        short_ref2 = ref2_hash[:6] if ref2_hash else "current"
        
        # Create directory for comparison plots
        plot_dir = Path(f"comparison_plots_{short_ref2}_new_{short_ref1}_old")
        plot_dir.mkdir(exist_ok=True)
        
        # Save high-res image in the new directory
        plot_type = "diff_keys" if option == "different keys" else "same_name_diff"
        filename = plot_dir / f"{plot_type}.png"
        fig.write_image(str(filename), scale=4, width=1200, height=800)
        print(f"Saved plot to {filename}")
    
    return fig 