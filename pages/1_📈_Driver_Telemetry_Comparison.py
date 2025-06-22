import datetime
from typing import List, Tuple

import fastf1
import fastf1.plotting
import plotly.graph_objs as go
import streamlit as st

from utils.cache_utils import setup_fastf1_cache

fastf1.plotting.setup_mpl(
    mpl_timedelta_support=False, misc_mpl_mods=False, color_scheme="fastf1"
)

st.set_page_config(
    page_title="Driver Telemetry Comparison", layout="wide", page_icon="📈"
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


def plot_multi_driver_telemetry_comparison(
    session: fastf1.core.Session, drivers: List[str], metric: str, metric_label: str
) -> Tuple[go.Figure, List[str]]:
    """
    Plot the selected metric vs distance for multiple drivers, using their fastest laps.

    Args:
        session (fastf1.core.Session): Loaded F1 session
        drivers (List[str]): List of driver abbreviations
        metric (str): Selected telemetry metric to plot
        metric_label (str): Display label for the selected metric

    Returns:
        Tuple[go.Figure, List[str]]: Plotly figure with driver telemetry comparison and list of drivers with missing data
    """
    fig = go.Figure()
    missing_data_drivers = []

    team_drivers = {}

    for driver_abbr in drivers:
        try:
            driver_info = next(
                (
                    d
                    for d in session.drivers
                    if session.get_driver(d)["Abbreviation"] == driver_abbr
                ),
                None,
            )

            if driver_info is None:
                missing_data_drivers.append(driver_abbr)
                continue

            laps = session.laps.pick_drivers(driver_info)
            if laps.empty:
                missing_data_drivers.append(driver_abbr)
                continue

            team = session.get_driver(driver_info)["TeamName"]
            fastest_lap = laps.pick_fastest()
            telemetry = fastest_lap.get_telemetry()

            if metric not in telemetry.columns:
                missing_data_drivers.append(driver_abbr)
                continue

            color = fastf1.plotting.get_team_color(team, session=session)

            if team not in team_drivers:
                team_drivers[team] = 0

            line_style = "solid" if team_drivers[team] == 0 else "dash"
            team_drivers[team] += 1

            driver_full_name = session.get_driver(driver_info)["FullName"]

            fig.add_trace(
                go.Scatter(
                    x=telemetry["Distance"].round(),
                    y=telemetry[metric].round(),
                    mode="lines",
                    name=driver_abbr,
                    line=dict(color=color, dash=line_style),
                    hovertemplate=f"Distance: %{{x:.0f}} m<br>Driver: {driver_full_name}<br>{metric_label}: %{{y}}<extra></extra>",
                )
            )

        except Exception:
            missing_data_drivers.append(driver_abbr)
            continue

    fig.update_layout(
        xaxis_title="Distance (m)",
        yaxis_title=metric_label,
        legend_title="Drivers",
        template="plotly_white",
        height=600,
        hovermode="x unified",
    )

    return fig, missing_data_drivers


CAR_DATA_METRICS = {
    "Speed [km/h]": "Speed",
    "RPM": "RPM",
    "Gear Number": "nGear",
    "Throttle [%]": "Throttle",
    "Brake": "Brake",
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

        with st.spinner("Loading race session..."):
            session = load_race_session(selected_year, selected_event, schedule)

        driver_name_to_abbr = {}
        driver_abbrs = []
        driver_full_names = []

        for driver in session.drivers:
            try:
                driver_info = session.get_driver(driver)
                driver_abbr = driver_info["Abbreviation"]
                driver_full_name = driver_info["FullName"]

                driver_abbrs.append(driver_abbr)
                driver_full_names.append(driver_full_name)
                driver_name_to_abbr[driver_full_name] = driver_abbr
            except Exception:
                continue

        driver_data = sorted(zip(driver_full_names, driver_abbrs), key=lambda x: x[0])
        driver_full_names, driver_abbrs = zip(*driver_data) if driver_data else ([], [])
        driver_full_names = list(driver_full_names)
        driver_abbrs = list(driver_abbrs)

        abbr_to_driver_name = {
            abbr: full_name for full_name, abbr in driver_name_to_abbr.items()
        }

        default_drivers = driver_abbrs[: min(2, len(driver_abbrs))]

        selected_drivers = st.multiselect(
            "Select Drivers to Compare",
            options=driver_abbrs,
            default=default_drivers,
            format_func=lambda abbr: f"{abbr_to_driver_name[abbr]} ({abbr})",
            help="Select at least two drivers to compare their telemetry data",
        )

        if len(selected_drivers) < 2:
            st.warning("Please select at least two drivers for comparison")
            st.stop()

    except Exception as e:
        st.error(f"Error loading race events or drivers: {e}")
        st.stop()

st.subheader(f"**{selected_event} {selected_year} - Race**")
st.write(
    "This visualization compares telemetry data between drivers to analyze performance differences around the track."
)

try:
    all_missing_drivers = set()

    for metric_label, metric in CAR_DATA_METRICS.items():
        st.subheader(f"{metric_label} Comparison")

        with st.spinner(f"Creating {metric_label} plot..."):
            fig, missing_drivers = plot_multi_driver_telemetry_comparison(
                session, selected_drivers, metric, metric_label
            )
            st.plotly_chart(fig, use_container_width=True)
            all_missing_drivers.update(missing_drivers)

    if all_missing_drivers:
        st.warning(
            f"Some telemetry data is missing for: {', '.join(all_missing_drivers)}"
        )

except Exception as e:
    st.error(f"Could not plot telemetry comparison: {e}")
    st.info(
        f"Try selecting different drivers or a different Grand Prix for {selected_year}."
    )
