import fastf1 as ff1
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import plotly.express as px

from utils.cache_utils import setup_fastf1_cache
from utils.styling import get_position_overtake_css, create_f1_stat_card, team_colors

st.set_page_config(
    page_title="F1 Analytics - Overtake Insights", 
    page_icon="💨", 
    layout="wide"
)

st.markdown(get_position_overtake_css(), unsafe_allow_html=True)


st.markdown("""
# Position & Overtake Insights

Analyze overtaking patterns and race position dynamics 

## Visualizations

- **Overtakes vs Position Changes:** Scatter plot showing the relationship between number of overtakes and net positions gained during the race
- **Race Position Progression:** Line chart tracking lap-by-lap position changes for top-performing drivers throughout the race
""")

setup_fastf1_cache()

sidebar = st.sidebar
with sidebar:
    st.header("Race Selection")
    
    current_year = 2024
    year = st.selectbox(
        "Select Year",
        range(current_year, 2019, -1),
    )

    try:
        events = ff1.get_event_schedule(year)
        race_events = events[events["EventFormat"] != "testing"]
        event_names = race_events["EventName"].tolist()
        circuit = st.selectbox("Select Grand Prix", event_names)
        selected_event = race_events[race_events["EventName"] == circuit].iloc[0]
        round_number = selected_event["RoundNumber"]
    except Exception as e:
        st.error(f"Error loading events: {e}")
        st.stop()


@st.cache_data(show_spinner=False)
def process_speed_data(year, round_number):
    session = ff1.get_session(year, round_number, 'R')
    session.load()
    laps = session.laps
    
    speed_columns = ['SpeedI1', 'SpeedI2', 'SpeedFL', 'SpeedST']
    available_speed_cols = [col for col in speed_columns if col in laps.columns]
    
    driver_data = []
    
    for driver in laps['Driver'].unique():
        driver_laps = laps[laps['Driver'] == driver].copy()
        
        if driver_laps.empty:
            continue
            
        max_speeds = {}
        for col in available_speed_cols:
            speeds = driver_laps[col].dropna()
            if not speeds.empty:
                max_speeds[col] = speeds.max()
        
        if not max_speeds:
            continue
            
        overall_max = max(max_speeds.values()) if max_speeds else 0
        
        try:
            fastest_lap = driver_laps.pick_fastest()
            team = fastest_lap.get('Team', 'Unknown')
            compound = fastest_lap.get('Compound', 'Unknown')
        except:
            team = driver_laps.iloc[0].get('Team', 'Unknown')
            compound = 'Unknown'
        
        position_data = driver_laps[['LapNumber', 'Position']].dropna()
        overtakes = 0
        positions_gained = 0
        
        if len(position_data) > 1:
            start_pos = position_data.iloc[0]['Position']
            end_pos = position_data.iloc[-1]['Position']
            positions_gained = max(0, start_pos - end_pos)  
            
            for i in range(len(position_data) - 1):
                current_pos = position_data.iloc[i]['Position']
                next_pos = position_data.iloc[i+1]['Position']
                if current_pos > next_pos:  
                    overtakes += 1
        
        valid_laps = driver_laps['LapTime'].dropna()
        avg_lap_time = valid_laps.mean().total_seconds() if not valid_laps.empty else 0
        best_lap_time = valid_laps.min().total_seconds() if not valid_laps.empty else 0
        
        driver_data.append({
            'Driver': driver,
            'Team': team,
            'MaxSpeed': overall_max,
            'Overtakes': overtakes,
            'PositionsGained': positions_gained,
            'Compound': compound,
            'AvgLapTime': avg_lap_time,
            'BestLapTime': best_lap_time,
            'TotalLaps': len(driver_laps),
            **max_speeds  
        })
    
    return pd.DataFrame(driver_data), available_speed_cols

