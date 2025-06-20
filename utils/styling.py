"""
F1 Analytics - Centralized Styling Utilities

This module provides consistent F1-themed styling for all visualizations.
"""

import streamlit as st
from typing import Dict, Any

F1_COLORS = {
    'primary_red': '#FF1E00',
    'dark_bg': '#15151E', 
    'secondary_dark': '#2a2a3e',
    'text_primary': '#ffffff',
    'text_secondary': '#b0b0b0',
    'text_labels': '#888888',
    'tire_soft': '#FF1E00',
    'tire_medium': '#FFD700',
    'tire_hard': '#C0C0C0',
    'tire_intermediate': '#00D400',
    'tire_wet': '#0080FF'
}

def get_f1_css() -> str:
    """
    Returns the complete F1-themed CSS styling.
    
    Returns:
        str: CSS styling string for F1 theme
    """
    return f"""
    <style>
    .f1-header {{
        background: linear-gradient(135deg, {F1_COLORS['dark_bg']} 0%, {F1_COLORS['secondary_dark']} 100%);
        color: {F1_COLORS['text_primary']};
        padding: 20px;
        border-radius: 12px;
        border-left: 4px solid {F1_COLORS['primary_red']};
        margin-bottom: 20px;
        text-align: center;
    }}
    .f1-title {{
        background: linear-gradient(135deg, {F1_COLORS['dark_bg']} 0%, {F1_COLORS['secondary_dark']} 100%);
        color: white;
        padding: 30px;
        border-radius: 12px;
        border-left: 4px solid {F1_COLORS['primary_red']};
        margin-bottom: 30px;
        text-align: center;
    }}
    .f1-section {{
        background: rgba(21, 21, 30, 0.6);
        border: 1px solid rgba(255, 30, 0, 0.2);
        border-radius: 8px;
        padding: 16px;
        margin: 12px 0;
        backdrop-filter: blur(10px);
    }}
    .f1-metric {{
        background: rgba(255, 255, 255, 0.05);
        border-radius: 6px;
        padding: 8px 12px;
        margin: 6px 0;
        border-left: 2px solid {F1_COLORS['primary_red']};
        color: white;
    }}
    .f1-time {{
        font-family: 'Monaco', 'Consolas', monospace;
        font-size: 24px;
        font-weight: bold;
        color: {F1_COLORS['primary_red']};
        text-align: center;
        margin: 10px 0;
    }}
    .f1-label {{
        color: {F1_COLORS['text_secondary']};
        font-size: 14px;
        margin-bottom: 4px;
    }}
    .f1-value {{
        color: {F1_COLORS['text_primary']};
        font-weight: 600;
        font-size: 16px;
    }}
    .f1-stats-header {{
        background: linear-gradient(90deg, {F1_COLORS['dark_bg']} 0%, {F1_COLORS['secondary_dark']} 100%);
        color: {F1_COLORS['text_primary']};
        padding: 12px 16px;
        border-radius: 8px;
        border-left: 3px solid {F1_COLORS['primary_red']};
        margin: 8px 0;
        text-align: center;
        font-weight: bold;
    }}
    .f1-stat-item {{
        background: rgba(255, 255, 255, 0.05);
        padding: 8px 12px;
        margin: 4px 0;
        border-radius: 4px;
        border-left: 1px solid {F1_COLORS['primary_red']};
        font-family: 'Monaco', 'Consolas', monospace;
    }}
    .f1-stat-value {{
        font-family: 'Monaco', 'Consolas', monospace;
        font-size: 24px;
        font-weight: bold;
        color: {F1_COLORS['primary_red']};
        text-align: center;
    }}
    .f1-stat-label {{
        color: {F1_COLORS['text_secondary']};
        font-size: 14px;
        text-align: center;
        margin-bottom: 8px;
    }}
    </style>
    """

