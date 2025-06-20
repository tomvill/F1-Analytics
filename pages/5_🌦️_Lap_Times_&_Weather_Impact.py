from typing import Dict, List, Tuple

import fastf1
import fastf1.plotting
import pandas as pd
import plotly.graph_objs as go
import streamlit as st

from utils.cache_utils import setup_fastf1_cache

fastf1.plotting.setup_mpl(
    mpl_timedelta_support=True, misc_mpl_mods=False, color_scheme="fastf1"
)


st.set_page_config(
    page_title="Lap Times & Weather Impact", layout="wide", page_icon="🌦️"
)
st.title("🌦️ Lap Times & Weather Impact")
st.markdown("""
Analyze how weather conditions affect driver performance during races.
This visualization shows lap time evolution and weather parameters side-by-side to help identify correlations.
""")

setup_fastf1_cache()


@st.cache_data(ttl=86400)
def get_available_years() -> List[int]:
    """
    Get a list of available years for F1 data, from 2018 to current year.

    Returns:
        List[int]: List of years with available F1 data
    """
    return list(range(2024, 2017, -1))


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


def plot_lap_times(
    session: fastf1.core.Session,
    selected_drivers: List[str],
    weather_data: Dict[str, object] = None,
) -> go.Figure:
    """
    Plot lap times vs lap number for selected drivers in the race.

    Args:
        session (fastf1.core.Session): Loaded F1 race session
        selected_drivers (List[str]): List of selected driver abbreviations
        weather_data (Dict[str, object], optional): Weather data dictionary

    Returns:
        go.Figure: Plotly figure with lap times
    """
    fig = go.Figure()
    team_styles: Dict[str, int] = {}
    missing_data_drivers = []
    drivers_with_data = 0

    if not selected_drivers:
        fig.update_layout(
            title="No Drivers Selected",
            annotations=[
                dict(
                    text="Please select at least one driver to display lap times",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    font=dict(size=16),
                )
            ],
        )
        return fig

    laps_data = session.laps
    laps_data = laps_data.drop(laps_data[laps_data["PitOutTime"].notna()].index)
    laps_data = laps_data.drop(laps_data[laps_data["PitInTime"].notna()].index)

    for driver in selected_drivers:
        try:
            driver_info = session.get_driver(driver)
            driver_abbr = driver_info["Abbreviation"]
            team = driver_info["TeamName"]

            driver_laps = laps_data.pick_drivers(driver_abbr)

            if driver_laps.empty:
                missing_data_drivers.append(driver_abbr)
                continue

            lap_times = []
            for _, lap in driver_laps.iterrows():
                if pd.notna(lap["LapTime"]):
                    lap_time_seconds = lap["LapTime"].total_seconds()

                    if lap_time_seconds < 300:
                        lap_times.append(lap_time_seconds)

            if not lap_times:
                missing_data_drivers.append(driver_abbr)
                continue

            lap_numbers = list(range(1, len(lap_times) + 1))

            drivers_with_data += 1

            color = fastf1.plotting.get_team_color(team, session)

            if team not in team_styles:
                team_styles[team] = 0

            if team_styles[team] == 0:
                line_dash = "solid"
            elif team_styles[team] == 1:
                line_dash = "dash"
            else:
                line_dash = "dot"

            team_styles[team] += 1

            fig.add_trace(
                go.Scatter(
                    x=lap_numbers,
                    y=lap_times,
                    mode="lines",
                    name=driver_abbr,
                    line=dict(color=color, dash=line_dash),
                    hovertemplate=f"Lap %{{x}}<br>Time: %{{y:.3f}}s<br>Team: {team}<extra>{driver_abbr}</extra>",
                )
            )

        except Exception:
            try:
                missing_data_drivers.append(driver_abbr)
            except Exception:
                missing_data_drivers.append(str(driver))
            continue

    if (
        weather_data
        and weather_data.get("available")
        and weather_data.get("time_series")
    ):
        try:
            weather_ts = weather_data["time_series"]
            if len(weather_ts.get("rainfall", [])) > 0:
                max_laps = (
                    session.laps["LapNumber"].max() if not session.laps.empty else 0
                )
                rainfall_data = weather_ts["rainfall"]

                if max(rainfall_data) > 0:
                    num_laps = int(max_laps)
                    rain_periods = []

                    segments = len(rainfall_data)
                    rain_start = None

                    for i, rain_value in enumerate(rainfall_data):
                        lap_position = (
                            1 + (i / segments) * num_laps if segments > 0 else 1
                        )

                        if rain_value > 0 and rain_start is None:
                            rain_start = lap_position
                        elif rain_value == 0 and rain_start is not None:
                            rain_periods.append((rain_start, lap_position))
                            rain_start = None

                    if rain_start is not None:
                        rain_periods.append((rain_start, num_laps))

                    for i, (start_lap, end_lap) in enumerate(rain_periods):
                        fig.add_vrect(
                            x0=start_lap,
                            x1=end_lap,
                            fillcolor="rgba(0, 130, 255, 0.15)",
                            layer="below",
                            line_width=0,
                            opacity=0.5,
                        )

                    fig.add_trace(
                        go.Scatter(
                            x=[None],
                            y=[None],
                            mode="lines",
                            line=dict(color="rgba(0, 130, 255, 0.15)", width=10),
                            name="Rainfall Periods",
                            showlegend=True,
                        )
                    )
        except Exception as e:
            st.warning(f"Could not overlay rainfall data: {str(e)}")

    fig.update_layout(
        title="Lap Times Throughout Race",
        xaxis_title="Lap Number",
        yaxis_title="Lap Time (seconds)",
        legend_title="Drivers",
        template="plotly_white",
        height=600,
        hovermode="x unified",
        showlegend=True,
    )

    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="rgba(211, 211, 211, 0.3)")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(211, 211, 211, 0.3)")

    if drivers_with_data == 0 and selected_drivers:
        fig.update_layout(
            title="No Lap Time Data Available",
            annotations=[
                dict(
                    text="No lap time data available for selected drivers",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    font=dict(size=16),
                )
            ],
        )

    if missing_data_drivers:
        st.info(f"No lap time data available for: {', '.join(missing_data_drivers)}")

    return fig


