import os
from PIL import Image
import streamlit as st
import pandas as pd
import networkx as nx
import plotly.graph_objects as go

# Try importing zoom package
try:
    from streamlit_image_zoom import image_zoom
except ImportError as e:
    image_zoom = None
    st.warning(f"⚠️ 'streamlit-image-zoom' package not found or failed to load: {e}. Zoom functionality will be disabled.")

# ---------------------- UI Styling ---------------------- #
st.set_page_config(page_title="Delhi Metro Route Finder", page_icon="🚇")
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        color: #003566;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🚇 Delhi Metro Route Finder")
st.markdown("### Developed by **Akash Sharma** 🧑‍💻")

# ---------------------- Load Data ---------------------- #
DATA_PATH = "data/Delhi_metro_cleaned.xlsx"
try:
    df = pd.read_excel(DATA_PATH)
except Exception as e:
    st.error(f"⚠️ Could not read Excel file at {DATA_PATH}.\nError: {e}")
    df = pd.DataFrame()

line_colors = {
    "Blue Line": "🔵",
    "Yellow Line": "🟡",
    "Red Line": "🔴",
    "Green Line": "🟢",
    "Pink Line": "🩷",
    "Violet Line": "🔹",
    "Orange Line": "🟠",
    "Magenta Line": "🔹",
    "Grey Line": "⚫",
    "Airport Express": "🟤",
}

# ---------------------- View Mode Selection ---------------------- #
view_mode = st.radio(
    "Choose View Mode:", ["Route Finder", "Metro Map View"], horizontal=True
)

# ---------------------- Metro Map View ---------------------- #
if view_mode == "Metro Map View":
    st.markdown("### 📽️ Interactive Delhi Metro Map")
    with st.expander("🔍 Search a station on map"):
        station_query = st.text_input("Type station name")
        if station_query:
            st.info(f"🔍 You searched for: {station_query.title()}")

    MAP_PATH = "data/Delhi_metro_map.png"
    
    if not os.path.exists(MAP_PATH):
        st.error(f"🗺️ Map image not found at: {MAP_PATH}. Please verify the path or filename.")
    else:
        try:
            Image.MAX_IMAGE_PIXELS = None
            img = Image.open(MAP_PATH)
            if image_zoom:
                image_zoom(img)
                st.caption("🖱 Scroll to zoom, drag to move. 📱 Pinch to zoom on mobile.")
            else:
                st.image(MAP_PATH, use_container_width=True)
                st.caption("📱 Use browser pinch/zoom if needed.")
        except Exception as e:
            st.error(f"❌ Failed to render map: {e}")
            st.image(MAP_PATH, use_container_width=True)

# ---------------------- Route Finder ---------------------- #
else:
    if not df.empty:
        G = nx.Graph()
        for _, row in df.iterrows():
            line = str(row["Line"]).strip().title()
            G.add_edge(row["Station"], row["Connected_Station"], line=line)

        stations = sorted(set(df["Station"]).union(set(df["Connected_Station"])))
        col1, col2 = st.columns(2)
        with col1:
            source = st.selectbox("Source Station", stations)
        with col2:
            destination = st.selectbox("Destination Station", stations)

        if st.button("Get Route"):
            if source == destination:
                st.warning("Source and destination cannot be the same.")
            else:
                try:
                    path = nx.shortest_path(G, source, destination)
                    st.success(f"✅ Route found! Total stops: {len(path) - 1}")
                    st.markdown("### 📍 Route Path:")
                    for i, station in enumerate(path):
                        line_info = df[
                            ((df["Station"] == station) & (df["Connected_Station"].isin(path))) |
                            ((df["Connected_Station"] == station) & (df["Station"].isin(path)))
                        ]["Line"].values
                        line_str = str(line_info[0]).strip().title() if len(line_info) > 0 else "N/A"
                        emoji = next((emoji for name, emoji in line_colors.items() if line_str.startswith(name)), "⚪")
                        st.markdown(
                            f"<div style='font-size:16px; margin-bottom:8px;'><b>{i+1}.</b> {station} <span style='font-size:18px;'>{emoji}</span> <span style='background-color:#f1f3f5; border-radius:5px; padding:2px 6px; font-size:13px;'>{line_str}</span></div>",
                            unsafe_allow_html=True,
                        )
                    st.info(f"Estimated Time: {(len(path) - 1) * 2} minutes")
                    interchanges = []
                    for i in range(1, len(path) - 1):
                        curr_line = df[
                            ((df["Station"] == path[i - 1]) & (df["Connected_Station"] == path[i])) |
                            ((df["Station"] == path[i]) & (df["Connected_Station"] == path[i - 1]))
                        ]["Line"].values
                        next_line = df[
                            ((df["Station"] == path[i]) & (df["Connected_Station"] == path[i + 1])) |
                            ((df["Station"] == path[i + 1]) & (df["Connected_Station"] == path[i]))
                        ]["Line"].values
                        if len(curr_line) > 0 and len(next_line) > 0:
                            curr_line = str(curr_line[0]).strip().title()
                            next_line = str(next_line[0]).strip().title()
                            if curr_line != next_line:
                                interchanges.append((path[i], curr_line, next_line))
                    if interchanges:
                        st.markdown("### 🔁 Interchanges:")
                        for station, from_line, to_line in interchanges:
                            from_emoji = line_colors.get(from_line, "⚪")
                            to_emoji = line_colors.get(to_line, "⚪")
                            st.warning(f"🔁 {station}: {from_emoji} {from_line} ➞ {to_emoji} {to_line}")
                    else:
                        st.info("✅ No interchanges required.")
                except nx.NetworkXNoPath:
                    st.error("❌ No path found between selected stations.")
    else:
        st.error("⚠️ File is empty or not found!")

# ---------------------- Footer ---------------------- #
st.markdown("---")
st.markdown("<center>Made with ❤️ by <b>Akash Sharma</b></center>", unsafe_allow_html=True)
            