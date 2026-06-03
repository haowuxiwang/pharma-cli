"""Chart generation module using Plotly."""

import plotly.graph_objects as go
import plotly.io as pio
from typing import Dict, Any, List
import numpy as np


def create_control_chart(data: Dict[str, Any]) -> str:
    """Create interactive control chart.

    Args:
        data: Control chart data from R script

    Returns:
        HTML string of interactive chart
    """
    chart = data.get('chart', data)
    points = chart.get('points', [])
    center = chart.get('center', 0)
    ucl = chart.get('ucl', 0)
    lcl = chart.get('lcl', 0)
    out_of_control = chart.get('out_of_control_points', [])

    fig = go.Figure()

    # Add data points
    fig.add_trace(go.Scatter(
        x=list(range(1, len(points) + 1)),
        y=points,
        mode='lines+markers',
        name='Data',
        line=dict(color='blue', width=2),
        marker=dict(size=8)
    ))

    # Add UCL
    fig.add_hline(
        y=ucl,
        line_dash="dash",
        line_color="red",
        line_width=2,
        annotation_text=f"UCL = {ucl:.4f}",
        annotation_position="top right"
    )

    # Add CL
    fig.add_hline(
        y=center,
        line_color="green",
        line_width=2,
        annotation_text=f"CL = {center:.4f}",
        annotation_position="top right"
    )

    # Add LCL
    fig.add_hline(
        y=lcl,
        line_dash="dash",
        line_color="red",
        line_width=2,
        annotation_text=f"LCL = {lcl:.4f}",
        annotation_position="bottom right"
    )

    # Highlight out-of-control points
    if out_of_control:
        # Handle both list and single integer
        if isinstance(out_of_control, (list, tuple)):
            ooc_list = out_of_control
        else:
            ooc_list = [out_of_control]

        # Convert to 0-based index
        ooc_indices = [i - 1 for i in ooc_list if 0 <= i - 1 < len(points)]
        if ooc_indices:
            fig.add_trace(go.Scatter(
                x=[i + 1 for i in ooc_indices],
                y=[points[i] for i in ooc_indices],
                mode='markers',
                name='Out of Control',
                marker=dict(size=12, color='red', symbol='x')
            ))

    # Update layout
    chart_type = data.get('chart_type', 'Control Chart')
    fig.update_layout(
        title=f'{chart_type.upper()} Chart',
        xaxis_title='Sample',
        yaxis_title='Value',
        showlegend=True,
        hovermode='x unified',
        template='plotly_white'
    )

    return pio.to_html(fig, full_html=False)


def create_histogram(data: Dict[str, Any], title: str = "Distribution") -> str:
    """Create interactive histogram.

    Args:
        data: Histogram data from R script
        title: Chart title

    Returns:
        HTML string of interactive chart
    """
    histogram = data.get('histogram', {})
    x = histogram.get('x', [])
    counts = histogram.get('counts', [])

    fig = go.Figure()

    # Add histogram bars
    fig.add_trace(go.Bar(
        x=x,
        y=counts,
        name='Frequency',
        marker_color='lightblue',
        marker_line_color='blue',
        marker_line_width=1
    ))

    # Add normal curve if available
    normal_curve = data.get('normal_curve', {})
    if normal_curve:
        curve_x = normal_curve.get('x', [])
        curve_y = normal_curve.get('y', [])

        # Scale curve to match histogram
        if counts and curve_y:
            max_count = max(counts)
            max_curve = max(curve_y) if curve_y else 1
            scale_factor = max_count / max_curve if max_curve > 0 else 1
            scaled_y = [y * scale_factor for y in curve_y]

            fig.add_trace(go.Scatter(
                x=curve_x,
                y=scaled_y,
                mode='lines',
                name='Normal Curve',
                line=dict(color='red', width=2)
            ))

    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title='Value',
        yaxis_title='Frequency',
        showlegend=True,
        hovermode='x',
        template='plotly_white'
    )

    return pio.to_html(fig, full_html=False)


def create_qq_plot(data: Dict[str, Any]) -> str:
    """Create interactive Q-Q plot.

    Args:
        data: Q-Q plot data from R script

    Returns:
        HTML string of interactive chart
    """
    qq_plot = data.get('qq_plot', {})
    theoretical = qq_plot.get('theoretical', [])
    sample = qq_plot.get('sample', [])

    fig = go.Figure()

    # Add scatter points
    fig.add_trace(go.Scatter(
        x=theoretical,
        y=sample,
        mode='markers',
        name='Sample',
        marker=dict(size=8, color='blue')
    ))

    # Add reference line
    if theoretical and sample:
        min_val = min(min(theoretical), min(sample))
        max_val = max(max(theoretical), max(sample))
        fig.add_trace(go.Scatter(
            x=[min_val, max_val],
            y=[min_val, max_val],
            mode='lines',
            name='Reference',
            line=dict(color='red', dash='dash', width=2)
        ))

    # Update layout
    fig.update_layout(
        title='Q-Q Plot',
        xaxis_title='Theoretical Quantiles',
        yaxis_title='Sample Quantiles',
        showlegend=True,
        hovermode='closest',
        template='plotly_white'
    )

    return pio.to_html(fig, full_html=False)


