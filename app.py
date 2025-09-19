import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from io import BytesIO
import base64

# --------------------
# Streamlit Page Config
# --------------------
st.set_page_config(
    page_title="Encap Post Cure Temperature Profile 2025",
    page_icon="📈",
    layout="wide"
)

# --------------------
# Hide Default Streamlit Menu & Footer
# --------------------
hide_st_style = """
<style>
#MainMenu {visibility: hidden;} 
footer {visibility: hidden;}    
header {visibility: hidden;}    
</style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# --------------------
# Convert Local Image (logo.png) to Base64
# --------------------
logo_path = "logo.png"

def get_base64_of_bin_file(bin_file):
    with open(bin_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

logo_base64 = get_base64_of_bin_file(logo_path)

# --------------------
# Custom Fixed Header
# --------------------
st.markdown(
    f"""
    <style>
    .custom-header {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background-color: white;
        color: black;
        padding: 12px 25px;
        font-size: 22px;
        font-weight: bold;
        display: flex;
        align-items: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.2);
        z-index: 9999;
    }}
    .custom-header img {{
        height: 50px;
        margin-right: 15px;
    }}
    .block-container {{
        padding-top: 60px;
    }}
    </style>

    <div class="custom-header">
        <img src="data:image/png;base64,{logo_base64}" alt="Logo">
        Encap Post Cure Temperature Profile 2025
    </div>
    """,
    unsafe_allow_html=True
)

# --------------------
# Function to show loading popup with rotating image
# --------------------
def show_popup(message="Loading..."):
    placeholder = st.empty()
    
    # Convert loader image to base64
    with open("loader.gif", "rb") as f:  # Replace with your spinner image
        img_base64 = base64.b64encode(f.read()).decode()
    
    placeholder.markdown(
        f"""
        <style>
        @keyframes bounce {{
            0%, 100% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-12px); }}
        }}
        .loader {{
            width: 80px;
            height: 80px;
            margin: 0 auto 10px auto;   /* loader centered with small gap below */
            animation: bounce 1s infinite;
            background-image: url("data:image/png;base64,{img_base64}");
            background-size: contain;
            background-repeat: no-repeat;
        }}
        .popup-overlay {{
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: rgba(0,0,0,0.35);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9998;
        }}
        .popup {{
            background: white;
            padding: 18px 28px;        /* slightly smaller padding */
            border-radius: 12px;
            text-align: center;
            font-size: 16px;
            font-weight: 600;
            box-shadow: 0 3px 10px rgba(0,0,0,0.25);
            max-width: 220px;
        }}
        </style>

        <div class="popup-overlay">
            <div class="popup">
                <div class="loader"></div>
                <div>{message}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    return placeholder


# --------------------
# Step 1: Load all datasets with popup
# --------------------
popup = show_popup("Loading, please wait...")
datasets = {
    "dataset1": pd.read_excel("BMV#80 & BMV#88 & BMV#86 & BMV#69.xlsx", sheet_name="DATA"),
    "dataset2": pd.read_excel("MEM#01 & MEM#02 & BMV#91.xlsx", sheet_name="DATA"),
    "dataset3": pd.read_excel("MEM#03.xlsx", sheet_name="DATA"),
    "dataset4": pd.read_excel("MEM#19 & MEM#20.xlsx", sheet_name="DATA")
    
}
popup.empty()  # Remove popup after loading

# --------------------
# Step 2: Create measurement -> dataset mapping
# --------------------
measurement_map = {}
exclude_cols = ["DATETIME", "CW", "DATE", "LCL", "UCL"]

for name, df in datasets.items():
    for col in df.columns:
        if col not in exclude_cols:
            measurement_map[col] = name

# --------------------
# Step 3: Side-by-side controls
# --------------------
col1, col2 = st.columns([1, 2])

with col1:
    selected_measures = st.multiselect(
        "Select Oven",
        options=list(measurement_map.keys())
    )

if selected_measures:
    dataset_name = measurement_map[selected_measures[0]]
    df = datasets[dataset_name].copy()
    df["DATETIME"] = pd.to_datetime(df["DATETIME"])
    df["DATE"] = pd.to_datetime(df["DATE"])

    with col2:
        min_date, max_date = df["DATE"].min(), df["DATE"].max()
        start_date, end_date = st.date_input(
            "📅 Select Date Range",
            [min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )

    if isinstance(start_date, datetime):
        start_date = start_date.date()
    if isinstance(end_date, datetime):
        end_date = end_date.date()

    # --------------------
    # Step 4: Show popup while filtering & generating chart
    # --------------------
    popup = show_popup("Processing data...")

    df = df[(df["DATE"].dt.date >= start_date) & (df["DATE"].dt.date <= end_date)]

    if not df.empty:
        fig = px.line(
            df,
            x="DATETIME",
            y=selected_measures,
            title=f"Temperature Profile: {', '.join(selected_measures)}"
        )
        fig.update_layout(legend_title_text="")  # Remove "variable" legend title

        # Add control limits if available
        if "LCL" in df.columns:
            fig.add_scatter(
                x=df["DATETIME"], y=df["LCL"], mode="lines", name="LCL",
                line=dict(color="red", dash="dash")
            )
        if "UCL" in df.columns:
            fig.add_scatter(
                x=df["DATETIME"], y=df["UCL"], mode="lines", name="UCL",
                line=dict(color="red", dash="dash")
            )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ No data in selected range.")

    popup.empty()  # Remove popup automatically

    # --------------------
    # Step 5: Raw data and download
    # --------------------
    st.subheader("📋 Filtered Raw Data")
    st.dataframe(df, use_container_width=True)

    def to_excel(dataframe):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            dataframe.to_excel(writer, index=False, sheet_name="FilteredData")
        return output.getvalue()

    excel_data = to_excel(df)

    st.download_button(
        label="⬇️ Download Excel",
        data=excel_data,
        file_name="filtered_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    st.download_button(
        label="⬇️ Download CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="filtered_data.csv",
        mime="text/csv",
    )
