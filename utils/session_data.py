"""
F1 Analytics - Session Data Utilities

This module handles loading and managing F1 session data across the application.
"""

import logging
from typing import List, Optional, Tuple

import fastf1
import streamlit as st

logger = logging.getLogger(__name__)


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
def load_session(
    year: int,
    event: str = None,
    round_number: int = None,
    session_type: str = "R",
    _schedule=None,
) -> Optional[fastf1.core.Session]:
    """
    Load a FastF1 session by either event name or round number.

    Args:
        year (int): Selected year
        event (str, optional): Selected event name. Takes precedence over round_number if both provided.
        round_number (int, optional): F1 round number. Used if event name not provided.
        session_type (str, optional): Type of session ('R' for Race, 'Q' for Qualifying, etc.)
        schedule: F1 event schedule DataFrame (prefixed with _ to prevent hashing)

    Returns:
        Optional[fastf1.core.Session]: Loaded F1 session or None if error occurs
    """
    try:
        if event and _schedule is not None:
            event_row = _schedule[_schedule["EventName"] == event].iloc[0]
            gp_round = int(event_row["RoundNumber"])
        elif round_number is not None:
            gp_round = round_number
        else:
            raise ValueError(
                "Either event name with schedule or round number must be provided"
            )

        session = fastf1.get_session(year, gp_round, session_type)
        session.load()

        if session.laps.empty:
            logger.warning(
                f"No lap data available for {year} Round {gp_round} {session_type}"
            )
            return None

        return session
    except Exception as e:
        logger.error(f"Error loading session data: {e}")
        return None


def get_drivers_mapping(session: fastf1.core.Session) -> Tuple[list, list, dict, dict]:
    """
    Create driver name/abbreviation mapping data structures needed for UI filters.

    Args:
        session (fastf1.core.Session): Loaded F1 session

    Returns:
        Tuple containing:
            - list of driver abbreviations
            - list of driver full names
            - mapping from full name to abbreviation
            - mapping from abbreviation to full name
    """
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
    if driver_data:
        driver_full_names, driver_abbrs = zip(*driver_data)
        driver_full_names = list(driver_full_names)
        driver_abbrs = list(driver_abbrs)

    abbr_to_driver_name = {
        abbr: full_name for full_name, abbr in driver_name_to_abbr.items()
    }

    return driver_abbrs, driver_full_names, driver_name_to_abbr, abbr_to_driver_name
