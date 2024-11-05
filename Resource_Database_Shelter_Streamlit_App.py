import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium

st.set_page_config(layout = "wide")
button_session_states = ["next_button", "back_button", "clear_client_info"]

st.write(st.session_state)

dataframe_path = "Resource Database Datasets/[CLEANED] Santa Clara County Shelters- 11.5.24.csv"

client_information_inputs = [
    "Veterans",
    "Survivors of Domestic Violence & Human Trafficking",
    "Adult (18 - 24)",
    "Adult Men",
    "Adult Women",
    "Family ",
    "Young Families (parents 18-24)",
    "Child(ren) (0 - 5)",
    "Child(ren) (12 - 17)",
    "Child(ren) (0 - 17)",
    "Sex Offender"
]

@st.cache_data
def process_resource_dataframe (dataframe_path: str) -> pd.DataFrame:
    resource_dataframe = pd.read_csv(dataframe_path).drop("Unnamed: 0", axis = 1)
    return resource_dataframe

def automatic_checkbox_checking ():
    if "current_shelter_idx" not in st.session_state:
        st.session_state["current_shelter_idx"] = 0
    else:
        st.session_state["current_shelter_idx"] = 0

    if st.session_state["Adult Men"]:
        st.session_state["Adult Women"] = False
    elif st.session_state["Adult Women"]:
        st.session_state["Adult Men"] = False

    if st.session_state["Young Families (parents 18-24)"] == True:
        st.session_state["Family "] = True

    if st.session_state["Child(ren) (0 - 5)"] or st.session_state["Child(ren) (12 - 17)"]:
        st.session_state["Child(ren) (0 - 17)"] = True

    if (st.session_state["Adult Men"] or st.session_state["Adult Women"] or st.session_state["Adult (18 - 24)"]) and st.session_state["Child(ren) (0 - 17)"]:
        st.session_state["Family "] = True
    if st.session_state["Adult (18 - 24)"] and st.session_state["Child(ren) (0 - 17)"]:
        st.session_state["Young Families (parents 18-24)"] = True

    if st.session_state["clear_client_info"]:
        st.session_state["shelter_search_terms"] = ""
        st.session_state["current_shelter_idx"] = 0
        for key in st.session_state.keys():
            if key not in button_session_states and key != "shelter_search_terms":
                st.session_state[key] = False

def update_shelter_search_terms_on_enter ():
    if st.session_state["shelter_search_terms"] != "":
        st.session_state["current_shelter_idx"] = 0

def get_client_information () -> list:
    client_information_inputs = {
        "Adult (18 - 24)": "Young Adult (18 - 24) Shelter",
        "Survivors of Domestic Violence & Human Trafficking": "Shelters For Survivors of Domestic Violence & Human Trafficking",
        "Adult Men": "Shelters For Men",
        "Adult Women": "Shelter For Women",
        "Family ": "Shelters For Families",
        "Young Families (parents 18-24)": "Shelters For Young Families (parents 18 - 24)",
        "Child(ren) (0 - 5)": "Shelters For Families With Young Children (0 - 5)",
        "Child(ren) (12 - 17)": "Shelters For Families With Children 12 - 17",
        "Child(ren) (0 - 17)": "Shelters For Families With Children 0 - 17",
        "Veterans": "Shelters For Veterans"
    }

    client_information = []

    st.sidebar.header("Input Specific Shelter Requirements")

    for key, value in client_information_inputs.items():
        is_category = st.sidebar.checkbox(
            label = value,
            key = key,
            on_change = automatic_checkbox_checking
        )
        if is_category:
            client_information.append(key)

    clear_client_info_button = st.sidebar.button(
        "Clear Client Information",
        key = "clear_client_info",
        on_click = automatic_checkbox_checking
    )

    shelter_search_terms = st.text_input(
        "Search For Shelters",
        key = "shelter_search_terms",
        on_change = update_shelter_search_terms_on_enter
    )
    
    return client_information

