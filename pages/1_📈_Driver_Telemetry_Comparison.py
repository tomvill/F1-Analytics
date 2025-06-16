import datetime
from typing import Dict, List, Tuple

import fastf1
import fastf1.plotting
import plotly.graph_objs as go
import streamlit as st

from utils.cache_utils import setup_fastf1_cache

fastf1.plotting.setup_mpl(
    mpl_timedelta_support=False, misc_mpl_mods=False, color_scheme="fastf1"
)

st.set_page_config(
    page_title="Driver Telemetry Comparison", layout="centered", page_icon="📈"
)
st.title("📈 Driver Telemetry Comparison")

setup_fastf1_cache()


@st.cache_data(ttl=86400)
def get_available_years() -> List[int]:
    """
    Get a list of available years for F1 data, from 2018 to current year.

    Returns:
        List[int]: List of years with available F1 data
    """
    current_year = datetime.datetime.now().year
    return list(range(2018, current_year + 1))


@st.cache_data(ttl=86400)
def get_race_events(year: int) -> Tuple[List[str], fastf1.events.EventSchedule]:
    """
    Get the race events for a specific year, excluding pre-season testing.

    Args:
        year (int): The year to get events for

    Returns:
        Tuple[List[str], fastf1.events.EventSchedule]: A tuple containing list of event names
                                                      and the full schedule DataFrame
    """
    schedule = fastf1.get_event_schedule(year)
    race_schedule = schedule[schedule["EventFormat"] != "testing"]
    event_names = race_schedule["EventName"].tolist()
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
    event_row = _schedule[_schedule["EventName"] == event].iloc[0]
    gp_round = int(event_row["RoundNumber"])

    session = fastf1.get_session(year, gp_round, "R")
    session.load()
    return session


def plot_driver_telemetry(
    session: fastf1.core.Session, metric: str, metric_label: str
) -> go.Figure:
    """
    Plot the selected metric vs distance for all drivers, using their fastest lap.

    Args:
        session (fastf1.core.Session): Loaded F1 session
        metric (str): Selected telemetry metric to plot
        metric_label (str): Display label for the selected metric

    Returns:
        go.Figure: Plotly figure with driver telemetry
    """
    fig = go.Figure()
    team_styles: Dict[str, int] = {}
    missing_data_drivers = []

    for driver in session.drivers:
        laps = session.laps.pick_drivers(driver)
        if laps.empty:
            try:
                driver_abbr = session.get_driver(driver)["Abbreviation"]
                missing_data_drivers.append(driver_abbr)
            except Exception:
                missing_data_drivers.append(str(driver))
            continue

        try:
            driver_abbr = session.get_driver(driver)["Abbreviation"]
            team = session.get_driver(driver)["TeamName"]

            fastest_lap = laps.pick_fastest()
            telemetry = fastest_lap.get_telemetry()

            if metric not in telemetry.columns:
                missing_data_drivers.append(driver_abbr)
                continue

            color = fastf1.plotting.get_team_color(team, session=session)

            if team not in team_styles:
                team_styles[team] = 0

            line_dash = ["solid", "dash", "dot"][team_styles[team] % 3]

            fig.add_trace(
                go.Scatter(
                    x=telemetry["Distance"],
                    y=telemetry[metric],
                    mode="lines",
                    name=driver_abbr,
                    line=dict(color=color, dash=line_dash),
                )
            )
            team_styles[team] += 1

        except Exception:
            try:
                missing_data_drivers.append(driver_abbr)
            except Exception:
                missing_data_drivers.append(str(driver))
            continue

    fig.update_layout(
        title=f"Driver {metric_label} vs Distance",
        xaxis_title="Distance (m)",
        yaxis_title=metric_label,
        legend_title="Drivers",
        template="plotly_white",
        height=600,
        hovermode="x unified",
    )

    if missing_data_drivers:
        st.info(f"No data available for: {', '.join(missing_data_drivers)}")

    return fig


CAR_DATA_METRICS = {
    "Speed [km/h]": "Speed",
    "RPM": "RPM",
    "Gear Number": "nGear",
    "Throttle [%]": "Throttle",
    "Brake (On/Off)": "Brake",
}

years = get_available_years()
default_year_index = min(
    years.index(2024) if 2024 in years else len(years) - 1, len(years) - 1
)

with st.sidebar:
    st.header("Filters")
    selected_year = st.selectbox("Select Year", years, index=default_year_index)

    try:
        event_names, schedule = get_race_events(selected_year)
        selected_event = st.selectbox("Select Grand Prix", event_names)

        selected_metric_label = st.selectbox(
            "Select Car Data Metric", list(CAR_DATA_METRICS.keys()), index=0
        )
        selected_metric = CAR_DATA_METRICS[selected_metric_label]
    except Exception as e:
        st.error(f"Error loading race events: {e}")
        st.stop()

st.write(f"**{selected_event} {selected_year} - Race**")
st.write(
    "This visualization compares driver telemetry data to analyze performance differences around the track."
)

try:
    with st.spinner("Loading Race data..."):
        session = load_race_session(selected_year, selected_event, schedule)

    with st.spinner("Creating telemetry plot..."):
        fig = plot_driver_telemetry(session, selected_metric, selected_metric_label)
        st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.warning(f"Could not load race data or plot telemetry: {e}")
    st.info(f"Try selecting a different Grand Prix for {selected_year}.")
    st.error(f"Error details: {e}")
