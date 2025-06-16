import os

import fastf1
import streamlit as st

from utils.cache_utils import setup_fastf1_cache

setup_fastf1_cache()

st.set_page_config(page_title="F1 Analytics", layout="wide", page_icon="🏎️")

st.title("🏁 Welcome to F1 Analytics")
st.markdown("Select a visualization from the sidebar to get started.")

st.markdown("""
## About this Project

This interactive dashboard visualizes Formula 1 race data using the FastF1 package.
Navigate through different visualizations in the sidebar to analyze:

- **Driver Telemetry** - Compare speed, RPM, throttle usage and more
- **Sector Performance** - Analyze sector times across drivers
- **Race Strategy** - Visualize pit stops and race progression
- **Speed Insights** - Examine top speeds and overtaking zones
- **Weather Impact** - See how weather affects lap times
- **Track Dynamics** - View track-specific data and racing lines
""")

with st.expander("Technical Details", expanded=False):
    st.markdown("""
    ### Data Source
    All data is provided by the FastF1 API, which accesses official F1 timing data.
    
    ### Cache Management
    This app uses a local cache to improve performance.
    When you first view a race, data is downloaded and then cached for future use.
    """)

    cache_path = os.path.abspath(".fast-f1-cache")
    cache_size = 0
    num_files = 0

    if st.button("Clear FastF1 Cache", key="clear_cache_btn"):
        try:
            fastf1.Cache.clear_cache(cache_path)
            st.success("Cache cleared!")
            cache_size = 0
            num_files = 0
        except FileNotFoundError:
            st.info("Cache directory does not exist.")
        except Exception as e:
            st.error(f"Error clearing cache: {e}")

    try:
        for path, dirs, files in os.walk(cache_path):
            num_files += len(files)
            for f in files:
                cache_size += os.path.getsize(os.path.join(path, f))

        if cache_size > 0:
            st.info(
                f"Cache status: Active with {num_files} files ({cache_size / 1048576:.1f} MB)"
            )
        else:
            st.info("Cache status: Directory exists but is empty")
    except Exception:
        st.info("Cache status: Not yet created")

st.sidebar.title("🏎️ F1 Race Visualizations")
st.sidebar.markdown("Explore race insights through 6 interactive visualizations.")
