import fastf1 as ff1
import fastf1.plotting
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.cache_utils import setup_fastf1_cache
from utils.session_data import get_available_years, load_session
from utils.styling import create_f1_stat_card, get_position_overtake_css

np.random.seed(42)

st.set_page_config(
    page_title="Position & Overtake Insights", page_icon="🏆", layout="wide"
)

st.markdown(get_position_overtake_css(), unsafe_allow_html=True)

st.title("🏆 Position & Overtake Insights")
st.markdown("""
Explore how drivers gained positions and made overtakes during the race. Use the filters to select a season and Grand Prix. The charts below visualize key race dynamics for top drivers.
""")

setup_fastf1_cache()

sidebar = st.sidebar
with sidebar:
    st.header("Race Selection")

    years = get_available_years()
    year = st.selectbox("Select Year", options=years, index=0)

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
    """Process speed trap and lap data efficiently - No heavy telemetry processing"""
    session = load_session(year=year, round_number=round_number, session_type="R")
    if session is None:
        return None
    laps = session.laps

    results = session.results
    abbr_to_full = dict(zip(results["Abbreviation"], results["FullName"]))

    speed_columns = ["SpeedI1", "SpeedI2", "SpeedFL", "SpeedST"]
    available_speed_cols = [col for col in speed_columns if col in laps.columns]

    driver_data = []

    for driver in laps["Driver"].unique():
        driver_laps = laps[laps["Driver"] == driver].copy()

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
            team = fastest_lap.get("Team", "Unknown")
            compound = fastest_lap.get("Compound", "Unknown")
        except Exception:
            team = driver_laps.iloc[0].get("Team", "Unknown")
            compound = driver_laps.iloc[0].get("Compound", "Unknown")

        position_data = driver_laps[["LapNumber", "Position"]].dropna()
        overtakes = 0
        positions_gained = 0

        if len(position_data) > 1:
            start_pos = position_data.iloc[0]["Position"]
            end_pos = position_data.iloc[-1]["Position"]
            positions_gained = max(0, start_pos - end_pos)

            for i in range(len(position_data) - 1):
                current_pos = position_data.iloc[i]["Position"]
                next_pos = position_data.iloc[i + 1]["Position"]
                if current_pos > next_pos:
                    overtakes += 1

        valid_laps = driver_laps["LapTime"].dropna()
        avg_lap_time = valid_laps.mean().total_seconds() if not valid_laps.empty else 0
        best_lap_time = valid_laps.min().total_seconds() if not valid_laps.empty else 0

        driver_data.append(
            {
                "Driver": driver,
                "Team": team,
                "MaxSpeed": overall_max,
                "Overtakes": overtakes,
                "PositionsGained": positions_gained,
                "Compound": compound,
                "AvgLapTime": avg_lap_time,
                "BestLapTime": best_lap_time,
                "TotalLaps": len(driver_laps),
                **max_speeds,
            }
        )

    df = pd.DataFrame(driver_data)

    df["DriverFullName"] = df["Driver"].map(abbr_to_full).fillna(df["Driver"])

    return df, available_speed_cols


def create_overtakes_position_chart(df, circuit, year, round_number):
    """Create focused overtakes vs position changes visualization with team colors and jittering for overlapping points"""

    if df.empty:
        return go.Figure().add_annotation(
            text="No data available for this race",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=20, color="white"),
        )

    plot_df = df.copy()

    plot_df["point_key"] = (
        plot_df["Overtakes"].astype(str) + "_" + plot_df["PositionsGained"].astype(str)
    )
    plot_df["point_count"] = plot_df.groupby("point_key")["Driver"].transform("count")

    mask = plot_df["point_count"] > 1
    if mask.any():
        for _, group in plot_df[mask].groupby("point_key"):
            n_points = len(group)

            angles = np.linspace(0, 2 * np.pi, n_points, endpoint=False)
            radius = 0.15

            for i, idx in enumerate(group.index):
                jitter_x = radius * np.cos(angles[i])
                jitter_y = radius * np.sin(angles[i])

                plot_df.loc[idx, "Overtakes_jit"] = (
                    plot_df.loc[idx, "Overtakes"] + jitter_x
                )
                plot_df.loc[idx, "PositionsGained_jit"] = (
                    plot_df.loc[idx, "PositionsGained"] + jitter_y
                )

    plot_df["Overtakes_jit"] = plot_df["Overtakes_jit"].fillna(plot_df["Overtakes"])
    plot_df["PositionsGained_jit"] = plot_df["PositionsGained_jit"].fillna(
        plot_df["PositionsGained"]
    )

    session = ff1.get_session(year, round_number, "R")
    session.load()

    team_colors = {}
    for team in df["Team"].unique():
        team_colors[team] = fastf1.plotting.get_team_color(team, session)

    colors = df["Team"].map(team_colors)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=plot_df["Overtakes_jit"],
            y=plot_df["PositionsGained_jit"],
            mode="markers+text",
            text=plot_df["Driver"],
            textposition="middle right",
            marker=dict(
                size=15, color=colors, opacity=0.8, line=dict(width=2, color="white")
            ),
            name="Drivers",
            hovertemplate="<b>%{text}</b><br>Overtakes: %{customdata[0]}<br>Positions Gained: %{customdata[1]}<br>Team: %{customdata[2]}<extra></extra>",
            customdata=plot_df[["Overtakes", "PositionsGained", "Team"]].values,
        )
    )

    max_x = max(plot_df["Overtakes"].max() + 1, 5)
    max_y = max(plot_df["PositionsGained"].max() + 1, 5)

    fig.update_layout(
        title={
            "text": f"Overtakes vs Position Changes - {circuit} {year}",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 20, "color": "white"},
        },
        xaxis_title="Number of Overtakes",
        yaxis_title="Positions Gained",
        height=500,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        annotations=[
            dict(
                text="Note: Points with identical values are slightly offset for visibility",
                xref="paper",
                yref="paper",
                x=0.98,
                y=0.02,
                showarrow=False,
                font=dict(size=10, color="rgba(255,255,255,0.5)"),
                align="right",
            )
        ],
    )

    fig.update_xaxes(
        gridcolor="rgba(255,255,255,0.1)",
        tickfont=dict(color="white"),
        showgrid=True,
        range=[-0.5, max_x],
        tickmode="linear",
        tick0=0,
        dtick=1,
    )
    fig.update_yaxes(
        gridcolor="rgba(255,255,255,0.1)",
        tickfont=dict(color="white"),
        showgrid=True,
        range=[-0.5, max_y],
        tickmode="linear",
        tick0=0,
        dtick=1,
    )

    return fig