@st.cache_data
def get_suggested_shelters (client_information: list, resource_database: pd.DataFrame) -> pd.DataFrame:
    all_false = True
    for item in client_information:
        if item != False:
            all_false = False
    
    if all_false:
        return resource_database
    
    suggested_shelters = resource_database.copy()

    if "Veterans" in client_information or "Adult Men" in client_information or "Adult Women" in client_information:
        client_information.append("Single Adult")
    
    indexes_of_suggested_shelters = np.array([])
    suggested_shelters = suggested_shelters.astype("str")
    for category in client_information:
        indexes_for_category = suggested_shelters[suggested_shelters[category].str.contains("T")].index.to_numpy()
        indexes_of_suggested_shelters = np.append(indexes_of_suggested_shelters, indexes_for_category)
    
    if len(indexes_of_suggested_shelters) > 0:
        indexes_of_suggested_shelters = list(set(indexes_of_suggested_shelters))
        indexes_of_suggested_shelters = np.array(indexes_of_suggested_shelters)

    suggested_shelters = suggested_shelters.iloc[indexes_of_suggested_shelters]

    suggested_shelters = suggested_shelters.reset_index(drop = True)

    return suggested_shelters

def create_quick_shelter_to_string (suggested_shelters: pd.DataFrame, shelter_idx: int) -> str:
    to_return = ""
    for column in suggested_shelters.columns:
        to_return += str(suggested_shelters[column].iloc[shelter_idx]) + "\n"

    return to_return

def update_shelters_from_search (suggested_shelters: pd.DataFrame) -> pd.DataFrame:
    try:
        search_terms = st.session_state["shelter_search_terms"].split(" ")
    except:
        return
    
    search_term_columns = []

    for search_term in search_terms:
        suggested_shelters[f"Contains {search_term}"] = np.zeros(len(suggested_shelters))
        search_term_columns.append(f"Contains {search_term}")
    
    for index in suggested_shelters.index:
        for search_term in search_terms:
            search_term_col = f"Contains {search_term}"
            shelter_to_string = create_quick_shelter_to_string(suggested_shelters, index)
            suggested_shelters.at[index, search_term_col] = 0 if search_term in shelter_to_string else 1

    suggested_shelters = suggested_shelters.sort_values(by = search_term_columns)

    suggested_shelters = suggested_shelters.reset_index(drop = True)

    return suggested_shelters

resource_dataframe = process_resource_dataframe(dataframe_path)
client_information = get_client_information()
suggested_shelters = get_suggested_shelters(client_information, resource_dataframe)
suggested_shelters = update_shelters_from_search(suggested_shelters)

def create_map (suggested_shelters: pd.DataFrame) -> folium.Map:
    shelter_map = folium.Map(
        location = [37.335480, -121.893028]
    )

    if len(suggested_shelters) == len(resource_dataframe):
        suggested_shelters = resource_dataframe.astype(str)

    indexes_of_valid_address = []
    
    for i in range(len(suggested_shelters["Latitude"].to_numpy())):
        if suggested_shelters.iloc[i]["Latitude"] != "nan":
            indexes_of_valid_address.append(i)

    valid_address_df = suggested_shelters.iloc[indexes_of_valid_address]

    latitudes = valid_address_df["Latitude"].to_numpy()
    longitudes = valid_address_df["Longitude"].to_numpy()

    shelter_names = valid_address_df["Shelter Name"].to_numpy()

    for i in range(len(latitudes)):
        lat = latitudes[i]
        long = longitudes[i]

        folium.Marker(
            location = (lat, long),
            popup = shelter_names[i]
        ).add_to(shelter_map)
    
    st_folium(shelter_map, use_container_width = True, height = 400, returned_objects=[])

