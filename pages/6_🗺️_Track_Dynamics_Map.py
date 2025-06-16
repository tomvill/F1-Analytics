import streamlit as st
import fastf1 as ff1
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from utils.cache_utils import setup_fastf1_cache
import datetime
import matplotlib as mpl
from matplotlib import cm
import plotly.express as px

st.set_page_config(
    page_title="F1 Analytics - Track Dynamics Map",
    page_icon="🗺️",
    layout="wide"
)

st.title('🗺️ Track Dynamics Map')
st.markdown("""
This visualization displays the racing line of the fastest lap of a selected driver for a given race session with a track map with color gradients representing different telemetry data.
Each segment of the track is colored according to the selected metric, allowing you to analyze:
- **Speed**: Blue (slow) to red (fast) gradient showing speed variations around the track
- **Gear**: Different colors for each gear (1-8), highlighting shifting points
- **Throttle**: Green gradient from 0% to 100% showing throttle application
- **Brake**: Purple intensity showing braking zones

**Track Features**: White circles with red borders indicate corner numbers for easy reference and analysis.
""")

setup_fastf1_cache()

sidebar = st.sidebar
main_col1, main_col2 = st.columns([3, 1])  

with sidebar:
    st.header("Filters")
    
    current_year = 2024
    year = st.selectbox(
        "Select Year", 
        range(current_year, 2017, -1), 
        help="FastF1 provides reliable data from 2018 onwards"
    )
    
    try:
        events = ff1.get_event_schedule(year)
        race_events = events[events['EventFormat'] != 'testing']
        
        if race_events.empty:
            st.error(f"No race events found for {year}. Please select a different year.")
            st.stop()
            
        event_names = race_events['EventName'].tolist()
        circuit = st.selectbox("Select Grand Prix", event_names)
        
        selected_event = race_events[race_events['EventName'] == circuit].iloc[0]
        round_number = selected_event['RoundNumber']
        
    except Exception as e:
        st.error(f"Error loading event schedule: {e}")
        st.stop()
    
    session_type_name = "Race"
    session_key = "R"

    driver_placeholder = st.empty()
    
    telemetry_metrics = {
        "Speed": {
            "column": "Speed",
            "colormap": "plasma",
            "title": "Speed (km/h)",
            "reverse": False
        },
        "Gear": {
            "column": "nGear",
            "colormap": "Set1",
            "title": "Gear",
            "reverse": False,
            "discrete": True
        },
        "Throttle": {
            "column": "Throttle",
            "colormap": "Greens",
            "title": "Throttle (%)",
            "reverse": False
        },
        "Brake": {
            "column": "Brake",
            "colormap": "Purples",
            "title": "Brake",
            "reverse": False,
            "discrete": True
        }
    }
    
    selected_metric = st.selectbox(
        "Select Telemetry Metric", 
        list(telemetry_metrics.keys()),
        index=0
    )
    
    metric_info = telemetry_metrics[selected_metric]
    
    
@st.cache_data(show_spinner=False)
def load_session_data(year, round_number, session_key):
    try:
        session = ff1.get_session(year, round_number, session_key)
        session.load()
        
        if session.laps.empty:
            st.warning(f"No lap data available for this session. The data might not be available.")
            return None
            
        return session
    except Exception as e:
        st.error(f"Error loading session data: {e}")
        return None