def create_capability_chart(data: Dict[str, Any]) -> str:
    """Create interactive capability chart.

    Args:
        data: Capability data from R script

    Returns:
        HTML string of interactive chart
    """
    histogram = data.get('histogram', {})
    x = histogram.get('x', [])
    counts = histogram.get('counts', [])

    usl = data.get('usl')
    lsl = data.get('lsl')
    target = data.get('target')
    mean = data.get('mean')

    fig = go.Figure()

    # Add histogram bars
    fig.add_trace(go.Bar(
        x=x,
        y=counts,
        name='Frequency',
        marker_color='lightblue',
        marker_line_color='blue',
        marker_line_width=1
    ))

    # Add specification limits
    if usl is not None:
        fig.add_vline(
            x=usl,
            line_dash="dash",
            line_color="red",
            line_width=2,
            annotation_text=f"USL = {usl}",
            annotation_position="top right"
        )

    if lsl is not None:
        fig.add_vline(
            x=lsl,
            line_dash="dash",
            line_color="red",
            line_width=2,
            annotation_text=f"LSL = {lsl}",
            annotation_position="top left"
        )

    if target is not None:
        fig.add_vline(
            x=target,
            line_color="green",
            line_width=2,
            annotation_text=f"Target = {target}",
            annotation_position="top right"
        )

    if mean is not None:
        fig.add_vline(
            x=mean,
            line_color="purple",
            line_width=2,
            annotation_text=f"Mean = {mean:.4f}",
            annotation_position="top left"
        )

    # Update layout
    cpk = data.get('cpk', 0)
    rating = data.get('rating', 'Unknown')
    fig.update_layout(
        title=f'Process Capability (Cpk = {cpk:.4f}, Rating: {rating})',
        xaxis_title='Value',
        yaxis_title='Frequency',
        showlegend=True,
        hovermode='x',
        template='plotly_white'
    )

    return pio.to_html(fig, full_html=False)


def create_scatter_plot(x: List[float], y: List[float],
                       title: str = "Scatter Plot",
                       x_label: str = "X",
                       y_label: str = "Y",
                       regression_line: bool = False) -> str:
    """Create interactive scatter plot.

    Args:
        x: X values
        y: Y values
        title: Chart title
        x_label: X axis label
        y_label: Y axis label
        regression_line: Whether to add regression line

    Returns:
        HTML string of interactive chart
    """
    fig = go.Figure()

    # Add scatter points
    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode='markers',
        name='Data',
        marker=dict(size=10, color='blue')
    ))

    # Add regression line if requested
    if regression_line and len(x) > 1:
        # Calculate regression line
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        x_line = np.linspace(min(x), max(x), 100)
        y_line = p(x_line)

        fig.add_trace(go.Scatter(
            x=x_line,
            y=y_line,
            mode='lines',
            name='Regression',
            line=dict(color='red', width=2)
        ))

    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title=y_label,
        showlegend=True,
        hovermode='closest',
        template='plotly_white'
    )

    return pio.to_html(fig, full_html=False)


def create_box_plot(data: List[float], groups: List[str] = None,
                    title: str = "Box Plot") -> str:
    """Create interactive box plot.

    Args:
        data: List of values or list of lists for multiple groups
        groups: Group names (optional)
        title: Chart title

    Returns:
        HTML string of interactive chart
    """
    fig = go.Figure()

    if not data:
        return pio.to_html(fig, full_html=False)

    # Handle single group or multiple groups
    if isinstance(data[0], (list, tuple)):
        # Multiple groups
        for i, group_data in enumerate(data):
            group_name = groups[i] if groups and i < len(groups) else f"Group {i+1}"
            fig.add_trace(go.Box(
                y=group_data,
                name=group_name,
                boxpoints='outliers',
                jitter=0.3,
                pointpos=-1.8
            ))
    else:
        # Single group
        fig.add_trace(go.Box(
            y=data,
            name="Data",
            boxpoints='outliers',
            jitter=0.3,
            pointpos=-1.8
        ))

    # Update layout
    fig.update_layout(
        title=title,
        yaxis_title='Value',
        showlegend=True,
        hovermode='closest',
        template='plotly_white'
    )

    return pio.to_html(fig, full_html=False)