def create_shelter_information (shelter_name: str, suggested_shelters: pd.DataFrame) -> None:
    shelter_index = suggested_shelters[suggested_shelters["Shelter Name"] == shelter_name].index.to_numpy()[0]
    st.markdown(f"# {shelter_index + 1}. {shelter_name} \n")
    st.divider()
    
    columns_to_show = [
        "Category",
        "Shelter Managed By",
        "Congregate?",
        "Site Description",
        "Phone #",
        "Populations Served",
        "Phone Operating Hours",
        "Eligibility Criteria",
        "Website",
        "# of Units",
        "# of Beds",
        "Setting Type",
        "Rent / Program Fee",
        "Meals Offered",
        "Services & Amenities",
        "Here4You",
        "How to Apply",
        "Application Requirements"
    ]

    columns_to_remove_if_null = [
        "Site Description",
        "Eligibility Criteria",
        "How To Apply"
    ]

    to_return = ""

    def process_phone_number (phone_number: str) -> str:
        phone_number = phone_number.split(" ")
        area_code = phone_number[0]
        
        return f"({area_code}) {phone_number[1]}-{phone_number[2]}"

    for column in columns_to_show:
        if column == "Distance From User" and "Distance From User" not in suggested_shelters.columns:
            continue

        if (column == "Application Requirements" or column == "How to Apply") and "T" in suggested_shelters.at[shelter_index, "Here4You"].upper():
            continue

        if column == "Congregate?" and "F" in suggested_shelters.at[shelter_index, column].upper():
            to_return += f"## Non-congregate shelter\n"
            continue
        elif column == "Congregate?" and "T" in suggested_shelters.at[shelter_index, column].upper():
            to_return += f"## Congregate shelter\n"
            continue
        
        if column == "# of Units" and "T" in suggested_shelters.at[shelter_index, "Congregate?"].upper():
            to_return += f"## {column}: 1\n"
            continue

        if column in columns_to_remove_if_null and "nan" in suggested_shelters.at[shelter_index, column]:
            continue

        if column == "Rent / Program Fee" and "nan" in suggested_shelters.at[shelter_index, column]:
            to_return += f"## {column}: Free\n"
            continue
        
        if column == "Here4You" and "T" in suggested_shelters.at[shelter_index, "Here4You"].upper():
            to_return += f"## Apply via Here4You ((408)-385-2400, available from 9 am to 7 pm, 7 days a week)\n"
            continue
        elif column == "Here4You" and "T" not in suggested_shelters.at[shelter_index, "Here4You"].upper():
            to_return += f"## Not available through Here4You\n"
            continue

        if column == "Meals Offered" and "T" in suggested_shelters.at[shelter_index, column].upper():
            to_return += f"## {column}: {suggested_shelters.at[shelter_index, column].capitalize()}\n"
            continue

        if column == "Phone #":
            try:
                to_return += f"## {column}: {process_phone_number(suggested_shelters.at[shelter_index, column])}\n"
            except: #Catches error if phone number is of incorrect format and/or is null
                to_return += f"## {column}: {suggested_shelters.at[shelter_index, column]}\n"

            continue

        shelter_information = suggested_shelters.at[shelter_index, column]
        if column == "Distance From User":
            if str(shelter_information) == "inf":
                shelter_information = "N/A"
            else:
                shelter_information = np.round(shelter_information, 2)
                shelter_information = str(shelter_information) + " miles"
        shelter_information = shelter_information.replace("\n", "; ")
        shelter_information = shelter_information.replace("$", "")
        shelter_information = shelter_information.replace("*", "")

        column = column.replace("?", "")
        to_return += f"## {column}: {shelter_information}\n"

    st.markdown(to_return)

def scrollthrough_shelters ():
    try:
        max_index = int(suggested_shelters.index.to_numpy()[-1])
    except:
        return
    
    not_buttons = [key for key in st.session_state.keys() if key not in button_session_states]

    if st.session_state["back_button"]:
        if 'current_shelter_idx' not in st.session_state:
            st.session_state['current_shelter_idx'] = 1

        if st.session_state["current_shelter_idx"] == 0:
            st.session_state["current_shelter_idx"] = max_index
        else:
            st.session_state["current_shelter_idx"] -= 1
    
    if st.session_state["next_button"]:
        if 'current_shelter_idx' not in st.session_state:
            st.session_state['current_shelter_idx'] = -1
        
        if st.session_state["current_shelter_idx"] == max_index:
            st.session_state["current_shelter_idx"] = 0
        else:
            st.session_state["current_shelter_idx"] += 1

def create_shelter_scrollthorugh (suggested_shelters: pd.DataFrame) -> None:
    columns = st.columns([1, 1, 10, 1])
    with columns[0]:
        st.button(
            label = "Back",
            key = "back_button",
            on_click = scrollthrough_shelters
        )
    with columns[-1]:
        st.button(
            label = "Next",
            key = "next_button",
            on_click = scrollthrough_shelters
        )
    
    if "current_shelter_idx" not in st.session_state or len(suggested_shelters) == 0:
        st.header("No Shelters Found")
    
    else:
        current_shelter_index = st.session_state["current_shelter_idx"]
        try:
            shelter_name_to_display = suggested_shelters.iloc[current_shelter_index]["Shelter Name"]
            create_shelter_information(shelter_name_to_display, suggested_shelters)
        except:
            st.header("No Shelters Found")

create_map(suggested_shelters)

create_shelter_scrollthorugh(suggested_shelters)