def get_position_overtake_css() -> str:
    """
    Returns the CSS styles specifically for Position & Overtake Insights page.
    
    Returns:
        str: CSS styling string for Position & Overtake page
    """
    return """
    <style>
    .f1-title {
        background: linear-gradient(135deg, #15151E 0%, #2a2a3e 100%);
        color: white;
        padding: 30px;
        border-radius: 12px;
        border-left: 4px solid #FF1E00;
        margin-bottom: 30px;
        text-align: center;
    }
    .f1-section {
        background: rgba(21, 21, 30, 0.6);
        border: 1px solid rgba(255, 30, 0, 0.2);
        border-radius: 8px;
        padding: 16px;
        margin: 12px 0;
        backdrop-filter: blur(10px);
    }
    .f1-metric {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 6px;
        padding: 12px;
        margin: 8px 0;
        border-left: 2px solid #FF1E00;
        color: white;
    }
    .f1-stat-value {
        font-family: 'Monaco', 'Consolas', monospace;
        font-size: 24px;
        font-weight: bold;
        color: #FF1E00;
        text-align: center;
    }
    .f1-stat-label {
        color: #b0b0b0;
        font-size: 14px;
        text-align: center;
        margin-bottom: 8px;
    }
    </style>
    """

def apply_f1_styling():
    """Apply F1 theme styling to the current Streamlit page."""
    st.markdown(get_f1_css(), unsafe_allow_html=True)

def get_f1_plotly_layout(title: str = "", height: int = 800) -> Dict[str, Any]:
    """
    Get standardized F1-themed Plotly layout configuration.
    
    Args:
        title (str): Chart title
        height (int): Chart height in pixels
        
    Returns:
        Dict[str, Any]: Plotly layout configuration
    """
    return {
        'title': {
            'text': title,
            'x': 0.5,
            'xanchor': 'center',
            'font': {
                'size': 18,
                'color': F1_COLORS['text_primary'],
                'family': 'Arial, sans-serif'
            }
        },
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'height': height,
        'margin': dict(l=20, r=20, t=80, b=20),
        'font': {
            'color': F1_COLORS['text_primary'],
            'family': 'Arial, sans-serif'
        },
        'hoverlabel': {
            'bgcolor': 'rgba(0, 0, 0, 0.8)',
            'bordercolor': F1_COLORS['primary_red'],
            'font': {
                'size': 14, 
                'color': F1_COLORS['text_primary'], 
                'family': 'Arial'
            }
        },
        'colorway': [F1_COLORS['primary_red'], F1_COLORS['tire_medium'], F1_COLORS['tire_hard'], 
                    F1_COLORS['tire_intermediate'], F1_COLORS['tire_wet']]
    }

def get_f1_heatmap_colorscale() -> list:
    """
    Get F1-themed colorscale for heatmaps.
    
    Returns:
        list: Plotly colorscale configuration
    """
    return [
        [0.0, f"rgba(0, 100, 0, 0.8)"],      # Dark green for best times
        [0.2, f"rgba(50, 150, 0, 0.7)"],     # Green
        [0.4, f"rgba(150, 200, 0, 0.6)"],    # Yellow-green
        [0.6, f"rgba(255, 200, 0, 0.7)"],    # Yellow
        [0.8, f"rgba(255, 100, 0, 0.8)"],    # Orange
        [1.0, f"rgba(255, 30, 0, 0.9)"]      # F1 Red for worst times
    ]

def create_f1_header(title: str, subtitle: str = "") -> str:
    """
    Create a standardized F1-themed header.
    
    Args:
        title (str): Main title text
        subtitle (str): Optional subtitle text
        
    Returns:
        str: HTML string for the header
    """
    subtitle_html = f"<p style='margin: 8px 0 0 0; color: {F1_COLORS['text_secondary']};'>{subtitle}</p>" if subtitle else ""
    
    return f"""
    <div class="f1-header">
        <h2 style="margin: 0; color: {F1_COLORS['text_primary']};">{title}</h2>
        {subtitle_html}
    </div>
    """

