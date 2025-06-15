import streamlit as st
import fastf1 as ff1
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
from datetime import timedelta

st.set_page_config(
    page_title="F1 Analytics - Sector Performance Heatmap",
    page_icon="📊",
    layout="wide"
)

st.title('📊 Sector Performance Heatmap')
st.markdown("""
This visualization shows sector performance data across laps. Each cell represents the time difference (delta) 
between a sector time and the driver's personal best time for that sector. Dark green indicates personal best times, 
while progressively warmer colors (yellow, orange, red) indicate increasing time deltas. The color scale is optimized
to highlight even small differences in performance. The heatmap is joined with sector statistics, including the top 3 sector times for the selected driver.
""")

ff1.Cache.enable_cache('.fast-f1-cache')

with st.sidebar:
    
    current_year = 2024  
    year = st.selectbox("Select Year", range(current_year, 2017, -1), 
                        help="FastF1 provides reliable data from 2018 onwards")
    
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
        
        session_type = "Race"
        session_key = "R" 
        
    
    except Exception as e:
        st.error(f"Error loading event schedule: {e}")
        st.stop()

@st.cache_data(show_spinner=False)
def load_session_data(year, round_number, session_key):
    try:
        session = ff1.get_session(year, round_number, session_key)
        session.load()
        
        if session.laps.empty:
            st.warning(f"No lap data available for this race session. The data might not be available.")
            return None
            
        return session
    except Exception as e:
        st.error(f"Error loading session data: {e}")
        return None

with st.spinner("Loading race session data... This may take a moment."):
    session = load_session_data(year, round_number, session_key)

if session is None:
    st.warning("No data available for the selected session. Please try a different circuit or year.")
    st.stop()

laps_data = session.laps


drivers = laps_data['Driver'].unique().tolist()

with st.sidebar:
    selected_driver = st.selectbox(
        "Select Driver", 
        drivers,
        help="Select a driver to analyze their sector performance"
    )

    laps_data = laps_data.pick_driver(selected_driver)
    st.success(f"Data filtered to show {selected_driver}'s laps")

def timedelta_to_seconds(td):
    if pd.isna(td):
        return None
    if isinstance(td, timedelta):
        return td.total_seconds()
    try:
        return float(td)
    except:
        return None

def prepare_heatmap_data(laps_data, driver=None):
    if driver:
        driver_laps = laps_data.pick_driver(driver)
    else:
        driver_laps = laps_data
    
    valid_laps = driver_laps.dropna(subset=['Sector1Time', 'Sector2Time', 'Sector3Time'])
    
    if valid_laps.empty:
        return None, None
    
    valid_laps['S1_seconds'] = valid_laps['Sector1Time'].apply(timedelta_to_seconds)
    valid_laps['S2_seconds'] = valid_laps['Sector2Time'].apply(timedelta_to_seconds)
    valid_laps['S3_seconds'] = valid_laps['Sector3Time'].apply(timedelta_to_seconds)
    
    valid_laps = valid_laps.dropna(subset=['S1_seconds', 'S2_seconds', 'S3_seconds'])
    
    if valid_laps.empty:
        return None, None
    
    s1_benchmark = valid_laps['S1_seconds'].min()
    s2_benchmark = valid_laps['S2_seconds'].min()
    s3_benchmark = valid_laps['S3_seconds'].min()
    
    valid_laps['S1_delta'] = valid_laps['S1_seconds'] - s1_benchmark
    valid_laps['S2_delta'] = valid_laps['S2_seconds'] - s2_benchmark
    valid_laps['S3_delta'] = valid_laps['S3_seconds'] - s3_benchmark
    
    heatmap_data = valid_laps[['LapNumber', 'S1_delta', 'S2_delta', 'S3_delta']].copy()
    
    heatmap_data = heatmap_data.set_index('LapNumber')
    
    heatmap_data.columns = ['Sector 1', 'Sector 2', 'Sector 3']
    
    return heatmap_data, valid_laps

