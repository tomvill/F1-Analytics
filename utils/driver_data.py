"""
F1 Analytics - Driver Data Utilities

This module handles fetching driver information using FastF1's built-in SessionResults
and DriverResult functionality.
"""

from typing import Dict, Optional

import fastf1 as ff1
import pandas as pd
import streamlit as st


@st.cache_data(ttl=3600, show_spinner=False)
def get_session_results(year: int, round_number: int, session_type: str = "R"):
    """
    Get session results which contain driver information.

    Args:
        year (int): F1 season year
        round_number (int): Round number of the Grand Prix
        session_type (str): Session type ('R' for Race, 'Q' for Qualifying, etc.)

    Returns:
        SessionResults: FastF1 SessionResults object containing driver data
    """
    try:
        session = ff1.get_session(year, round_number, session_type)
        session.load()
        return session.results
    except Exception as e:
        print(f"Error loading session results for {year} Round {round_number}: {e}")
        return None


def get_driver_info(session_results, driver_identifier: str) -> Optional[Dict]:
    """
    Get driver information from session results using the driver identifier.

    Args:
        session_results: FastF1 SessionResults object (DataFrame)
        driver_identifier (str): Driver's three letter identifier (e.g., 'VER') or driver number as string

    Returns:
        Optional[Dict]: Driver information as dictionary or None if not found
    """
    try:
        if session_results is None or session_results.empty:
            return None

        if "Abbreviation" in session_results.columns:
            driver_rows = session_results[
                session_results["Abbreviation"] == driver_identifier.upper()
            ]
            if not driver_rows.empty:
                driver_dict = driver_rows.iloc[0].to_dict()
                driver_dict["driver_identifier"] = driver_identifier
                return driver_dict

        try:
            driver_num = str(driver_identifier)
            if driver_num in session_results.index:
                driver_dict = session_results.loc[driver_num].to_dict()
                driver_dict["driver_identifier"] = driver_identifier
                return driver_dict
        except (ValueError, KeyError):
            pass

        try:
            driver_num = int(driver_identifier)
            driver_num_str = str(driver_num)
            if driver_num_str in session_results.index:
                driver_dict = session_results.loc[driver_num_str].to_dict()
                driver_dict["driver_identifier"] = driver_identifier
                return driver_dict
        except (ValueError, KeyError):
            pass

        return None

    except Exception as e:
        print(f"Error getting driver info for {driver_identifier}: {e}")
        return None


def get_driver_full_name(session_results, driver_identifier: str) -> Optional[str]:
    """
    Get driver's full name from session results.

    Args:
        session_results: FastF1 SessionResults object
        driver_identifier (str): Driver's three letter identifier (e.g., 'VER') or driver number

    Returns:
        Optional[str]: Driver's full name or None if not found
    """
    driver_info = get_driver_info(session_results, driver_identifier)
    if driver_info:
        if "full_name" in driver_info and driver_info["full_name"].strip():
            return driver_info["full_name"]
        elif "FullName" in driver_info:
            return driver_info["FullName"]
        elif "FirstName" in driver_info and "LastName" in driver_info:
            return f"{driver_info['FirstName']} {driver_info['LastName']}".strip()
        elif "Abbreviation" in driver_info:
            return driver_info["Abbreviation"]
    return None


def get_driver_team_name(session_results, driver_identifier: str) -> Optional[str]:
    """
    Get driver's team name from session results.

    Args:
        session_results: FastF1 SessionResults object
        driver_identifier (str): Driver's three letter identifier (e.g., 'VER') or driver number

    Returns:
        Optional[str]: Team name or None if not found
    """
    driver_info = get_driver_info(session_results, driver_identifier)
    if driver_info:
        return driver_info.get("TeamName") or driver_info.get("Team")
    return None


def get_driver_team_color(session_results, driver_identifier: str) -> Optional[str]:
    """
    Get driver's team color from session results.

    Args:
        session_results: FastF1 SessionResults object
        driver_identifier (str): Driver's three letter identifier (e.g., 'VER') or driver number

    Returns:
        Optional[str]: Team color (hex code) or None if not found
    """
    driver_info = get_driver_info(session_results, driver_identifier)
    if driver_info:
        team_color = driver_info.get("TeamColor")
        if team_color:
            return f"#{team_color}" if not team_color.startswith("#") else team_color
    return None