def create_overtakes_position_chart(df, circuit, year):
    
    if df.empty:
        return go.Figure().add_annotation(
            text="No data available for this race", 
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="white")
        )
    
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(
            x=df['Overtakes'],
            y=df['PositionsGained'],
            mode='markers+text',
            text=df['Driver'],
            textposition='middle right',
            marker=dict(
                size=15,
                color='#FF1E00',
                opacity=0.8,
                line=dict(width=2, color='white')
            ),
            name="Drivers",
            hovertemplate="<b>%{text}</b><br>Overtakes: %{x}<br>Positions Gained: %{y}<br>Team: " + 
                         df['Team'].astype(str) + "<extra></extra>"
        )
    )
    
    fig.update_layout(
        title={
            'text': f"Overtakes vs Position Changes - {circuit} {year}",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': 'white'}
        },
        xaxis_title="Number of Overtakes",
        yaxis_title="Positions Gained",
        height=500,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white")
    )
    
    fig.update_xaxes(
        gridcolor="rgba(255,255,255,0.1)", 
        tickfont=dict(color="white"),
        showgrid=True
    )
    fig.update_yaxes(
        gridcolor="rgba(255,255,255,0.1)", 
        tickfont=dict(color="white"),
        showgrid=True
    )
    
    return fig

@st.cache_data(show_spinner=False)
def create_race_progression_chart(year, round_number):
    session = ff1.get_session(year, round_number, 'R')
    session.load()
    laps = session.laps
    
    final_results = session.results.head(10)
    top_drivers = final_results['Abbreviation'].tolist()
    
    fig = go.Figure()
    
    for i, driver in enumerate(top_drivers):
        driver_data = laps[laps['Driver'] == driver][['LapNumber', 'Position']].dropna()
        
        if not driver_data.empty:
            color = team_colors.get(driver, px.colors.qualitative.Set3[i % len(px.colors.qualitative.Set3)])
            
            fig.add_trace(
                go.Scatter(
                    x=driver_data['LapNumber'],
                    y=driver_data['Position'],
                    mode='lines+markers',
                    name=driver,
                    line=dict(width=3, color=color),
                    marker=dict(size=5, color=color),
                    hovertemplate=f"<b>{driver}</b><br>Lap: %{{x}}<br>Position: %{{y}}<extra></extra>"
                )
            )
    
    fig.update_layout(
        title=f"Race Position Progression - {circuit} {year}",
        title_font=dict(size=18, color="white"),
        xaxis_title="Lap Number",
        yaxis_title="Position",
        yaxis=dict(autorange="reversed", dtick=1), 
        height=500,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        legend=dict(
            bgcolor="rgba(0,0,0,0.7)",
            bordercolor="rgba(255,255,255,0.2)",
            borderwidth=1
        )
    )
    
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.1)", showgrid=True)
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.1)", showgrid=True)
    
    return fig


with st.spinner("Processing speed data..."):
    df, speed_cols = process_speed_data(year, round_number)

if df.empty:
    st.warning("No speed data available for this race.")
    st.stop()

st.markdown('<div class="f1-section">', unsafe_allow_html=True)
st.subheader("Overtakes vs Position Changes Analysis")
fig_overtakes = create_overtakes_position_chart(df, circuit, year)
st.plotly_chart(fig_overtakes, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="f1-section">', unsafe_allow_html=True)
st.subheader("Race Position Progression")
fig_positions = create_race_progression_chart(year, round_number)
st.plotly_chart(fig_positions, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="f1-section">', unsafe_allow_html=True)
st.subheader("Race Statistics")

col1, col2, col3 = st.columns(3)

with col1:
    total_overtakes = df['Overtakes'].sum()
    avg_overtakes = df['Overtakes'].mean()
    description = f"avg {avg_overtakes:.1f} per driver"
    stat_card_html = create_f1_stat_card("Total Overtakes", str(total_overtakes), description)
    st.markdown(stat_card_html, unsafe_allow_html=True)

with col2:
    positions_gained_total = df['PositionsGained'].sum()
    max_positions_gained = df['PositionsGained'].max()
    best_climber = df.loc[df['PositionsGained'].idxmax(), 'Driver'] if max_positions_gained > 0 else "None"
    description = f"max {max_positions_gained} by {best_climber}"
    stat_card_html = create_f1_stat_card("Total Positions Gained", str(positions_gained_total), description)
    st.markdown(stat_card_html, unsafe_allow_html=True)

with col3:
    active_drivers = len(df)
    drivers_with_overtakes = (df['Overtakes'] > 0).sum()
    description = f"{drivers_with_overtakes} made overtakes"
    stat_card_html = create_f1_stat_card("Active Drivers", str(active_drivers), description)
    st.markdown(stat_card_html, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

