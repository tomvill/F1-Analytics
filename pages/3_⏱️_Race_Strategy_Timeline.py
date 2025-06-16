import fastf1
import fastf1.plotting
import plotly.graph_objects as go
import streamlit as st
from collections import defaultdict
import datetime
from utils.cache_utils import setup_fastf1_cache
from utils.styling import apply_f1_styling, get_f1_plotly_layout

st.set_page_config(page_title="Race Strategy Timeline", layout="wide", page_icon="⏱️")
st.title("⏱️ Race Strategy Timeline")

# Apply F1 styling
apply_f1_styling()

setup_fastf1_cache()

@st.cache_data(ttl=86400)
def get_available_years() -> list[int]:
    """
    Get a list of available years for F1 data, from 2018 to current year.
    
    Returns:
        List[int]: List of years with available F1 data
    """
    current_year = datetime.datetime.now().year
    return list(range(2018, current_year + 1))


@st.cache_data(ttl=86400)
def get_race_events(year: int) -> tuple[list[str], fastf1.events.EventSchedule]:
    """
    Get the race events for a specific year, excluding pre-season testing.
    
    Args:
        year (int): The year to get events for
        
    Returns:
        Tuple[List[str], fastf1.events.EventSchedule]: A tuple containing list of event names 
                                                      and the full schedule DataFrame
    """
    schedule = fastf1.get_event_schedule(year)
    race_schedule = schedule[schedule['EventFormat'] != 'testing']
    event_names = race_schedule['EventName'].tolist()
    return event_names, race_schedule


@st.cache_data(ttl=86400, show_spinner=False)
def load_race_session(year: int, event: str, _schedule) -> fastf1.core.Session:
    """
    Load the FastF1 race session for the selected year and event.
    
    Args:
        year (int): Selected year
        event (str): Selected event name
        _schedule: F1 event schedule DataFrame (prefixed with _ to prevent hashing)
        
    Returns:
        fastf1.core.Session: Loaded F1 race session
    """
    event_row = _schedule[_schedule['EventName'] == event].iloc[0]
    gp_round = int(event_row['RoundNumber'])
    
    session = fastf1.get_session(year, gp_round, 'R')
    session.load()
    return session


def create_strategy_plot(session: fastf1.core.Session) -> tuple[go.Figure, list[str]]:
    """
    Create a Plotly figure showing the race strategy timeline for all drivers.
    
    Args:
        session (fastf1.core.Session): Loaded F1 session
        
    Returns:
        Tuple[go.Figure, List[str]]: Plotly figure with race strategy visualization
                                    and list of driver order
    """
    laps = session.laps
    
    drivers = session.drivers
    drivers = [session.get_driver(driver)["Abbreviation"] for driver in drivers]

    stints = laps[["Driver", "Stint", "Compound", "LapNumber"]]
    stints = stints.groupby(["Driver", "Stint", "Compound"], as_index=False).count()
    stints = stints.rename(columns={"LapNumber": "StintLength"})

    unique_compounds = stints["Compound"].unique()
    compound_colors = {}
    for compound in unique_compounds:
        compound_colors[compound] = fastf1.plotting.get_compound_color(compound, session)

    fig = go.Figure()

    compound_traces = defaultdict(list)

    for driver in drivers:
        fig.add_trace(go.Bar(
            y=[driver],
            x=[0.0001],
            orientation='h',
            marker=dict(
                color='rgba(0,0,0,0)',
                line=dict(width=0)
            ),
            showlegend=False,
            hoverinfo="none",
            base=0
        ))

    for driver in drivers:
        driver_stints = stints.loc[stints["Driver"] == driver]
        previous_stint_end = 0
        for _, row in driver_stints.iterrows():
            compound = row["Compound"]
            compound_color = compound_colors[compound]
            
            trace = go.Bar(
                y=[driver],
                x=[row["StintLength"]],
                base=previous_stint_end,
                orientation='h',
                marker=dict(
                    color=compound_color,
                    line=dict(color='black', width=1)
                ),
                name=compound,
                legendgroup=compound,
                showlegend=False,
                hoverinfo="text",
                hovertext=f"Driver: {driver}<br>Compound: {compound}<br>Laps: {previous_stint_end+1}-{previous_stint_end+row['StintLength']}"
            )
            
            fig.add_trace(trace)
            compound_traces[compound].append(len(fig.data) - 1)
            
            previous_stint_end += row["StintLength"]

    for compound in unique_compounds:
        fig.add_trace(go.Bar(
            y=[None],
            x=[0],
            name=compound,
            marker=dict(color=compound_colors[compound]),
            legendgroup=compound,
            showlegend=True,
        ))

    driver_totals = stints.groupby('Driver')['StintLength'].sum().sort_values(ascending=False)
    fixed_driver_order = driver_totals.index.tolist()

    max_race_length = driver_totals.max()

    event_name = session.event['EventName']
    race_year = session.event['EventDate'].year
    
    # Apply F1 layout styling
    layout = get_f1_plotly_layout(title=f"Driver Stint Analysis - {event_name} {race_year}", height=800)
    layout.update({
        'barmode': 'stack',
        'xaxis': dict(
            title=dict(
                text="Lap Number",
                font=dict(color="#ffffff", size=14)
            ),
            tickfont=dict(color="#ffffff", size=12),
            range=[0, max_race_length * 1.05],
            fixedrange=False,
            showgrid=True,
            gridcolor="rgba(255, 255, 255, 0.1)"
        ),
        'yaxis': dict(
            title=dict(
                text="Driver",
                font=dict(color="#ffffff", size=14)
            ),
            tickfont=dict(color="#ffffff", size=12),
            categoryarray=fixed_driver_order,
            categoryorder='array',
            fixedrange=False,
            showgrid=True,
            gridcolor="rgba(255, 255, 255, 0.1)"
        ),
        'showlegend': True,
        'hovermode': 'closest',
        'legend': dict(
            title="Tire Compounds",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color="#ffffff")
        )
    })
    
    fig.update_layout(layout)
    
    return fig, fixed_driver_order