def get_driver_info(session: fastf1.core.Session) -> Dict[str, Dict]:
    """
    Get a dictionary of driver information including abbreviation and team.

    Args:
        session (fastf1.core.Session): Loaded F1 session

    Returns:
        Dict[str, Dict]: Dictionary with driver information
    """
    driver_info = {}
    for driver in session.drivers:
        try:
            info = session.get_driver(driver)
            driver_info[info["Abbreviation"]] = {
                "FullName": f"{info['FirstName']} {info['LastName']}",
                "TeamName": info["TeamName"],
            }
        except Exception:
            continue
    return driver_info


def get_team_drivers(driver_info: Dict[str, Dict]) -> Dict[str, List[str]]:
    """
    Group drivers by teams.

    Args:
        driver_info (Dict[str, Dict]): Dictionary with driver information

    Returns:
        Dict[str, List[str]]: Dictionary with teams as keys and lists of driver abbreviations as values
    """
    teams = {}
    for abbr, info in driver_info.items():
        team = info["TeamName"]
        if team not in teams:
            teams[team] = []
        teams[team].append(abbr)
    return teams


def get_weather_data(session: fastf1.core.Session) -> Dict[str, object]:
    """
    Extract relevant weather data from the session.

    Args:
        session (fastf1.core.Session): Loaded F1 race session

    Returns:
        Dict[str, object]: Dictionary with processed weather data
    """
    try:
        weather_data = session.weather_data

        if weather_data.empty:
            return {
                "available": False,
                "message": "No weather data available for this session",
            }

        stats = {
            "available": True,
            "air_temp": {
                "mean": round(weather_data["AirTemp"].mean(), 1),
                "min": round(weather_data["AirTemp"].min(), 1),
                "max": round(weather_data["AirTemp"].max(), 1),
            },
            "track_temp": {
                "mean": round(weather_data["TrackTemp"].mean(), 1),
                "min": round(weather_data["TrackTemp"].min(), 1),
                "max": round(weather_data["TrackTemp"].max(), 1),
            },
            "humidity": {
                "mean": round(weather_data["Humidity"].mean(), 1),
                "min": round(weather_data["Humidity"].min(), 1),
                "max": round(weather_data["Humidity"].max(), 1),
            },
            "wind": {
                "speed_mean": round(weather_data["WindSpeed"].mean(), 1),
                "speed_max": round(weather_data["WindSpeed"].max(), 1),
                "direction_mean": round(weather_data["WindDirection"].mean(), 1),
            },
            "rain": any(weather_data["Rainfall"] > 0),
        }

        stats["time_series"] = {
            "time": weather_data.index,
            "air_temp": weather_data["AirTemp"],
            "track_temp": weather_data["TrackTemp"],
            "humidity": weather_data["Humidity"],
            "rainfall": weather_data["Rainfall"],
        }

        return stats
    except Exception as e:
        return {
            "available": False,
            "message": f"Error processing weather data: {str(e)}",
        }