def get_driver_country_code(session_results, driver_identifier: str) -> Optional[str]:
    """
    Get driver's country code from session results.

    Args:
        session_results: FastF1 SessionResults object
        driver_identifier (str): Driver's three letter identifier (e.g., 'VER') or driver number

    Returns:
        Optional[str]: Country code or None if not found
    """
    driver_info = get_driver_info(session_results, driver_identifier)
    if driver_info:
        return driver_info.get("CountryCode")
    return None


def get_driver_number(session_results, driver_identifier: str) -> Optional[int]:
    """
    Get driver's racing number from session results.

    Args:
        session_results: FastF1 SessionResults object
        driver_identifier (str): Driver's three letter identifier (e.g., 'VER') or driver number

    Returns:
        Optional[int]: Driver number or None if not found
    """
    driver_info = get_driver_info(session_results, driver_identifier)
    if driver_info:
        driver_number = driver_info.get("DriverNumber")
        if driver_number is not None:
            try:
                return int(driver_number)
            except (ValueError, TypeError):
                return None
    return None


def is_driver_dnf(session_results, driver_identifier: str) -> bool:
    """
    Check if driver did not finish (DNF) the session.

    Args:
        session_results: FastF1 SessionResults object (DataFrame)
        driver_identifier (str): Driver's three letter identifier (e.g., 'VER') or driver number

    Returns:
        bool: True if driver did not finish, False otherwise
    """
    try:
        driver_info = get_driver_info(session_results, driver_identifier)
        if driver_info:
            classified_pos = driver_info.get("ClassifiedPosition", "")
            if isinstance(classified_pos, str):
                classified_pos = classified_pos.upper()
                if classified_pos in [
                    "R",
                    "D",
                    "E",
                    "W",
                ]:  # Retired, Disqualified, Excluded, Withdrawn
                    return True

            status = str(driver_info.get("Status", "")).upper()
            if "DNF" in status or "RETIRED" in status or "ACCIDENT" in status:
                return True

            position = driver_info.get("Position")
            if pd.isna(position) and "Abbreviation" in driver_info:
                return True

    except Exception as e:
        print(f"Error checking DNF status for {driver_identifier}: {e}")

    return False


def get_driver_position(session_results, driver_identifier: str) -> Optional[int]:
    """
    Get driver's finishing position from session results.

    Args:
        session_results: FastF1 SessionResults object
        driver_identifier (str): Driver's three letter identifier (e.g., 'VER') or driver number

    Returns:
        Optional[int]: Finishing position or None if not found/DNF
    """
    driver_info = get_driver_info(session_results, driver_identifier)
    if driver_info:
        position = driver_info.get("Position")
        if position is not None:
            try:
                return int(position)
            except (ValueError, TypeError):
                return None
    return None


def get_driver_team_info(session_results, driver_identifier: str) -> Dict:
    """
    Get comprehensive team information for a driver.

    Args:
        session_results: FastF1 SessionResults object
        driver_identifier (str): Driver's three letter identifier (e.g., 'VER') or driver number

    Returns:
        Dict: Team information including team_name, team_color, country_code
    """
    return {
        "team_name": get_driver_team_name(session_results, driver_identifier) or "",
        "team_color": get_driver_team_color(session_results, driver_identifier) or "",
        "country_code": get_driver_country_code(session_results, driver_identifier)
        or "",
        "driver_number": get_driver_number(session_results, driver_identifier),
        "position": get_driver_position(session_results, driver_identifier),
        "dnf": is_driver_dnf(session_results, driver_identifier),
    }


def get_all_drivers_from_session(session_results) -> list:
    """
    Get list of all driver identifiers from session results.

    Args:
        session_results: FastF1 SessionResults object

    Returns:
        list: List of driver identifiers (abbreviations)
    """
    try:
        if session_results is None or session_results.empty:
            return []

        if "Abbreviation" in session_results.columns:
            return session_results["Abbreviation"].dropna().unique().tolist()
        elif "Driver" in session_results.columns:
            return session_results["Driver"].dropna().unique().tolist()
        else:
            return []

    except Exception as e:
        print(f"Error getting drivers from session: {e}")
        return []


def get_driver_headshot_url(session_results, driver_identifier: str) -> Optional[str]:
    """
    Get driver's headshot URL from session results.

    Args:
        session_results: FastF1 SessionResults object
        driver_identifier (str): Driver's three letter identifier (e.g., 'VER') or driver number

    Returns:
        Optional[str]: Headshot URL or None if not found
    """
    driver_info = get_driver_info(session_results, driver_identifier)
    if driver_info:
        return driver_info.get("HeadshotUrl")
    return None