def create_track_telemetry_map(telemetry_data, metric_info, driver_name, lap_info, circuit_info=None):
    metric_column = metric_info["column"]
    colormap_name = metric_info["colormap"]
    title = metric_info["title"]
    reverse = metric_info.get("reverse", False)
    is_discrete = metric_info.get("discrete", False)
    
    x = telemetry_data['X'].values
    y = telemetry_data['Y'].values
    
    if metric_column not in telemetry_data.columns:
        st.error(f"Metric {metric_column} not found in telemetry data")
        return go.Figure()
        
    color_values = telemetry_data[metric_column].values
    
    nan_positions = np.isnan(x) | np.isnan(y)
    nan_colors = np.isnan(color_values)
    
    gap_indices = []
    for i in range(len(x)):
        if nan_positions[i] or nan_colors[i]:
            gap_indices.append(i)
    
    points = np.column_stack([x, y])
    
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=x, 
        y=y,
        mode='lines',
        line=dict(color='black', width=10),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    if is_discrete:
        if metric_column == "nGear":
            unique_values = sorted(telemetry_data[metric_column].dropna().unique())
            if len(unique_values) == 0:
                st.warning("No valid gear data found")
                return fig
                
            max_value = int(max(unique_values))
            colorscale = []
            cmap = mpl.colormaps[colormap_name]
            if hasattr(cmap, 'resampled'):
                cmap = cmap.resampled(max_value)
            
            for i in range(max_value):
                norm_val = i / max_value
                rgba = cmap(i)
                color = f'rgba({rgba[0]*255}, {rgba[1]*255}, {rgba[2]*255}, {rgba[3]})'
                colorscale.append([norm_val, color])
                colorscale.append([(i+1)/max_value, color])
            
            z_min = 0
            z_max = max_value
            tick_vals = list(range(1, max_value + 1))
            tick_text = [f"Gear {i}" for i in tick_vals]
        
        elif metric_column in ["Brake", "DRS"]:
            colorscale = [[0, 'rgba(220, 220, 220, 0.8)'], [1, 'rgba(128, 0, 128, 1)']] if metric_column == "Brake" else [[0, 'rgba(220, 220, 220, 0.8)'], [1, 'rgba(0, 128, 0, 1)']]
            z_min = 0
            z_max = 1
            tick_vals = [0, 1]
            tick_text = ["Off", "On"]
    else:
        valid_values = color_values[~np.isnan(color_values)]
        if len(valid_values) == 0:
            st.warning(f"No valid {metric_column} data found")
            return fig
            
        z_min = min(valid_values)
        z_max = max(valid_values)
        
        cmap = mpl.colormaps[colormap_name]
        colorscale = []
        
        for i in range(11):
            val = i / 10
            rgba = cmap(val)
            color = f'rgba({rgba[0]*255}, {rgba[1]*255}, {rgba[2]*255}, {rgba[3]})'
            colorscale.append([val, color])
        
        step = (z_max - z_min) / 5
        tick_vals = [z_min + step * i for i in range(6)]
        tick_text = [f"{val:.0f}" for val in tick_vals]
    
    gap_segments = []
    
    for i in range(len(points) - 1):
        if nan_positions[i] or nan_positions[i+1]:
            gap_segments.append((i, i+1))
            continue
            
        if nan_colors[i]:
            gap_segments.append((i, i+1))
            continue
        
        value = color_values[i]
        
        if z_max > z_min:
            normalized_value = (value - z_min) / (z_max - z_min)
        else:
            normalized_value = 0.5
        
        if is_discrete:
            if metric_column == "nGear":
                if pd.notna(value):
                    gear_index = int(value) - 1  
                    if 0 <= gear_index < len(cmap.colors):
                        rgba = cmap.colors[gear_index]
                        color = f'rgba({rgba[0]*255}, {rgba[1]*255}, {rgba[2]*255}, {rgba[3]})'
                    else:
                        color = 'rgba(200, 200, 200, 0.8)' 
                else:
                    color = 'rgba(200, 200, 200, 0.8)'  
            else: 
                color = colorscale[0][1] if value == 0 else colorscale[1][1]
        else:
            
            for j in range(len(colorscale) - 1):
                lower_bound = colorscale[j][0]
                upper_bound = colorscale[j+1][0]
                
                if lower_bound <= normalized_value <= upper_bound:
                    lower_color = colorscale[j][1]
                    upper_color = colorscale[j+1][1]
                    
                    lower_rgba = [float(x) for x in lower_color.replace('rgba(', '').replace(')', '').split(',')]
                    upper_rgba = [float(x) for x in upper_color.replace('rgba(', '').replace(')', '').split(',')]
                    
                    factor = (normalized_value - lower_bound) / (upper_bound - lower_bound) if upper_bound > lower_bound else 0
                    
                    r = lower_rgba[0] + factor * (upper_rgba[0] - lower_rgba[0])
                    g = lower_rgba[1] + factor * (upper_rgba[1] - lower_rgba[1])
                    b = lower_rgba[2] + factor * (upper_rgba[2] - lower_rgba[2])
                    a = lower_rgba[3] + factor * (upper_rgba[3] - lower_rgba[3])
                    
                    color = f'rgba({r}, {g}, {b}, {a})'
                    break
            else:
                color = 'rgba(128, 128, 128, 0.8)' 
        
        fig.add_trace(go.Scatter(
            x=[points[i][0], points[i+1][0]],
            y=[points[i][1], points[i+1][1]],
            mode='lines',
            line=dict(
                color=color,
                width=6
            ),
            showlegend=False,
            hovertemplate=(
                f"Distance: {telemetry_data['Distance'].iloc[i]:.0f}m<br>" +
                f"{title}: " + (f"{color_values[i]:.0f}" if is_discrete else f"{color_values[i]:.1f}") +
                ("" if metric_column == "nGear" or metric_column == "Brake" else 
                 (" km/h" if metric_column == "Speed" else 
                  (" %" if metric_column == "Throttle" else ""))) + "<br>" +
                "<extra></extra>" 
            )
        ))
    
    for i, j in gap_segments:
        if (nan_positions[i] and nan_positions[j]) or (i >= len(points) or j >= len(points)):
            continue
            
        gap_color = 'rgba(150, 150, 150, 0.7)'  # Gray with some transparency
        
        fig.add_trace(go.Scatter(
            x=[points[i][0], points[j][0]],
            y=[points[i][1], points[j][1]],
            mode='lines',
            line=dict(
                color=gap_color,
                width=3,
                dash='dash'  
            ),
            showlegend=False,
            hovertemplate="Missing or invalid data in this segment"
        ))
    
    if is_discrete:
        if metric_column == "nGear":
            z = [[i] * 2 for i in range(1, z_max + 1)]
            colorbar_trace = go.Heatmap(
                z=z,
                colorscale=colorscale,
                showscale=True,
                visible=False,
                colorbar=dict(
                    title=title,
                    tickvals=tick_vals,
                    ticktext=tick_text,
                    len=0.5,
                    y=0.5
                )
            )
            fig.add_trace(colorbar_trace)
        elif metric_column in ["Brake", "DRS"]:
            z = [[0, 0], [1, 1]]
            colorbar_trace = go.Heatmap(
                z=z,
                colorscale=colorscale,
                showscale=True,
                visible=False,
                colorbar=dict(
                    title=title,
                    tickvals=tick_vals,
                    ticktext=tick_text,
                    len=0.5,
                    y=0.5
                )
            )
            fig.add_trace(colorbar_trace)
    else:
        z = [[i * (z_max - z_min) / 10 + z_min for i in range(11)] for _ in range(2)]
        colorbar_trace = go.Heatmap(
            z=z,
            colorscale=colorscale,
            showscale=True,
            visible=False,
            zmin=z_min,
            zmax=z_max,
            colorbar=dict(
                title=title,
                tickvals=tick_vals,
                ticktext=tick_text,
                len=0.5,
                y=0.5
            )
        )
        fig.add_trace(colorbar_trace)
    
    if len(gap_segments) > 0:
        fig.add_annotation(
            x=0.02,
            y=0.98,
            xref="paper",
            yref="paper",
            text="Dashed lines indicate missing or invalid data",
            showarrow=False,
            bgcolor="rgba(255, 255, 255, 0.7)",
            bordercolor="gray",
            borderwidth=1,
            font=dict(size=10),
            align="left"
        )
    
    # Add corner markers if circuit info is available
    if circuit_info is not None and hasattr(circuit_info, 'corners') and not circuit_info.corners.empty:
        corners_df = circuit_info.corners
        # Add corner markers
        fig.add_trace(go.Scatter(
            x=corners_df['X'],
            y=corners_df['Y'],
            mode='markers+text',
            marker=dict(
                color='rgba(255, 255, 255, 0.8)',
                size=8,
                line=dict(color='#FF1E00', width=2)
            ),
            text=corners_df['Number'].astype(str),
            textposition='middle center',
            textfont=dict(color='#FF1E00', size=10, family='Arial Black'),
            name='Corners',
            showlegend=False,
            hovertemplate=(
                "Corner %{text}<br>" +
                "<extra></extra>"
            )
        ))
    
    lap_text = f"Lap {lap_info['LapNumber']}" if 'LapNumber' in lap_info else "Fastest Lap"
    lap_time = lap_info.get('LapTime', None)
    lap_time_str = ""
    
    if lap_time is not None and not pd.isna(lap_time) and not isinstance(lap_time, pd.Series):
        try:
            lap_time_str = str(lap_time).split('.')[0] + '.' + str(lap_time).split('.')[1][:3]
            lap_time_str = lap_time_str[2:] if lap_time_str.startswith('0:') else lap_time_str
        except (IndexError, AttributeError):
            lap_time_str = str(lap_time)
    
    title_text = f"{driver_name} - {circuit} {year} {session_type_name} - {lap_text}"
    
    fig.update_layout(
        title=dict(
            text=title_text,
            x=0.5,
            xanchor='center'
        ),
        showlegend=False,
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            scaleanchor="x",
            scaleratio=1
        ),
        autosize=True,
        margin=dict(l=20, r=20, t=80, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=800,
        hoverlabel=dict(
            bgcolor="rgba(0, 0, 0, 0.8)",
            bordercolor="#FF1E00",
            font=dict(size=14, color="white", family="Arial")
        )
    )
    
    return fig