def create_scatter_matrix(data: Dict[str, List[float]],
                         title: str = "Scatter Matrix") -> str:
    """Create interactive scatter matrix (pairs plot).

    Args:
        data: Dictionary of column_name: values
        title: Chart title

    Returns:
        HTML string of interactive chart
    """
    import pandas as pd

    # Create DataFrame
    df = pd.DataFrame(data)

    # Create scatter matrix
    fig = go.Figure()

    # Add scatter plots for each pair
    columns = list(data.keys())
    n = len(columns)

    for i in range(n):
        for j in range(n):
            if i != j:
                fig.add_trace(go.Scatter(
                    x=data[columns[j]],
                    y=data[columns[i]],
                    mode='markers',
                    name=f"{columns[i]} vs {columns[j]}",
                    xaxis=f"x{j+1}",
                    yaxis=f"y{i+1}",
                    showlegend=False
                ))

    # Update layout
    fig.update_layout(
        title=title,
        template='plotly_white',
        height=800,
        width=800
    )

    return pio.to_html(fig, full_html=False)


def create_heatmap(data: List[List[float]],
                   x_labels: List[str] = None,
                   y_labels: List[str] = None,
                   title: str = "Heatmap") -> str:
    """Create interactive heatmap.

    Args:
        data: 2D list of values
        x_labels: Labels for x axis
        y_labels: Labels for y axis
        title: Chart title

    Returns:
        HTML string of interactive chart
    """
    fig = go.Figure(data=go.Heatmap(
        z=data,
        x=x_labels,
        y=y_labels,
        colorscale='Viridis',
        showscale=True
    ))

    # Update layout
    fig.update_layout(
        title=title,
        template='plotly_white'
    )

    return pio.to_html(fig, full_html=False)


def create_pareto_chart(categories: List[str],
                       values: List[float],
                       title: str = "Pareto Chart") -> str:
    """Create interactive Pareto chart.

    Args:
        categories: Category names
        values: Values for each category
        title: Chart title

    Returns:
        HTML string of interactive chart
    """
    # Sort by value descending
    sorted_data = sorted(zip(categories, values), key=lambda x: x[1], reverse=True)
    sorted_categories = [x[0] for x in sorted_data]
    sorted_values = [x[1] for x in sorted_data]

    # Calculate cumulative percentage
    total = sum(sorted_values)
    cumulative = []
    running_sum = 0
    for val in sorted_values:
        running_sum += val
        cumulative.append(running_sum / total * 100)

    fig = go.Figure()

    # Add bars
    fig.add_trace(go.Bar(
        x=sorted_categories,
        y=sorted_values,
        name='Value',
        marker_color='blue'
    ))

    # Add cumulative line
    fig.add_trace(go.Scatter(
        x=sorted_categories,
        y=cumulative,
        name='Cumulative %',
        yaxis='y2',
        line=dict(color='red', width=2),
        mode='lines+markers'
    ))

    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title='Category',
        yaxis_title='Value',
        yaxis2=dict(
            title='Cumulative %',
            overlaying='y',
            side='right',
            range=[0, 100]
        ),
        showlegend=True,
        hovermode='closest',
        template='plotly_white'
    )

    return pio.to_html(fig, full_html=False)


def create_diagnostic_plots(regression_data: Dict[str, Any]) -> Dict[str, str]:
    """Create regression diagnostic plots.

    Args:
        regression_data: Regression analysis data

    Returns:
        Dictionary of HTML chart strings
    """
    plots = {}

    residuals = regression_data.get('residuals', {})
    fitted_values = regression_data.get('fitted_values', [])

    # Residuals vs Fitted
    if fitted_values and 'mean' in residuals:
        # Create synthetic residuals for visualization
        n = len(fitted_values)
        residual_values = np.random.normal(0, residuals.get('std', 1), n)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=fitted_values,
            y=residual_values,
            mode='markers',
            name='Residuals',
            marker=dict(size=8, color='blue')
        ))
        fig.add_hline(y=0, line_dash="dash", line_color="red")
        fig.update_layout(
            title='Residuals vs Fitted',
            xaxis_title='Fitted Values',
            yaxis_title='Residuals',
            showlegend=True,
            template='plotly_white'
        )
        plots['residuals_vs_fitted'] = pio.to_html(fig, full_html=False)

    # Q-Q Plot
    qq_plot = regression_data.get('qq_plot', {})
    if qq_plot:
        theoretical = qq_plot.get('theoretical', [])
        sample = qq_plot.get('sample', [])

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=theoretical,
            y=sample,
            mode='markers',
            name='Sample',
            marker=dict(size=8, color='blue')
        ))
        if theoretical and sample:
            min_val = min(min(theoretical), min(sample))
            max_val = max(max(theoretical), max(sample))
            fig.add_trace(go.Scatter(
                x=[min_val, max_val],
                y=[min_val, max_val],
                mode='lines',
                name='Reference',
                line=dict(color='red', dash='dash', width=2)
            ))
        fig.update_layout(
            title='Normal Q-Q Plot',
            xaxis_title='Theoretical Quantiles',
            yaxis_title='Sample Quantiles',
            showlegend=True,
            template='plotly_white'
        )
        plots['qq_plot'] = pio.to_html(fig, full_html=False)

    return plots