def create_f1_metric_card(label: str, value: str, description: str = "") -> str:
    """
    Create a standardized F1-themed metric card.
    
    Args:
        label (str): Metric label
        value (str): Metric value
        description (str): Optional description
        
    Returns:
        str: HTML string for the metric card
    """
    desc_html = f"<p style='margin: 4px 0 0 0; color: {F1_COLORS['text_labels']}; font-size: 12px;'>{description}</p>" if description else ""
    
    return f"""
    <div class="f1-section">
        <div class="f1-label">{label}</div>
        <div class="f1-time">{value}</div>
        {desc_html}
    </div>
    """

def get_tire_color(compound: str) -> str:
    """
    Get the F1 official tire compound color.
    
    Args:
        compound (str): Tire compound name
        
    Returns:
        str: Hex color code
    """
    compound_upper = compound.upper()
    tire_colors = {
        'SOFT': F1_COLORS['tire_soft'],
        'MEDIUM': F1_COLORS['tire_medium'], 
        'HARD': F1_COLORS['tire_hard'],
        'INTERMEDIATE': F1_COLORS['tire_intermediate'],
        'WET': F1_COLORS['tire_wet']
    }
    return tire_colors.get(compound_upper, F1_COLORS['text_labels'])

def create_f1_driver_card(driver_display_name: str, team_name: str, team_color: str, 
                         driver_number: str, position: str, dnf_status: bool, 
                         driver_headshot: str, circuit: str, year: int) -> str:
    """
    Create a F1-styled driver information card with photo and team details.
    
    Args:
        driver_display_name (str): Full driver name
        team_name (str): Team name
        team_color (str): Team color hex code
        driver_number (str): Driver number
        position (str): Race position
        dnf_status (bool): Whether driver DNF'd
        driver_headshot (str): URL to driver headshot image
        circuit (str): Circuit name
        year (int): Race year
        
    Returns:
        str: HTML string for the driver card
    """
    headshot_html = f"<img src='{driver_headshot}' style='width: 100%; height: 100%; object-fit: cover;' />" if driver_headshot else "<span style='font-size: 24px;'>🏎️</span>"
    driver_number_html = f'<span style="color: #b0b0b0; font-size: 12px;">#{driver_number}</span>' if driver_number else ''
    
    if dnf_status:
        status_html = '<span style="color: #FF1E00; font-size: 12px; font-weight: bold;">⚠️ DNF</span>'
    elif position:
        status_html = f'<span style="color: #00D400; font-size: 12px; font-weight: bold;">🏁 P{position}</span>'
    else:
        status_html = ''
    
    return f"""
    <div style="
        background: linear-gradient(135deg, rgba(21, 21, 30, 0.95) 0%, rgba(42, 42, 62, 0.85) 100%);
        border: 1px solid rgba(255, 30, 0, 0.3);
        border-left: 4px solid {team_color};
        border-radius: 12px;
        padding: 16px;
        margin: 16px 0;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    ">
        <div style="display: flex; align-items: center; gap: 16px;">
            <div style="
                width: 70px; 
                height: 70px; 
                border-radius: 50%; 
                overflow: hidden;
                border: 2px solid {team_color};
                background: rgba(255, 255, 255, 0.1);
                display: flex;
                align-items: center;
                justify-content: center;
            ">
                {headshot_html}
            </div>
            <div style="flex: 1;">
                <h2 style="
                    color: white; 
                    margin: 0 0 4px 0; 
                    font-size: 20px; 
                    font-weight: bold;
                    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
                ">{driver_display_name}</h2>
                <div style="
                    color: {team_color}; 
                    font-size: 14px; 
                    font-weight: 600;
                    margin-bottom: 4px;
                ">● {team_name}</div>
                <div style="display: flex; gap: 12px; align-items: center;">
                    {driver_number_html}
                    {status_html}
                </div>
                <div style="
                    color: #888888; 
                    font-size: 12px; 
                    margin-top: 4px;
                ">{circuit} • {year}</div>
            </div>
        </div>
    </div>
    """