def display_weather_panel(weather_data: Dict[str, object]) -> None:
    """
    Display weather information in a panel.

    Args:
        weather_data (Dict[str, object]): Dictionary with processed weather data
    """
    st.subheader("Weather Conditions")

    if not weather_data["available"]:
        st.info(weather_data["message"])
        return

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Air Temperature",
            f"{weather_data['air_temp']['mean']}°C",
            f"{weather_data['air_temp']['max'] - weather_data['air_temp']['min']:.1f}°C variation",
        )

        st.metric(
            "Humidity",
            f"{weather_data['humidity']['mean']}%",
            f"{weather_data['humidity']['max'] - weather_data['humidity']['min']:.1f}% variation",
        )

    with col2:
        st.metric(
            "Track Temperature",
            f"{weather_data['track_temp']['mean']}°C",
            f"{weather_data['track_temp']['max'] - weather_data['track_temp']['min']:.1f}°C variation",
        )

        st.metric(
            "Wind Speed",
            f"{weather_data['wind']['speed_mean']} km/h",
            f"Max: {weather_data['wind']['speed_max']} km/h",
        )

    # Display rain status with icon
    if weather_data["rain"]:
        st.warning("⛈️ Rain detected during this session", icon="⚠️")
    else:
        st.success("☀️ No rainfall during this session", icon="✅")

    # Display temperature range
    st.subheader("Temperature Details")
    st.markdown(f"""
    | Metric | Min | Mean | Max | Variation |
    |--------|-----|------|-----|-----------|
    | **Air Temp** | {weather_data["air_temp"]["min"]}°C | {weather_data["air_temp"]["mean"]}°C | {weather_data["air_temp"]["max"]}°C | {weather_data["air_temp"]["max"] - weather_data["air_temp"]["min"]:.1f}°C |
    | **Track Temp** | {weather_data["track_temp"]["min"]}°C | {weather_data["track_temp"]["mean"]}°C | {weather_data["track_temp"]["max"]}°C | {weather_data["track_temp"]["max"] - weather_data["track_temp"]["min"]:.1f}°C |
    | **Humidity** | {weather_data["humidity"]["min"]}% | {weather_data["humidity"]["mean"]}% | {weather_data["humidity"]["max"]}% | {weather_data["humidity"]["max"] - weather_data["humidity"]["min"]:.1f}% |
    """)

    # Add wind direction info
    direction = weather_data["wind"]["direction_mean"]
    cardinal_direction = "N/A"

    # Convert degrees to cardinal directions
    if 337.5 <= direction <= 360 or 0 <= direction < 22.5:
        cardinal_direction = "North"
    elif 22.5 <= direction < 67.5:
        cardinal_direction = "Northeast"
    elif 67.5 <= direction < 112.5:
        cardinal_direction = "East"
    elif 112.5 <= direction < 157.5:
        cardinal_direction = "Southeast"
    elif 157.5 <= direction < 202.5:
        cardinal_direction = "South"
    elif 202.5 <= direction < 247.5:
        cardinal_direction = "Southwest"
    elif 247.5 <= direction < 292.5:
        cardinal_direction = "West"
    elif 292.5 <= direction < 337.5:
        cardinal_direction = "Northwest"

    st.caption(f"**Wind Direction**: {cardinal_direction} ({direction:.1f}°)")


st.sidebar.header("Race Selection")

selected_year = st.sidebar.selectbox(
    "Select Year", options=get_available_years(), index=0
)

events, schedule = get_race_events(selected_year)

selected_event = st.sidebar.selectbox("Select Grand Prix", options=events)

with st.spinner("Loading race data..."):
    try:
        session = load_race_session(selected_year, selected_event, schedule)

        st.sidebar.header("Driver Selection")
        driver_info = get_driver_info(session)
        team_drivers = get_team_drivers(driver_info)

        selection_method = st.sidebar.radio(
            "Select drivers by:",
            options=["Team", "Individual Drivers", "Top Performing"],
            index=0,
        )

        if selection_method == "Team":
            selected_teams = st.sidebar.multiselect(
                "Select Teams",
                options=["All Teams"] + list(team_drivers.keys()),
                default=["All Teams"],
            )

            if not selected_teams:
                st.sidebar.warning("Please select at least one team")
                selected_drivers = []

            elif "All Teams" in selected_teams:
                selected_drivers = list(driver_info.keys())
                if len(selected_teams) > 1:
                    st.sidebar.info("'All Teams' option selected, showing all drivers")
            else:
                selected_drivers = []
                for team in selected_teams:
                    selected_drivers.extend(team_drivers[team])

        elif selection_method == "Individual Drivers":
            selected_drivers = st.sidebar.multiselect(
                "Select Drivers",
                options=sorted(list(driver_info.keys())),
                default=sorted(list(driver_info.keys())[:5]),
            )
            if not selected_drivers:
                st.sidebar.warning("Please select at least one driver")
                selected_drivers = []

        elif selection_method == "Top Performing":
            try:
                num_drivers = st.sidebar.slider(
                    "Number of drivers", 1, len(driver_info), 5
                )
                results_df = session.results
                top_drivers = (
                    results_df.sort_values("Position")["Abbreviation"]
                    .head(num_drivers)
                    .tolist()
                )
                selected_drivers = [d for d in top_drivers if d in driver_info]

                if not selected_drivers:
                    st.sidebar.warning("No drivers found with this filter")
                    selected_drivers = []
                else:
                    st.sidebar.info(f"Showing top {len(selected_drivers)} finishers")
            except Exception:
                st.sidebar.warning("Couldn't determine positions.")
                selected_drivers = []

        st.subheader(f"Lap Times - {selected_year} {selected_event}")

        # Get weather data for the panel
        weather_data = get_weather_data(session)

        # Create a two-column layout
        lap_times_col, weather_col = st.columns([0.65, 0.35])

        with lap_times_col:
            fig = plot_lap_times(session, selected_drivers, weather_data)
            st.plotly_chart(fig, use_container_width=True)

        with weather_col:
            # Weather data display
            display_weather_panel(weather_data)

    except Exception as e:
        st.error(f"Error loading session data: {str(e)}")
        st.info("Try selecting a different race or year.")