years = get_available_years()
default_year_index = min(years.index(2024) if 2024 in years else len(years) - 1, len(years) - 1)

with st.sidebar:
    st.header("Filters")
    selected_year = st.selectbox('Select Year', years, index=default_year_index)
    
    try:
        event_names, schedule = get_race_events(selected_year)
        selected_event = st.selectbox('Select Grand Prix', event_names)
    except Exception as e:
        st.error(f"Error loading race events: {e}")
        st.stop()

st.write(f"**{selected_event} {selected_year} - Race Strategy**")
st.write("This visualization shows the tire stint strategies used by each driver throughout the race.")

try:
    with st.spinner('Loading race data...'):
        session = load_race_session(selected_year, selected_event, schedule)
    
    with st.spinner('Creating strategy plot...'):
        fig, driver_order = create_strategy_plot(session)
        
        config = {
            'displayModeBar': True,
            'scrollZoom': False,
            'doubleClick': False,
            'showAxisDragHandles': False,
            'displaylogo': False,
            'modeBarButtonsToRemove': [
                'zoom2d', 'pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d',
                'autoScale2d', 'resetScale2d', 'hoverClosestCartesian', 'hoverCompareCartesian',
                'toggleSpikelines', 'resetViewMapbox', 'sendDataToCloud', 'editInChartStudio',
                'zoom3d', 'pan3d', 'orbitRotation', 'tableRotation', 'resetCameraDefault3d',
                'resetCameraLastSave3d', 'hoverClosest3d', 'hoverClosestGl2d', 'hoverClosestPie',
                'toggleHover', 'resetViews', 'toggleDragMode', 'drawline', 'drawopenpath',
                'drawclosedpath', 'drawcircle', 'drawrect', 'eraseshape'
            ],
            'toImageButtonOptions': {
                'format': 'png',
                'filename': f'{selected_year}_{selected_event.replace(" ", "_")}_race_strategy',
            }
        }
        
        st.plotly_chart(fig, use_container_width=True, config=config)
        
        missing_drivers = []
        if missing_drivers:
            st.info(f"No strategy data available for: {', '.join(missing_drivers)}")
        
except Exception as e:
    st.warning(f"Could not load race data or create strategy plot: {e}")
    st.info(f"Try selecting a different Grand Prix for {selected_year}.")
    st.error(f"Error details: {e}")