def create_f1_tire_info_metric(compound: str, tire_color: str) -> str:
    """
    Create a F1-themed tire information metric.
    
    Args:
        compound (str): Tire compound name
        tire_color (str): Tire color hex code
        
    Returns:
        str: HTML string for tire info metric
    """
    return f"""
    <div class="f1-metric">
        <span style="color: #b0b0b0;">Compound:</span>
        <span style="color: {tire_color}; float: right;">● {compound}</span>
    </div>
    """

def create_f1_tire_life_metric(tyre_life: int) -> str:
    """
    Create a F1-themed tire life metric.
    
    Args:
        tyre_life (int): Number of laps on tire
        
    Returns:
        str: HTML string for tire life metric
    """
    return f"""
    <div class="f1-metric">
        <span style="color: #b0b0b0;">Tire Life:</span>
        <span style="color: white; float: right;">{tyre_life} laps</span>
    </div>
    """

def create_f1_tire_na_metrics() -> str:
    """
    Create F1-themed tire metrics for when data is not available.
    
    Returns:
        str: HTML string for N/A tire metrics
    """
    return """
    <div class="f1-metric">
        <span style="color: #b0b0b0;">Compound:</span>
        <span style="color: #888888; float: right;">N/A</span>
    </div>
    <div class="f1-metric">
        <span style="color: #b0b0b0;">Tyre Life:</span>
        <span style="color: #888888; float: right;">N/A</span>
    </div>
    """

def create_f1_tire_life_na_metric() -> str:
    """
    Create F1-themed tire life metric for when data is not available.
    
    Returns:
        str: HTML string for N/A tire life metric
    """
    return """
    <div class="f1-metric">
        <span style="color: #b0b0b0;">Tyre Life:</span>
        <span style="color: #888888; float: right;">N/A</span>
    </div>
    """

def create_f1_speed_metrics(max_speed: float, avg_speed: float, min_speed: float) -> str:
    """
    Create F1-themed speed analysis metrics.
    
    Args:
        max_speed (float): Maximum speed
        avg_speed (float): Average speed
        min_speed (float): Minimum speed
        
    Returns:
        str: HTML string for speed metrics
    """
    return f"""
    <div class="f1-metric">
        <span style="color: #b0b0b0;">Max</span>
        <span style="color: white; float: right;">{max_speed:.1f} km/h</span>
    </div>
    <div class="f1-metric">
        <span style="color: #b0b0b0;">Avg</span>
        <span style="color: white; float: right;">{avg_speed:.1f} km/h</span>
    </div>
    <div class="f1-metric">
        <span style="color: #b0b0b0;">Min</span>
        <span style="color: white; float: right;">{min_speed:.1f} km/h</span>
    </div>
    """

def create_f1_performance_metric(label: str, value: str) -> str:
    """
    Create a single F1-themed performance metric.
    
    Args:
        label (str): Metric label
        value (str): Metric value
        
    Returns:
        str: HTML string for performance metric
    """
    return f"""
    <div class="f1-metric">
        <span style="color: #b0b0b0;">{label}</span>
        <span style="color: white; float: right;">{value}</span>
    </div>
    """

def create_f1_stat_card(label: str, value: str, description: str = "") -> str:
    """
    Create a F1-themed statistic card for race insights.
    
    Args:
        label (str): Statistic label
        value (str): Statistic value
        description (str): Optional description text
        
    Returns:
        str: HTML string for stat card
    """
    desc_html = f'<div style="color: #b0b0b0; font-size: 12px; text-align: center;">{description}</div>' if description else ''
    
    return f"""
    <div class="f1-metric">
        <div class="f1-stat-label">{label}</div>
        <div class="f1-stat-value">{value}</div>
        {desc_html}
    </div>
    """
