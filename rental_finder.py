import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# Google Sheets Setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
#creds = ServiceAccountCredentials.from_json_keyfile_name("google_sheets_creds.json", scope)
# Load Google Sheets credentials from Streamlit secrets
creds_dict = st.secrets["google_sheets"]
#creds_json = json.loads(json.dumps(creds_dict))  # Convert TOML to JSON format
creds_json = dict(st.secrets["google_sheets"])

# Authorize GSpread with the JSON credentials
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
client = gspread.authorize(creds)

#client = gspread.authorize(creds)

# Open Google Sheet by Key
sheet = client.open_by_key("1ImV4ARo-W3GvBhFcYcBeaov_DCd6QK7yKFOWlODylMI").sheet1

# Load data from Google Sheets
data = pd.DataFrame(sheet.get_all_values())

# Check if data exists
if not data.empty:
    # Use the first row as column names
    data.columns = data.iloc[0]
    data = data[1:]  # Drop first row since it's now used as column headers
    data.columns = data.columns.astype(str).str.strip()  # Ensure all column names are strings and clean
else:
    st.error("❌ No data found in Google Sheets.")
    st.stop()

st.title("🏠 Mombasa Rental Listings")

# Maintain app state across interactions
if "option" not in st.session_state:
    st.session_state["option"] = "View Listings"  # Default

# Buttons for switching views
col1, col2 = st.columns(2)
if col1.button("🔍 View Listings"):
    st.session_state["option"] = "View Listings"
if col2.button("➕ Add a Listing"):
    st.session_state["option"] = "Add a Listing"

# Set option based on session state
option = st.session_state["option"]

if option == "View Listings":
    # Sidebar Filters
    st.sidebar.header("Filter Listings")
    region_filter = st.sidebar.selectbox("Select Region", ["All"] + list(data["Region"].dropna().astype(str).unique()))
    rent_range = st.sidebar.slider("Rent Range (KES)", min_value=5000, max_value=100000, value=(5000, 50000))
    deposit_range = st.sidebar.slider("Deposit Range (KES)", min_value=0, max_value=200000, value=(0, 50000))
    security_filter = st.sidebar.slider("Security Level (1-5)", min_value=1, max_value=5, value=(1, 5))
    parking_filter = st.sidebar.selectbox("Parking Available", ["All", "Yes", "No"])
    water_filter = st.sidebar.selectbox("24/7 Water", ["All", "Yes", "No"])

    # Apply filters
    df_filtered = data[
        ((data["Region"] == region_filter) | (region_filter == "All")) &
        (data["Rent (KES)"].astype(float) >= rent_range[0]) & (data["Rent (KES)"].astype(float) <= rent_range[1]) &
        (data["Deposit Required (KES)"].astype(float) >= deposit_range[0]) & (data["Deposit Required (KES)"].astype(float) <= deposit_range[1]) &
        (data["Security Rating (1-5)"].astype(float) >= security_filter[0]) & (data["Security Rating (1-5)"].astype(float) <= security_filter[1]) &
        ((data["Parking"] == parking_filter) | (parking_filter == "All")) &
        ((data["24/7 Water"] == water_filter) | (water_filter == "All"))
    ]

    st.header("🏠 Available Rentals")
    st.dataframe(df_filtered.style.set_properties(**{'text-align': 'left'}), height=600, width=1200)

elif option == "Add a Listing":
    st.header("📌 Add a New Listing")

    # Track selected house types outside the form to enable dynamic updates
    if "selected_house_types" not in st.session_state:
        st.session_state["selected_house_types"] = []

    selected_house_types = st.multiselect(
        "Type of House", ["Bedsitter", "Studio", "1 Bedroom", "2 Bedroom"], 
        default=st.session_state["selected_house_types"]
    )

    st.session_state["selected_house_types"] = selected_house_types

    with st.form("listing_form"):
        apartment_name = st.text_input("Apartment Name")
        description = st.text_area("Description")
        location = st.text_input("Location (e.g., Bamburi)")
        region = st.selectbox("Region", ["Mombasa Island", "Mainland"])
        distance = st.number_input("Distance from CBD (in km)", min_value=0.0)
        security = st.slider("Location Security", 1, 5, 3)
        parking = st.selectbox("Parking", ["Yes", "No"])
        water = st.selectbox("24/7 Water", ["Yes", "No"])
        
        # Rent input for each selected house type outside the form to enable instant updates
        rent_values = {}
        for house in st.session_state["selected_house_types"]:
            rent_values[house] = st.number_input(f"Rent for {house} (KES)", min_value=5000, max_value=100000, step=500, key=f"rent_{house}")
        
        deposit = st.number_input("Deposit (KES)", min_value=0, max_value=200000, step=5000)
        gps_link = st.text_input("Google Maps Link")
        comments = st.text_area("Additional Comments")
        submit_button = st.form_submit_button("Add Listing")

        if submit_button:
            for house in st.session_state["selected_house_types"]:
                new_listing = [
                    apartment_name, description, region, location, distance, security,
                    house, parking, water, rent_values[house], deposit, gps_link, comments
                ]
                sheet.append_row(new_listing)
            st.success("Listing Added Successfully!")