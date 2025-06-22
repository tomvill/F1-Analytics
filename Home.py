import streamlit as st

from utils.cache_utils import setup_fastf1_cache
from utils.cache_utils import clear_fastf1_cache, get_cache_info

setup_fastf1_cache()

st.set_page_config(page_title="F1 Analytics", layout="wide", page_icon="🏎️")

st.title("🏁 Welcome to F1 Analytics")
st.markdown("Select a visualization from the sidebar to get started.")

st.markdown("""
## About this Project

This interactive dashboard visualizes Formula 1 race data using the FastF1 API.
Navigate through different visualizations in the sidebar to analyze:

- **Driver Telemetry** - Compare speed, RPM, throttle usage and more
- **Sector Performance** - Analyze sector times across drivers
- **Race Strategy** - Visualize pit stops and race progression
- **Postion and Overtake Insights** - Examine driver positions and overtakes
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

    if st.button("Clear FastF1 Cache", key="clear_cache_btn"):
        success, message = clear_fastf1_cache()
        if success:
            st.success("Cache cleared!")
        else:
            st.info(message)

    cache_size, num_files = get_cache_info()

    if cache_size > 0:
        st.info(
            f"Cache status: Active with {num_files} files ({cache_size / 1048576:.1f} MB)"
        )
    else:
        st.info("Cache status: Empty or not yet created")

st.markdown("""
    ### Authors
    
    This project was developed as part of the **INF8808 Data Visualization** course at Polytechnique Montréal.
    
    Team members:
    
    - **Thomas Villeneuve** - 2150864
    - **Jonathan Roy-Ascanio** - 2152552
    - **Christophe Lapointe** - 2151911
    - **Abdelnour Sikouky** - 2158244
    - **Jordan Caraballo Bonin** - 202254
    
    """)

st.sidebar.title("🏎️ F1 Race Visualizations")
st.sidebar.markdown("Explore race insights through 6 interactive visualizations.")