@st.cache_data(show_spinner=False)
def create_race_progression_chart(year, round_number):
    """Create race progression visualization"""
    session = ff1.get_session(year, round_number, "R")
    session.load()
    laps = session.laps

    final_results = session.results.head(10)
    top_drivers = final_results["Abbreviation"].tolist()

    fig = go.Figure()

    session = ff1.get_session(year, round_number, "R")
    session.load()

    results = session.results
    driver_fullname = dict(zip(results["Abbreviation"], results["FullName"]))
    driver_teams = dict(zip(results["Abbreviation"], results["TeamName"]))

    for i, driver in enumerate(top_drivers):
        driver_data = laps[laps["Driver"] == driver][["LapNumber", "Position"]].dropna()

        driver_data = driver_data[driver_data["Position"] >= 1]

        if not driver_data.empty:
            team = driver_teams.get(driver, "")
            color = fastf1.plotting.get_team_color(team, session)

            fig.add_trace(
                go.Scatter(
                    x=driver_data["LapNumber"],
                    y=driver_data["Position"],
                    mode="lines+markers",
                    name=driver,
                    line=dict(width=3, color=color),
                    marker=dict(size=5, color=color),
                    hovertemplate=f"<b>{driver_fullname.get(driver, driver)}</b><br>Lap: %{{x}}<br>Position: %{{y}}<extra></extra>",
                )
            )

    all_positions = [
        pos
        for driver in top_drivers
        for pos in laps[laps["Driver"] == driver]["Position"].dropna().tolist()
    ]
    all_positions = [pos for pos in all_positions if pos >= 1]
    max_position = max(all_positions) if all_positions else 20

    fig.update_layout(
        title=f"Race Position Progression - Points Finishers - {circuit} {year}",
        title_font=dict(size=18, color="white"),
        xaxis_title="Lap Number",
        yaxis_title="Position",
        yaxis=dict(
            autorange=False,
            dtick=1,
            range=[max_position + 0.5, 0.5],
            tickmode="linear",
            tick0=1,
            tickvals=list(range(1, int(max_position) + 1)),
            ticktext=[str(i) for i in range(1, int(max_position) + 1)],
        ),
        height=500,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        legend=dict(
            bgcolor="rgba(0,0,0,0.7)",
            bordercolor="rgba(255,255,255,0.2)",
            borderwidth=1,
        ),
        hovermode="x unified",
        hoverlabel=dict(
            namelength=-1,
            bgcolor="rgba(255,255,255,0.9)",
            font_size=10,
        ),
    )

    for i, trace in enumerate(fig.data):
        if "name" in trace and not trace.name.startswith(f"{i + 1}. "):
            trace.name = f"{i + 1}. {trace.name}"

    fig.update_xaxes(gridcolor="rgba(255,255,255,0.1)", showgrid=True)
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.1)", showgrid=True)

    return fig


with st.spinner("Processing speed data..."):
    df, speed_cols = process_speed_data(year, round_number)

if df.empty:
    st.warning("No speed data available for this race.")
    st.stop()

with st.spinner("Creating visualizations..."):
    fig_overtakes = create_overtakes_position_chart(df, circuit, year, round_number)
    st.plotly_chart(fig_overtakes, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    fig_positions = create_race_progression_chart(year, round_number)
    st.plotly_chart(fig_positions, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.subheader("Race Statistics")

col1, col2, col3 = st.columns(3)

with col1:
    total_overtakes = df["Overtakes"].sum()
    avg_overtakes = df["Overtakes"].mean()
    description = f"~{avg_overtakes:.1f} per driver"
    stat_card_html = create_f1_stat_card(
        "Total Overtakes", str(total_overtakes), description
    )
    st.markdown(stat_card_html, unsafe_allow_html=True)

with col2:
    positions_gained_total = df["PositionsGained"].sum().astype(int)
    max_positions_gained = df["PositionsGained"].max().astype(int)
    best_climber = (
        df.loc[df["PositionsGained"].idxmax(), "DriverFullName"]
        if max_positions_gained > 0
        else "None"
    )
    description = f"{max_positions_gained} by {best_climber}"
    stat_card_html = create_f1_stat_card(
        "Total Positions Gained", str(positions_gained_total), description
    )
    st.markdown(stat_card_html, unsafe_allow_html=True)

with col3:
    active_drivers = len(df)
    drivers_with_overtakes = (df["Overtakes"] > 0).sum()
    description = f"{drivers_with_overtakes} made overtakes"
    stat_card_html = create_f1_stat_card(
        "Active Drivers", str(active_drivers), description
    )
    st.markdown(stat_card_html, unsafe_allow_html=True)