with st.spinner("Loading session data... This may take a moment."):
    session = load_session_data(year, round_number, session_key)

if session is None:
    st.warning("No data available for the selected session. Please try a different circuit, year, or session type.")
    st.stop()

drivers = session.laps['Driver'].unique().tolist()

with driver_placeholder.container():
    selected_driver = st.selectbox(
        "Select Driver",
        drivers,
        help="Select a driver to visualize their telemetry data on the track map"
    )

driver_laps = session.laps.pick_drivers(selected_driver)

if driver_laps.empty:
    st.warning(f"No lap data available for {selected_driver} in this session.")
    st.stop()

available_laps = sorted(driver_laps['LapNumber'].astype(int).unique().tolist())

lap_number_placeholder = st.sidebar.empty()
selected_lap_number = None


try:
    selected_lap = driver_laps.pick_fastest()
    if selected_lap is None or selected_lap.empty:
        st.warning(f"No fastest lap available for {selected_driver}. This could be due to a DNF (Did Not Finish) or insufficient lap data.")
        st.info("Please try selecting a different driver or check if this driver completed any valid laps in this session.")
        st.stop()
except Exception as e:
    st.error(f"Error getting fastest lap: {e}")
    st.info("This error often occurs when a driver has a DNF (Did Not Finish) or no valid lap times. Please try selecting a different driver.")
    st.stop()