def create_sector_heatmap(heatmap_data, driver_name, colorscale='RdYlGn_r'):
    z_data = heatmap_data.values
    
    sectors = ["Sector 1", "Sector 2", "Sector 3"]
    
    lap_numbers = heatmap_data.index.tolist()
    
    
    all_deltas = heatmap_data.values.flatten()
    all_deltas = all_deltas[~np.isnan(all_deltas)]  # Remove NaN values
    
    max_delta = np.max(all_deltas)
    
    non_zero_deltas = all_deltas[all_deltas > 0]
    if len(non_zero_deltas) > 0:
        p25 = np.percentile(non_zero_deltas, 25)
        p50 = np.percentile(non_zero_deltas, 50)
        p75 = np.percentile(non_zero_deltas, 75)
        
        effective_max = np.percentile(non_zero_deltas, 95)
    else:
        p25 = max_delta * 0.25
        p50 = max_delta * 0.5
        p75 = max_delta * 0.75
        effective_max = max_delta
    
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=sectors,
        y=lap_numbers,
        colorscale=colorscale,
        zmin=0, 
        zmax=effective_max,  
        text=[[f"{val:.3f}s" for val in row] for row in z_data],
        hovertemplate="Lap: %{y}<br>%{x}: %{text}<br>",
        colorbar=dict(
            title="Time Above Personal Best (s)",
            tickvals=[0, p25, p50, p75, effective_max],
            ticktext=["Personal Best", f"+{p25:.3f}s", f"+{p50:.3f}s", f"+{p75:.3f}s", f"+{effective_max:.3f}s"]
        )
    ))
    
    title_text = f"{driver_name} Sector Performance vs Personal Best"
    
    fig.update_layout(
        title=title_text,
        xaxis_title="Track Sector",
        yaxis_title="Lap Number",
        yaxis=dict(autorange="reversed"),  # To have lap 1 at the top
        height=800,
        width=1000,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    return fig

heatmap_data, valid_laps = prepare_heatmap_data(laps_data, selected_driver)

if heatmap_data is None:
    st.warning(f"No sector data available for {selected_driver} in this session.")
else:
    
    
    with st.expander("Sector Statistics", expanded=False):

        
        def get_top_n_sectors(data, sector_col, n=3):
            top_sectors = data.sort_values(by=sector_col).head(n).copy()
            top_sectors['formatted_time'] = top_sectors[sector_col].apply(
                lambda x: str(timedelta(seconds=x)).split('.')[0] + '.' + 
                          str(timedelta(seconds=x)).split('.')[1][:3]
            )
            top_sectors['formatted_time'] = top_sectors['formatted_time'].apply(
                lambda x: x[2:] if x.startswith('0:') else x
            )
            return top_sectors
        
        top_s1 = get_top_n_sectors(valid_laps, 'S1_seconds')
        top_s2 = get_top_n_sectors(valid_laps, 'S2_seconds')
        top_s3 = get_top_n_sectors(valid_laps, 'S3_seconds')
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Sector 1")
            for i, (_, row) in enumerate(top_s1.iterrows(), 1):
                st.markdown(f"**#{i}:** {row['formatted_time']} (Lap {int(row['LapNumber'])})")
            
        with col2:
            st.subheader("Sector 2")
            for i, (_, row) in enumerate(top_s2.iterrows(), 1):
                st.markdown(f"**#{i}:** {row['formatted_time']} (Lap {int(row['LapNumber'])})")
            
        with col3:
            st.subheader("Sector 3")
            for i, (_, row) in enumerate(top_s3.iterrows(), 1):
                st.markdown(f"**#{i}:** {row['formatted_time']} (Lap {int(row['LapNumber'])})")
        
        theoretical_best = valid_laps['S1_seconds'].min() + valid_laps['S2_seconds'].min() + valid_laps['S3_seconds'].min()
        theoretical_best_time = timedelta(seconds=theoretical_best)
        theoretical_best_str = f"{theoretical_best_time.seconds // 60}:{theoretical_best_time.seconds % 60:02d}.{theoretical_best_time.microseconds // 1000:03d}"
        
        try:
            best_lap = valid_laps.loc[valid_laps['LapTime'].apply(timedelta_to_seconds).idxmin()]
            best_lap_time = timedelta_to_seconds(best_lap['LapTime'])
            best_lap_time_delta = timedelta(seconds=best_lap_time - theoretical_best)
            best_lap_time_delta_str = f"+{best_lap_time_delta.seconds}.{best_lap_time_delta.microseconds // 1000:03d}"
            
            best_lap_time = timedelta(seconds=best_lap_time)
            best_lap_time_str = f"{best_lap_time.seconds // 60}:{best_lap_time.seconds % 60:02d}.{best_lap_time.microseconds // 1000:03d}"
            
            st.markdown("""
            ### Lap Analysis
            
            This analysis compares the driver's actual best lap with a theoretical best lap time.
            The theoretical best combines the fastest sectors from any lap, showing the potential if the driver could perform perfectly across all sectors in a single lap.
            The difference indicates how much improvement might be possible under ideal conditions.
            """)
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Theoretical Best Lap", theoretical_best_str, "Perfect sectors")
                
            with col2:
                st.metric("Actual Best Lap", best_lap_time_str, f"{best_lap_time_delta_str} vs theoretical")
        except:
            st.metric("Theoretical Best Lap", theoretical_best_str, "Perfect sectors")
            st.warning("Could not calculate actual best lap time")
    fig = create_sector_heatmap(heatmap_data, selected_driver)
    st.plotly_chart(fig, use_container_width=True)

