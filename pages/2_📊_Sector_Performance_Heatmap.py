from datetime import timedelta

import fastf1 as ff1
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from utils.styling import (
    apply_f1_styling,
    get_f1_plotly_layout,
    get_f1_heatmap_colorscale,
    create_f1_metric_card,
)
from utils.driver_data import get_driver_full_name

st.set_page_config(
    page_title="F1 Analytics - Sector Performance Heatmap",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Sector Performance Heatmap")
st.markdown("""
Analyze sector times lap-by-lap. Each cell shows how much slower a sector was compared to the driver’s personal best. Use the heatmap and stats below to spot consistency and performance trends.
""")

apply_f1_styling()

ff1.Cache.enable_cache(".fast-f1-cache")

with st.sidebar:
    current_year = 2024
    year = st.selectbox(
        "Select Year",
        range(current_year, 2017, -1),
    )

    try:
        events = ff1.get_event_schedule(year)

        race_events = events[events["EventFormat"] != "testing"]

        if race_events.empty:
            st.error(
                f"No race events found for {year}. Please select a different year."
            )
            st.stop()

        event_names = race_events["EventName"].tolist()
        circuit = st.selectbox("Select Grand Prix", event_names)

        selected_event = race_events[race_events["EventName"] == circuit].iloc[0]
        round_number = selected_event["RoundNumber"]

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
            st.warning(
                "No lap data available for this race session. The data might not be available."
            )
            return None

        return session
    except Exception as e:
        st.error(f"Error loading session data: {e}")
        return None


with st.spinner("Loading race session data... This may take a moment."):
    session = load_session_data(year, round_number, session_key)

if session is None:
    st.warning(
        "No data available for the selected session. Please try a different circuit or year."
    )
    st.stop()

laps_data = session.laps


drivers = laps_data["Driver"].unique().tolist()

with st.sidebar:
    selected_driver = st.selectbox(
        "Select Driver",
        drivers,
    )

    laps_data = laps_data.pick_drivers(selected_driver)


def timedelta_to_seconds(td):
    if pd.isna(td):
        return None
    if isinstance(td, timedelta):
        return td.total_seconds()
    try:
        return float(td)
    except ValueError:
        st.error(f"Invalid time format: {td}. Expected timedelta or float.")
        return None


def prepare_heatmap_data(laps_data, driver=None):
    if driver:
        driver_laps = laps_data.pick_drivers(driver)
    else:
        driver_laps = laps_data

    valid_laps = driver_laps.dropna(
        subset=["Sector1Time", "Sector2Time", "Sector3Time"]
    ).copy()

    if valid_laps.empty:
        return None, None

    s1_seconds = valid_laps["Sector1Time"].apply(timedelta_to_seconds)
    s2_seconds = valid_laps["Sector2Time"].apply(timedelta_to_seconds)
    s3_seconds = valid_laps["Sector3Time"].apply(timedelta_to_seconds)

    valid_laps = valid_laps.assign(
        S1_seconds=s1_seconds, S2_seconds=s2_seconds, S3_seconds=s3_seconds
    )

    valid_laps = valid_laps.dropna(subset=["S1_seconds", "S2_seconds", "S3_seconds"])

    if valid_laps.empty:
        return None, None

    s1_benchmark = valid_laps["S1_seconds"].min()
    s2_benchmark = valid_laps["S2_seconds"].min()
    s3_benchmark = valid_laps["S3_seconds"].min()

    valid_laps = valid_laps.assign(
        S1_delta=valid_laps["S1_seconds"] - s1_benchmark,
        S2_delta=valid_laps["S2_seconds"] - s2_benchmark,
        S3_delta=valid_laps["S3_seconds"] - s3_benchmark,
    )

    heatmap_data = valid_laps[["LapNumber", "S1_delta", "S2_delta", "S3_delta"]].copy()

    heatmap_data = heatmap_data.set_index("LapNumber")

    heatmap_data.columns = ["Sector 1", "Sector 2", "Sector 3"]

    return heatmap_data, valid_laps


def create_sector_heatmap(heatmap_data, driver_name, circuit, year):
    z_data = heatmap_data.values

    sectors = ["Sector 1", "Sector 2", "Sector 3"]

    lap_numbers = heatmap_data.index.tolist()

    all_deltas = heatmap_data.values.flatten()
    all_deltas = all_deltas[~np.isnan(all_deltas)]

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

    z_data_log = np.copy(z_data)
    z_data_original = np.copy(z_data)

    mask = ~np.isnan(z_data_log)
    epsilon = 0.001
    z_data_log[mask] = np.log10(z_data_log[mask] + epsilon)

    if effective_max > 0:
        log_min = np.log10(epsilon)
        log_p25 = np.log10(p25 + epsilon) if p25 > 0 else log_min
        log_p50 = np.log10(p50 + epsilon) if p50 > 0 else log_min
        log_p75 = np.log10(p75 + epsilon) if p75 > 0 else log_min
        log_max = np.log10(effective_max + epsilon)
    else:
        log_min = 0
        log_p25 = 0.25
        log_p50 = 0.5
        log_p75 = 0.75
        log_max = 1

    colorscale = get_f1_heatmap_colorscale()

    fig = go.Figure(
        data=go.Heatmap(
            z=z_data_log,
            x=sectors,
            y=lap_numbers,
            colorscale=colorscale,
            zmin=log_min,
            zmax=log_max,
            text=[[f"{val:.3f}s" for val in row] for row in z_data_original],
            hovertemplate="Lap: %{y}<br>%{x}: %{text}<br><extra></extra>",
            colorbar=dict(
                title=dict(
                    text="Delta to Best Sector", font=dict(color="#ffffff", size=14)
                ),
                tickvals=[log_min, log_p25, log_p50, log_p75, log_max],
                ticktext=[
                    "Best Sector",
                    f"+{p25:.3f}s",
                    f"+{p50:.3f}s",
                    f"+{p75:.3f}s",
                    f"+{effective_max:.3f}s",
                ],
                tickfont=dict(color="#ffffff", size=12),
                len=0.5,
                y=0.5,
            ),
        )
    )

    driver_full_name = get_driver_full_name(session.results, driver_name) or driver_name

    title_text = f"{driver_full_name} - {circuit} {year} - Sector Performance"

    layout = get_f1_plotly_layout(title=title_text, height=800)
    layout.update(
        {
            "xaxis": dict(
                title=dict(text="Track Sector", font=dict(color="#ffffff", size=14)),
                tickfont=dict(color="#ffffff", size=12),
                showgrid=True,
                gridcolor="rgba(255, 255, 255, 0.1)",
            ),
            "yaxis": dict(
                title=dict(text="Lap Number", font=dict(color="#ffffff", size=14)),
                tickfont=dict(color="#ffffff", size=12),
                autorange="reversed",
                showgrid=True,
                gridcolor="rgba(255, 255, 255, 0.1)",
            ),
            "width": 1000,
            "margin": dict(l=80, r=80, t=100, b=80),
        }
    )

    fig.update_layout(layout)

    return fig


heatmap_data, valid_laps = prepare_heatmap_data(laps_data, selected_driver)

if heatmap_data is None:
    st.warning(f"No sector data available for {selected_driver} in this session.")
else:
    with st.expander("Sector Statistics", expanded=False):

        def get_top_n_sectors(data, sector_col, n=3):
            top_sectors = data.sort_values(by=sector_col).head(n).copy()
            top_sectors["formatted_time"] = top_sectors[sector_col].apply(
                lambda x: str(timedelta(seconds=x)).split(".")[0]
                + "."
                + str(timedelta(seconds=x)).split(".")[1][:3]
            )
            top_sectors["formatted_time"] = top_sectors["formatted_time"].apply(
                lambda x: x[2:] if x.startswith("0:") else x
            )
            return top_sectors

        top_s1 = get_top_n_sectors(valid_laps, "S1_seconds")
        top_s2 = get_top_n_sectors(valid_laps, "S2_seconds")
        top_s3 = get_top_n_sectors(valid_laps, "S3_seconds")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(
                '<div class="f1-stats-header">Sector 1</div>', unsafe_allow_html=True
            )
            for i, (_, row) in enumerate(top_s1.iterrows(), 1):
                st.markdown(
                    f'<div class="f1-stat-item">#{i}: {row["formatted_time"]} (Lap {int(row["LapNumber"])})</div>',
                    unsafe_allow_html=True,
                )

        with col2:
            st.markdown(
                '<div class="f1-stats-header">Sector 2</div>', unsafe_allow_html=True
            )
            for i, (_, row) in enumerate(top_s2.iterrows(), 1):
                st.markdown(
                    f'<div class="f1-stat-item">#{i}: {row["formatted_time"]} (Lap {int(row["LapNumber"])})</div>',
                    unsafe_allow_html=True,
                )

        with col3:
            st.markdown(
                '<div class="f1-stats-header">Sector 3</div>', unsafe_allow_html=True
            )
            for i, (_, row) in enumerate(top_s3.iterrows(), 1):
                st.markdown(
                    f'<div class="f1-stat-item">#{i}: {row["formatted_time"]} (Lap {int(row["LapNumber"])})</div>',
                    unsafe_allow_html=True,
                )

        theoretical_best = (
            valid_laps["S1_seconds"].min()
            + valid_laps["S2_seconds"].min()
            + valid_laps["S3_seconds"].min()
        )
        theoretical_best_time = timedelta(seconds=theoretical_best)
        theoretical_best_str = f"{theoretical_best_time.seconds // 60}:{theoretical_best_time.seconds % 60:02d}.{theoretical_best_time.microseconds // 1000:03d}"

        try:
            best_lap = valid_laps.loc[
                valid_laps["LapTime"].dropna().apply(timedelta_to_seconds).idxmin()
            ]
            best_lap_time = timedelta_to_seconds(best_lap["LapTime"])
            best_lap_time_delta = timedelta(seconds=best_lap_time - theoretical_best)
            best_lap_time_delta_str = f"+{best_lap_time_delta.seconds}.{best_lap_time_delta.microseconds // 1000:03d}"

            best_lap_time = timedelta(seconds=best_lap_time)
            best_lap_time_str = f"{best_lap_time.seconds // 60}:{best_lap_time.seconds % 60:02d}.{best_lap_time.microseconds // 1000:03d}"

            st.markdown("""
            ### 🏁 Lap Analysis
            
            This analysis compares the driver's actual best lap with a theoretical best lap time.
            The theoretical best combines the fastest sectors from any lap, showing the potential if the driver could perform perfectly across all sectors in a single lap.
            The difference indicates how much improvement might be possible under ideal conditions.
            """)
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(
                    create_f1_metric_card(
                        "Theoretical Best Lap", theoretical_best_str, "Perfect sectors"
                    ),
                    unsafe_allow_html=True,
                )

            with col2:
                st.markdown(
                    create_f1_metric_card(
                        "Actual Best Lap",
                        best_lap_time_str,
                        f"{best_lap_time_delta_str} vs theoretical",
                    ),
                    unsafe_allow_html=True,
                )
        except Exception as e:
            st.error(f"Error calculating best lap time: {e}")
            st.markdown(
                create_f1_metric_card(
                    "Theoretical Best Lap", theoretical_best_str, "Perfect sectors"
                ),
                unsafe_allow_html=True,
            )
            st.warning("Could not calculate actual best lap time")

    fig = create_sector_heatmap(heatmap_data, selected_driver, circuit, year)
    st.plotly_chart(fig, use_container_width=True)