try:
    telemetry = selected_lap.get_telemetry()
    if telemetry.empty:
        st.warning(f"No telemetry data available for the selected lap.")
        st.stop()
    
    metric_column = metric_info["column"]
    if metric_column not in telemetry.columns:
        st.warning(f"{metric_column} data not available for this lap. Available columns: {telemetry.columns.tolist()}")
        st.stop()
        
    if 'X' not in telemetry.columns or 'Y' not in telemetry.columns:
        st.warning("Track position data (X, Y coordinates) not available for this lap.")
        st.stop()
        
except Exception as e:
    st.error(f"Error loading telemetry data: {e}")
    st.stop()

try:
    lap_info = {}
    
    if 'LapNumber' in selected_lap and not isinstance(selected_lap['LapNumber'], pd.Series):
        lap_info['LapNumber'] = selected_lap['LapNumber']
    else:
        lap_info['LapNumber'] = selected_lap_number if selected_lap_number is not None else "Unknown"
    
    if 'LapTime' in selected_lap and not isinstance(selected_lap['LapTime'], pd.Series):
        lap_info['LapTime'] = selected_lap['LapTime']
    
    circuit_info = session.get_circuit_info()
    
    fig = create_track_telemetry_map(telemetry, metric_info, selected_driver, lap_info, circuit_info)
    
    with main_col1:
        st.plotly_chart(fig, use_container_width=True)
    
    with main_col2:
        st.markdown("""
        <style>
        .f1-header {
            background: linear-gradient(135deg, #15151E 0%, #2a2a3e 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            border-left: 4px solid #FF1E00;
            margin-bottom: 20px;
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
            padding: 8px 12px;
            margin: 6px 0;
            border-left: 2px solid #FF1E00;
        }
        .f1-time {
            font-family: 'Monaco', 'Consolas', monospace;
            font-size: 24px;
            font-weight: bold;
            color: #FF1E00;
            text-align: center;
            margin: 10px 0;
        }
        .f1-label {
            color: #b0b0b0;
            font-size: 14px;
            margin-bottom: 4px;
        }
        .f1-value {
            color: white;
            font-weight: 600;
            font-size: 16px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Driver Header
        st.markdown(f"""
        <div class="f1-header">
            <h2 style="margin: 0; color: white;">🏎️ {selected_driver}</h2>
            <p style="margin: 8px 0 0 0; color: #b0b0b0;">{circuit} • {year}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Lap Time - Main Feature
        lap_time = selected_lap.get('LapTime', None)
        if lap_time is not None and not pd.isna(lap_time) and not isinstance(lap_time, pd.Series):
            try:
                # Convert lap time to full format: 00:01:32.608
                lap_time_str = str(lap_time)
                
                # Handle different formats that FastF1 might return
                if 'days' in lap_time_str:
                    # Remove days part if present
                    lap_time_str = lap_time_str.split('days ')[-1]
                
                # Ensure we have the full HH:MM:SS.mmm format
                if lap_time_str.count(':') == 1:  # Format: MM:SS.mmm
                    lap_time_str = f"00:{lap_time_str}"
                elif lap_time_str.count(':') == 0:  # Format: SS.mmm
                    lap_time_str = f"00:00:{lap_time_str}"
                
                # Ensure milliseconds are present and properly formatted
                if '.' not in lap_time_str:
                    lap_time_str = f"{lap_time_str}.000"
                else:
                    # Ensure we have exactly 3 decimal places
                    time_parts = lap_time_str.split('.')
                    if len(time_parts) > 1:
                        milliseconds = time_parts[1][:3].ljust(3, '0')  # Take first 3 digits, pad if needed
                        lap_time_str = f"{time_parts[0]}.{milliseconds}"
                
            except (IndexError, AttributeError, ValueError):
                lap_time_str = str(lap_time)
        else:
            lap_time_str = "N/A"
        
        st.markdown(f"""
        <div class="f1-section">
            <div class="f1-label">Lap {selected_lap['LapNumber']} Time</div>
            <div class="f1-time">{lap_time_str}</div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("🏎️ Tire Information", expanded=False):
            compound = selected_lap.get('Compound', None)
            tyre_life = selected_lap.get('TyreLife', None)
            
            if compound is not None and not pd.isna(compound):
                if compound.upper() == "SOFT":
                    tire_color = "#FF1E00"  
                elif compound.upper() == "MEDIUM":
                    tire_color = "#FFD700"  
                elif compound.upper() == "HARD":
                    tire_color = "#C0C0C0"  
                elif compound.upper() == "INTERMEDIATE":
                    tire_color = "#00D400" 
                elif compound.upper() == "WET":
                    tire_color = "#0080FF"  
                else:
                    tire_color = "#888888"  
                
                st.markdown(f"""
                    <div class="f1-metric">
                        <span style="color: #b0b0b0;">Compound:</span>
                        <span style="color: {tire_color}; float: right;">● {compound}</span>
                    </div>
                """, unsafe_allow_html=True)
                
                if tyre_life is not None and not pd.isna(tyre_life):
                    st.markdown(f"""
                    <div class="f1-metric">
                        <span style="color: #b0b0b0;">Tire Life:</span>
                        <span style="color: white; float: right;">{tyre_life} laps</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="f1-metric">
                        <span style="color: #b0b0b0;">Tyre Life:</span>
                        <span style="color: #888888; float: right;">N/A</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div class="f1-metric">
                        <span style="color: #b0b0b0;">Compound:</span>
                        <span style="color: #888888; float: right;">N/A</span>
                    </div>
                    <div class="f1-metric">
                        <span style="color: #b0b0b0;">Tyre Life:</span>
                        <span style="color: #888888; float: right;">N/A</span>
                    </div>
                """, unsafe_allow_html=True)
        
        with st.expander("Speed Analysis", expanded=False):
            max_speed = telemetry['Speed'].max()
            avg_speed = telemetry['Speed'].mean()
            min_speed = telemetry['Speed'].min()
            
            st.markdown(f"""
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
            """, unsafe_allow_html=True)
        
        with st.expander("Performance Metrics", expanded=False):
            performance_data = []
            
            if 'Throttle' in telemetry.columns:
                avg_throttle = telemetry['Throttle'].mean()
                full_throttle_pct = (telemetry['Throttle'] > 95).mean() * 100
                performance_data.extend([
                    ("Average Throttle %", f"{avg_throttle:.1f}%")
                ])
            
            if 'Brake' in telemetry.columns:
                brake_pct = telemetry['Brake'].mean() * 100
                performance_data.append(("Average Braking %", f"{brake_pct:.1f}%"))
            
            if 'RPM' in telemetry.columns:
                max_rpm = telemetry['RPM'].max()
                performance_data.append(("Max Rpm", f"{max_rpm:.0f}"))
            
            if performance_data:
                for label, value in performance_data:
                    st.markdown(f"""
                    <div class="f1-metric">
                        <span style="color: #b0b0b0;">{label}</span>
                        <span style="color: white; float: right;">{value}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("**Performance data not available**")
        
        
except Exception as e:
    st.error(f"Error creating visualization: {e}")
    import traceback
    st.code(traceback.format_exc())
