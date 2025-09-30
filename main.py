# Import configuration settings from the 'settings' module
from settings import camp_api_url, main_log_path, login_url, filter_path, download_csv_row_data, dashboard_reload_time,api_end_url
from campaign_details_dashboard_main import main as cmp_details_main
from agent_details_dashboard_main import main as agent_details_main

# Import necessary modules
from streamlit_autorefresh import st_autorefresh  # Module for auto-refreshing Streamlit app
from streamlit_echarts import st_echarts  # Module for integrating ECharts with Streamlit
import streamlit as st  # Module for creating Streamlit apps
import traceback  # Module for printing stack traces to debug errors
import threading  # Module for multi-threading
import datetime  # Module for date and time operations
import requests  # Module for making HTTP requests
import logging  # Module for logging messages
import json  # Module for working with JSON data
import os  # Module for interacting with the operating system
import base64


# Setting up logging to track the program's execution
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(lineno)s - %(message)s',  # Define the format of log messages
    level=logging.INFO,  # Set the logging level to INFO to capture informational messages
    filename=main_log_path  # Specify the log file to write log messages to
)

# Initialize the main logger
log = logging.getLogger('__main__')  # Get a logger specifically for the main module

# Initialize a threading lock for thread synchronization
lock = threading.Lock()  # Create a lock object to ensure thread-safe operations

# Set the behavior of the Streamlit page
st.set_page_config(
    page_title="Dashboard",  # Set the title of the web page
    page_icon="https://www.c-zentrix.com/images/favicon.png",  # Set the icon of the web page
    layout="wide",  # Set the layout of the web page to wide
    initial_sidebar_state='collapsed'  # Set the initial state of the sidebar to collapsed
)

# Include Font Awesome CSS for icons
st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">', unsafe_allow_html=True)

# Include Font Awesome JavaScript for icons
st.markdown('<script src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/js/all.min.js"></script>', unsafe_allow_html=True)

# Add a header with a logo to the Streamlit page
st.markdown(
    f"""
        <div class="test12" id="dashboard_data">
            <img src="https://stg.c-zentrix.com/images/C-Zentrix-logo-white.png" style="width: 110px;">
        </div>
    """,
    unsafe_allow_html=True,
)

# Set the theme for Plotly charts (None to use Streamlit's default theme)
theme_plotly = None

# Function to read a CSS file and cache the result to avoid re-reading it on each execution
@st.cache
def read_style():
    with open("style.css") as f:
        return f.read()


def access_url_parm():
    """
    Access and process URL parameters to fetch campaign data.

    Returns:
        tuple: A tuple containing the list of campaign names, status, session, and username.
    """
    try:
        # Get the query parameters from the URL
        query_params = st.experimental_get_query_params()
        if len(query_params) != 0:
            encrypted_text = query_params['data'][0]
            encrypted_text = encrypted_text.replace(" ", "+")

            key_cypher = 5

            try:
                # Decode the base64 encoded string
                decoded_text = base64.b64decode(encrypted_text).decode()
                decoded_string = ''
                for char in decoded_text:
                    # Reverse the character encoding by subtracting the key
                    decoded_char = chr(ord(char) - key_cypher)
                    decoded_string += decoded_char
            except:
                # pass
                decoded_text = base64.b64decode(encrypted_text)
                decoded_string = ''
                for byte in decoded_text:
                    # Reverse the character encoding by subtracting the key
                    decoded_char = chr(byte - key_cypher)
                    decoded_string += decoded_char
            
            decoded_string = json.loads(decoded_string)


            # Extract the values of 'username' and 'session' from the query parameters
            username = decoded_string.get("username", '')
            session = decoded_string.get("seesion_id", '')

            # Prepare the payload for the POST request
            payload = {
                "transaction_id": "CTI_DASHBOARD",
                "username": username,
                "session": session,
                "resFormat": "1"
            }


            try:
                # Send a POST request to the campaign API URL with the payload
                response = requests.post(camp_api_url, json=payload)
                result_resp = response.text  # Get the response text
            except:
                # Handle any exceptions that occur during the POST request
                result_resp = ""

            if result_resp != "":
                # If the response is not empty, parse the JSON data
                parsed_data = json.loads(result_resp)
                status = parsed_data["status"]  # Get the status from the parsed data
                if status == "SUCCESS":
                    # If the status is "SUCCESS", extract the campaign names
                    campaigns_str = parsed_data['data']['campaigns']
                    campaign_names_list = [name.strip() for name in campaigns_str.split(',')]  # Split and clean the campaign names
                else:
                    campaign_names_list = []  # If status is not "SUCCESS", set an empty list for campaign names
                return campaign_names_list, status, session, username  # Return the campaign names, status, session, and username
            else:
                # If the response is empty, set default values
                campaign_names_list = []
                status = "SUCCESS"
                session = ""
                username = ""
                return campaign_names_list, status, session, username  # Return the default values
        else:
            campaign_names_list = None
            status = None
            session = None 
            username = None
            return campaign_names_list, status, session, username  # Return the default values


    except Exception as err:
        # Log any exceptions that occur and print the stack trace
        log.error(str(err))
        traceback.print_exc()


def dashboard_list():
    """
    Display a sidebar filter with a dropdown menu to select a dashboard name.
    """

    try:
        with st.sidebar:
            st.markdown('<div class="sidebar-title">📈 Dashboards</div>', unsafe_allow_html=True)

            # Initialize session state variables if not already set
            if "selected_dashboard" not in st.session_state:
                st.session_state.selected_dashboard = None

            with st.container():
                if st.button("📞 Telephony Dashboard", key="telephony_dashboard"):
                    st.session_state.selected_dashboard = "telephony_dashboard"

                if st.button("🔊 Campaign Details Dashboard", key="campaign_dashboard"):
                    st.session_state.selected_dashboard = "campaign_dashboard"

                if st.button("👨‍💻 Agent Details Dashboard", key="agent_dashboard"):
                    st.session_state.selected_dashboard = "agent_dashboard"

            # Return current selected dashboard value from session state
            #return "agent_dashboard" 
            return st.session_state.selected_dashboard

    except Exception as err:
        log.error(str(err))
        traceback.print_exc()
        return None


def sidebar_filter(campaign_names_list):
    """
    Display a sidebar filter with a dropdown menu to select a campaign name.

    Args:
        campaign_names_list (list): List of campaign names to be displayed in the dropdown.
        status (str): Status of the campaign data fetch.

    Returns:
        str: The selected campaign name from the dropdown.
    """
    try:
        # Create a dropdown (selectbox) with the list of campaign names
        selected_campaign_name = st.selectbox("Select Campaign Name", campaign_names_list)
        # Return the selected campaign name
        return selected_campaign_name
    except Exception as err:
        # Log any exceptions that occur and print the stack trace
        log.error(str(err))
        traceback.print_exc()


def campaign_type_filter():
    """
    Display a sidebar filter with a dropdown menu to select a campaign type.

    Returns:
        str: The selected campaign type from the dropdown.
    """
    try:
        # List of campaign types to be displayed in the dropdown
        campaign_type_list = ["ALL", "INBOUND", "OUTBOUND"]

        # Create a sidebar in the Streamlit app
        #with st.sidebar:
        # Create a dropdown (selectbox) with the list of campaign types
        selected_campaign_type = st.selectbox("Select Campaign Type", campaign_type_list)
        # Return the selected campaign type
        return selected_campaign_type
    except Exception as err:
        # Log any exceptions that occur and print the stack trace
        log.error(str(err))
        traceback.print_exc()


def get_date_range():
    """
    Calculate and return various date ranges based on today and yesterday's dates.

    Returns:
        dict: A dictionary where the keys are date range labels and the values are lists containing the start and end dates for each range.
    """
    try:
        from datetime import datetime, timedelta

        # Get today's date
        today = datetime.now() - timedelta(days=0)

        # Get yesterday's date
        yesterday = datetime.now() - timedelta(days=1)

        # Calculate the start date for various ranges relative to yesterday
        seven_day_date = yesterday - timedelta(days=7)  # 7 days ago from yesterday
        thirty_day_date = yesterday - timedelta(days=30)  # 30 days ago from yesterday
        three_months_date = yesterday - timedelta(days=3*30)  # 3 months ago from yesterday
        six_months_date = yesterday - timedelta(days=6*30)  # 6 months ago from yesterday
        year_date = yesterday - timedelta(days=365)  # 365 days ago from yesterday

        # Create date range lists with start and end dates formatted as strings
        today_list = [today.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')]
        yesterday_list = [yesterday.strftime('%Y-%m-%d'), yesterday.strftime('%Y-%m-%d')]
        seven_day_list = [seven_day_date.strftime('%Y-%m-%d'), yesterday.strftime('%Y-%m-%d')]
        thirty_day_list = [thirty_day_date.strftime('%Y-%m-%d'), yesterday.strftime('%Y-%m-%d')]
        three_months_list = [three_months_date.strftime('%Y-%m-%d'), yesterday.strftime('%Y-%m-%d')]
        six_months_list = [six_months_date.strftime('%Y-%m-%d'), yesterday.strftime('%Y-%m-%d')]
        year_date_list = [year_date.strftime('%Y-%m-%d'), yesterday.strftime('%Y-%m-%d')]

        # Create a dictionary mapping date range labels to their respective lists of dates
        date_range_dict = {
            "Today": today_list,
            "Yesterday": yesterday_list,
            "Last 7 Days": seven_day_list,
            "Last Thirty Days": thirty_day_list,
            "Last 3 Months": three_months_list,
            "Last 6 Months": six_months_list,
            "Last Year": year_date_list
        }

        return date_range_dict

    except Exception as err:
        # Log any errors that occur and print the stack trace for debugging
        log.error(str(err))
        traceback.print_exc()


def filter_for_date_wise(selected_campaign_name):
    """
    Provides a date range based on the selected filter and campaign name.

    Args:
        selected_campaign_name (str): The name of the selected campaign.

    Returns:
        tuple: A tuple containing:
            - start_date (datetime.date): The start date for the selected filter range.
            - end_date (datetime.date): The end date for the selected filter range.
            - choose_analytics (str): A string describing the selected date range for analytics.
            - selected_filter_name (str): The name of the selected filter.
    """
    try:
        from datetime import datetime

        # List of available date filters
        filter_list = ["Today", "Yesterday", "Last 7 Days", "Last Thirty Days", "Last 3 Months", "Last 6 Months", "Last Year", "Customize Date"]

        # Create a sidebar with a select box to choose the filter
        #with st.sidebar:
        selected_filter_name = st.selectbox("Select Filter", filter_list,key="filter_selectbox")

        # Initialize variables for the date range and analytics description
        start_date = end_date = None
        choose_analytics = ""

        # Get the date range dictionary from the get_date_range function
        date_range_dict = get_date_range()

        # Determine the start and end dates based on the selected filter
        if selected_filter_name in date_range_dict:
            date_range = date_range_dict[selected_filter_name]
            start_date = datetime.strptime(date_range[0], '%Y-%m-%d').date()
            end_date = datetime.strptime(date_range[1], '%Y-%m-%d').date()
            choose_analytics = f"<p>{selected_campaign_name} From {start_date} to {end_date}.</p>"
            choose_analytics = ""

        return start_date, end_date, choose_analytics, selected_filter_name

    except Exception as err:
        # Log any errors that occur and print the stack trace for debugging
        log.error(str(err))
        traceback.print_exc()


def send_post_request(selected_campaign_name, start_date, end_date, selected_filter_name, selected_campaign_type):
    # The payload (data) to be sent in the request body
    data = {
        "selected_campaign_name": selected_campaign_name,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "selected_filter_name": selected_filter_name,
        "selected_campaign_type": selected_campaign_type
    }


    # Headers to specify that we are sending JSON data
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        # Send the POST request
        response = requests.post(api_end_url, headers=headers, data=json.dumps(data))

        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            data = data["data"]
        else:
            data = [{'average_handling_time': '00:00:00'}, {'average_wait_time': '00:00:00'}, {'average_wrapup_time': '00:00:00'}, {'average_call_duration': '00:00:00'}, {'abandon_rate': 0}, {'total_answered_call': 0}, {'next_call_time': 0}, {}, {'average_queue_time': 0}, {'inbound_abandon_after_20': 0, 'inbound_abandon_within_20': 0}, {'inbound_answered_after_20': 0, 'inbound_answered_within_20': 0}, {'total_agent_manual_outbound': 0}, {'total_agent_progressive_inbound': 0}, {'total_agent_predictive': 0}, {'outbound_answered_after_20': 0, 'outbound_answered_within_20': 0}, {'success_percentage': 0, 'failure_percentage': 0}, {'agent_away': 0, 'agent_available': 0, 'agent_busy': 0, 'agent_after_call_work': 0, 'agent_total': 0}, {'phone_no_list': [], 'queue_time_list': []}, {'sla': 0}, {'call_status_disposition': 0}, {'agent_id_list': [], 'agent_aht_list': [], 'agent_call_volume': []}, {'hour_list': [], 'aht_value_list': [], 'call_volue_list': []}, {'ivrperformance': {'exception': 0, 'ivr_abandoned': 0, 'call_to_agent': 0}}]

        return data


    except requests.exceptions.RequestException as e:
        data = [{'average_handling_time': '00:00:00'}, {'average_wait_time': '00:00:00'}, {'average_wrapup_time': '00:00:00'}, {'average_call_duration': '00:00:00'}, {'abandon_rate': 0}, {'total_answered_call': 0}, {'next_call_time': 0}, {}, {'average_queue_time': 0}, {'inbound_abandon_after_20': 0, 'inbound_abandon_within_20': 0}, {'inbound_answered_after_20': 0, 'inbound_answered_within_20': 0}, {'total_agent_manual_outbound': 0}, {'total_agent_progressive_inbound': 0}, {'total_agent_predictive': 0}, {'outbound_answered_after_20': 0, 'outbound_answered_within_20': 0}, {'success_percentage': 0, 'failure_percentage': 0}, {'agent_away': 0, 'agent_available': 0, 'agent_busy': 0, 'agent_after_call_work': 0, 'agent_total': 0}, {'phone_no_list': [], 'queue_time_list': []}, {'sla': 0}, {'call_status_disposition': 0}, {'agent_id_list': [], 'agent_aht_list': [], 'agent_call_volume': []}, {'hour_list': [], 'aht_value_list': [], 'call_volue_list': []}, {'ivrperformance': {'exception': 0, 'ivr_abandoned': 0, 'call_to_agent': 0}}]
        return data
        # Handle any exceptions (e.g., network issues, server errors)
        # print(f"An error occurred: {e}")


def sidebar_date_picker(selected_campaign_name):
    """
    Provides a custom date range selector in the sidebar for the user to pick start and end dates.

    Args:
        selected_campaign_name (str): The name of the selected campaign.

    Returns:
        tuple: A tuple containing:
            - start_date (datetime.date): The start date selected by the user.
            - end_date (datetime.date): The end date selected by the user.
            - choose_analytics (str): A description of the selected date range or an error message.
    """
    try:
        import datetime
        from datetime import timedelta

        # Get the current date and time
        today = datetime.datetime.now()

        # Set default date range: start date is 366 days ago, end date is yesterday
        default_start_date_yesterday = today - timedelta(days=366)
        default_end_date_yesterday = today - timedelta(days=1)

        # Create a date input widget in the sidebar for selecting a date range
        #with st.sidebar:
        d = st.date_input(
            "Select Date Range",
            (default_start_date_yesterday, default_end_date_yesterday),
        )

        # Initialize variables for start and end dates
        start_date = end_date = ""

        # Extract start and end dates from the date input widget
        if len(d) == 2:
            start_date = d[0]
            end_date = d[1]

        # Create a descriptive string for the selected date range
        if start_date and end_date:
            choose_analytics = f"<p>{selected_campaign_name} From {start_date} to {end_date}.</p>"
            choose_analytics = ""
        else:
            choose_analytics = "<p>Please Select Both date Start and End....</p>"

        return start_date, end_date, choose_analytics

    except Exception as err:
        # Log any errors that occur and print the stack trace for debugging
        log.error(str(err))
        traceback.print_exc()


def select_box(campaign_names_list):
    try:
       #sidebar_date_picker(selected_campaign_name)
       col1, col2, col3, col4 = st.columns(4)

       # Create a sidebar with a select box to choose the filter
       with col1:
           selected_campaign_name = sidebar_filter(campaign_names_list)
       with col2:
           selected_campaign_type = campaign_type_filter()
       with col3:
           start_date, end_date, choose_analytics, selected_filter_name = filter_for_date_wise(selected_campaign_name)
           if selected_filter_name == "Customize Date":
               with col4:
                   start_date, end_date, choose_analytics = sidebar_date_picker(selected_campaign_name)

       return selected_campaign_name,selected_campaign_type,start_date, end_date, choose_analytics, selected_filter_name
    except Exception as err:
        # Log any errors that occur and print the stack trace for debugging
        log.error(str(err))
        traceback.print_exc()



def metric_graphs_average(
    average_handling_time_dict, average_wait_time_dict, average_wrapup_time_dict, average_call_duration_dict
):
    """
    Displays average metrics in the Streamlit app using HTML and icons.

    Args:
        average_handling_time_dict (dict): Dictionary containing the average handling time.
        average_wait_time_dict (dict): Dictionary containing the average wait time.
        average_wrapup_time_dict (dict): Dictionary containing the average wrapup time.
        average_call_duration_dict (dict): Dictionary containing the average call duration.

    Returns:
        None
    """
    try:
        from datetime import datetime, timedelta
        # Create four columns in the Streamlit app layout
        total1, total2, total3, total4 = st.columns(4)

        # Display average handling time
        with total1:
            average_handling_time = average_handling_time_dict.get('average_handling_time', 'N/A')

            handling_time = datetime.strptime(average_handling_time, "%H:%M:%S") - datetime(1900, 1, 1)

            five_minutes = timedelta(minutes=5)

            if handling_time > five_minutes:
                st.markdown(f"""
                    <div class="sm-grids-red">
                        <p class="sm-grid-title">Average Handling Time</p>
                        <div class="sm-grids-counts-red">
                            <p>{average_handling_time}</p>
                            <i class="fa-solid fa-headphones sm-grid-icon-red"></i>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="sm-grids-green">
                        <p class="sm-grid-title">Average Handling Time</p>
                        <div class="sm-grids-counts-green">
                            <p>{average_handling_time}</p>
                            <i class="fa-solid fa-headphones sm-grid-icon-green"></i>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

        # Display average wait time
        with total2:
            average_wait_time = average_wait_time_dict.get('average_wait_time', 'N/A')
            
            handling_time = datetime.strptime(average_wait_time, "%H:%M:%S") - datetime(1900, 1, 1)

            five_minutes = timedelta(minutes=1)

            if handling_time > five_minutes:
                # Use st.markdown to create HTML content with the icon
                st.markdown(f"""
                    <div class="sm-grids-red">
                        <p class="sm-grid-title">Average Wait Time</p>
                        <div class="sm-grids-counts-red">
                            <p>{average_wait_time}</p>
                            <i class="fa-solid fa-stopwatch sm-grid-icon-red"></i>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                # Use st.markdown to create HTML content with the icon
                st.markdown(f"""
                    <div class="sm-grids-green">
                        <p class="sm-grid-title">Average Wait Time</p>
                        <div class="sm-grids-counts-green">
                            <p>{average_wait_time}</p>
                            <i class="fa-solid fa-stopwatch sm-grid-icon-green"></i>
                        </div>
                    </div>
                """, unsafe_allow_html=True)


        # Display average wrapup time
        with total3:
            average_wrapup_time = average_wrapup_time_dict.get('average_wrapup_time', 'N/A')

            handling_time = datetime.strptime(average_wrapup_time, "%H:%M:%S") - datetime(1900, 1, 1)

            five_minutes = timedelta(minutes=5)

            if handling_time > five_minutes:
                # Use st.markdown to create HTML content with the icon
                st.markdown(f"""
                    <div class="sm-grids-red">
                        <p class="sm-grid-title">Average Wrapup Time</p>
                        <div class="sm-grids-counts-red">
                            <p>{average_wrapup_time}</p>
                            <i class="fa-solid fa-clock sm-grid-icon-red"></i>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                    # Use st.markdown to create HTML content with the icon
                st.markdown(f"""
                    <div class="sm-grids-green">
                        <p class="sm-grid-title">Average Wrapup Time</p>
                        <div class="sm-grids-counts-green">
                            <p>{average_wrapup_time}</p>
                            <i class="fa-solid fa-clock sm-grid-icon-green"></i>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

        # Display average call duration
        with total4:
            average_call_duration = average_call_duration_dict.get('average_call_duration', 'N/A')

            handling_time = datetime.strptime(average_call_duration, "%H:%M:%S") - datetime(1900, 1, 1)

            five_minutes = timedelta(minutes=5)

            if handling_time > five_minutes:
                # Use st.markdown to create HTML content with the icon
                st.markdown(f"""
                    <div class="sm-grids-red">
                        <p class="sm-grid-title">Average Call Duration</p>
                        <div class="sm-grids-counts-red">
                            <p>{average_call_duration}</p>
                            <i class="fa-solid fa-phone sm-grid-icon-red"></i>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                # Use st.markdown to create HTML content with the icon
                st.markdown(f"""
                    <div class="sm-grids-green">
                        <p class="sm-grid-title">Average Call Duration</p>
                        <div class="sm-grids-counts-green">
                            <p>{average_call_duration}</p>
                            <i class="fa-solid fa-phone sm-grid-icon-green"></i>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
    except Exception as err:
        # Log any errors that occur and print the stack trace for debugging
        log.error(str(err))
        traceback.print_exc()


def metric_graphs_rate_call(
    abandon_rate_dict, call_back_Scheduled_dict, total_answered_call_dict, average_queue_time_dict, agent_ideal_time_dict, selected_filter_name
):
    """
    Displays call-related metrics in the Streamlit app using HTML and icons.

    Args:
        abandon_rate_dict (dict): Dictionary containing the abandon rate.
        call_back_Scheduled_dict (dict): Dictionary containing the count of scheduled callbacks.
        total_answered_call_dict (dict): Dictionary containing the total number of answered calls.
        average_queue_time_dict (dict): Dictionary containing the average queue time.
        agent_ideal_time_dict (dict): Dictionary containing the ideal time for agents.
        selected_filter_name (str): Filter name to determine the context for display.

    Returns:
        None
    """
    try:
        # Create four columns in the Streamlit app layout
        total1, total2, total3, total4 = st.columns(4)

        # Display abandon rate
        with total1:
            abandon_rate = abandon_rate_dict.get('abandon_rate', 'N/A')
            if abandon_rate > 10:
                # Use st.markdown to create HTML content with the icon
                st.markdown(f"""
                    <div class="sm-grids-red">
                        <p class="sm-grid-title">Abandon Rate</p>
                        <div class="sm-grids-counts-red">
                            <p>{abandon_rate} %</p>
                            <i class="fa-solid fa-phone-slash sm-grid-icon-red"></i>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                # Use st.markdown to create HTML content with the icon
                st.markdown(f"""
                    <div class="sm-grids-green">
                        <p class="sm-grid-title">Abandon Rate</p>
                        <div class="sm-grids-counts-green">
                            <p>{abandon_rate} %</p>
                            <i class="fa-solid fa-phone-slash sm-grid-icon-green"></i>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

        # Display call back scheduled count
        with total2:
            call_back_Scheduled = call_back_Scheduled_dict.get('next_call_time', 'N/A')
            # Use st.markdown to create HTML content with the icon
            st.markdown(f"""
                <div class="sm-grids-org">
                    <p class="sm-grid-title">Call Back Scheduled</p>
                    <div class="sm-grids-counts-org">
                        <p>{call_back_Scheduled}</p>
                        <i class="fa-solid fa-rotate-right sm-grid-icon-org"></i>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # Display either the longest wait time or total answered calls based on the filter
        with total3:
            if selected_filter_name == "Today":
                title = "Longest Wait Time"
                try:
                    tmp_value = agent_ideal_time_dict.get('agent_ideal_time', '00:00:00')
                except:
                    tmp_value = "00:00:00"
            else:
                title = "Total Answered Call"
                tmp_value = total_answered_call_dict.get('total_answered_call', 'N/A')

            # Use st.markdown to create HTML content with the icon
            st.markdown(f"""
                <div class="sm-grids-voilet">
                    <p class="sm-grid-title">{title}</p>
                    <div class="sm-grids-counts-voilet">
                        <p>{tmp_value}</p>
                        <i class="fa-solid fa-clock-rotate-left sm-grid-icon-voilet"></i>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # Display average queue time
        with total4:
            average_queue_time = average_queue_time_dict.get('average_queue_time', 'N/A')
            # Use st.markdown to create HTML content with the icon
            st.markdown(f"""
                <div class="sm-grids-teal-green">
                    <p class="sm-grid-title">Average Queue Time (In Sec)</p>
                    <div class="sm-grids-counts-teal-green">
                        <p>{average_queue_time}</p>
                        <i class="fa-solid fa-hourglass-half sm-grid-icon-teal-green"></i>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    except Exception as err:
        # Log any errors that occur and print the stack trace for debugging
        log.error(str(err))
        traceback.print_exc()


def inbound_call_within_after_20_graphs(
    inbound_abandon_within_and_after_20_dict, inbound_answered_within_and_after_20_dict,
    inbound_answered_call_dict, inbound_call_abandon_dict, selected_filter_name,
    total_agent_manual_outbound_df, total_agent_progressive_inbound_df,
    total_agent_predictive_df, outbound_disconnected_within_and_after_20_dict
):
    """
    Displays various inbound call metrics and statistics in the Streamlit app using pie charts.

    Args:
        inbound_abandon_within_and_after_20_dict (dict): Dictionary with abandonment data for calls within and after 20 seconds.
        inbound_answered_within_and_after_20_dict (dict): Dictionary with answered call data for calls within and after 20 seconds.
        inbound_answered_call_dict (dict): Dictionary with the number of answered inbound calls.
        inbound_call_abandon_dict (dict): Dictionary with the number of abandoned inbound calls.
        selected_filter_name (str): Name of the selected filter to determine which data to display.
        total_agent_manual_outbound_df (DataFrame): DataFrame containing data on manual outbound agents.
        total_agent_progressive_inbound_df (DataFrame): DataFrame containing data on progressive inbound agents.
        total_agent_predictive_df (DataFrame): DataFrame containing data on predictive agents.
        outbound_disconnected_within_and_after_20_dict (dict): Dictionary with data on outbound disconnections within and after 20 seconds.

    Returns:
        None
    """
    try:
        # Create three columns for layout
        total1, total2, total3 = st.columns([50, 1, 50])

        # Display pie chart for inbound abandoned calls
        with total1:
            # Extract data for abandoned calls
            inbound_abandon_after_20 = inbound_abandon_within_and_after_20_dict.get('inbound_abandon_after_20', 0)
            inbound_abandon_within_20 = inbound_abandon_within_and_after_20_dict.get('inbound_abandon_within_20', 0)

            # Prepare data for pie chart
            final_value_dict1 = {"value": inbound_abandon_after_20, "name": "Queue time >= 20 Sec"}
            final_value_dict2 = {"value": inbound_abandon_within_20, "name": "Queue time < 20 Sec"}
            final_value_list = [final_value_dict1, final_value_dict2]

            # Define pie chart options
            options = {
                "title": {
                    "text": "Inbound Abandoned Call",
                    "left": "left",
                    "textStyle": {"fontSize": 12}
                },
                'toolbox': {
                    'feature': {
                        'saveAsImage': {'show': 'true'}
                    }
                },
                "tooltip": {"trigger": "item"},
                "legend": {
                    "top": "bottom",
                    "itemHeight": 14,
                    "itemWidth": 10,
                    "align": "auto",
                    "left": "center",
                },
                "dataset": [{"source": final_value_list, "bottom": "25%"}],
                "series": [
                    {
                        "name": 'Call',
                        "type": "pie",
                        "radius": ['40%', '70%'],
                        "label": {
                            "position": "inside",
                            "formatter": "{d}%",
                            "color": "#fff",
                            "fontSize": 10,
                        },
                        "percentPrecision": 0,
                        "emphasis": {
                            "label": {"show": "true"},
                            "itemStyle": {
                                "shadowBlur": 10,
                                "shadowOffsetX": 0,
                                "shadowColor": "rgba(0, 0, 0, 0.5)",
                            },
                        },
                        "color": ['rgb(255,99,71)', '#0a72c2']
                    },
                ],
            }

            # Display the pie chart using st_echarts
            st_echarts(options=options)

        # Display pie chart for inbound answered calls
        with total3:
            # Extract data for answered calls
            inbound_answered_after_20 = inbound_answered_within_and_after_20_dict.get('inbound_answered_after_20', 0)
            inbound_answered_within_20 = inbound_answered_within_and_after_20_dict.get('inbound_answered_within_20', 0)

            # Prepare data for pie chart
            final_value_dict1 = {"value": inbound_answered_after_20, "name": "Queue time >= 20 Sec"}
            final_value_dict2 = {"value": inbound_answered_within_20, "name": "Queue time < 20 Sec"}
            final_value_list = [final_value_dict1, final_value_dict2]

            # Define pie chart options
            options = {
                "title": {
                    "text": "Inbound Answered Call",
                    "left": "left",
                    "textStyle": {"fontSize": 12}
                },
                'toolbox': {
                    'feature': {
                        'saveAsImage': {'show': 'true'}
                    }
                },
                "tooltip": {"trigger": "item"},
                "legend": {
                    "top": "bottom",
                    "itemHeight": 14,
                    "itemWidth": 10,
                    "align": "auto",
                    "left": "center",
                },
                "dataset": [{"source": final_value_list, "bottom": "25%"}],
                "series": [
                    {
                        "name": 'Call',
                        "type": "pie",
                        "radius": ['40%', '70%'],
                        "label": {
                            "position": "inside",
                            "formatter": "{d}%",
                            "color": "#fff",
                            "fontSize": 10,
                        },
                        "percentPrecision": 0,
                        "emphasis": {
                            "label": {"show": "true"},
                            "itemStyle": {
                                "shadowBlur": 10,
                                "shadowOffsetX": 0,
                                "shadowColor": "rgba(0, 0, 0, 0.5)",
                            },
                        },
                        "color": ['rgb(255,99,71)', '#0a72c2']
                    },
                ],
            }

            # Display the pie chart using st_echarts
            st_echarts(options=options)

        # Create a new layout for the next set of metrics
        total1, total2, total3 = st.columns([50, 1, 50])

        # Display pie chart based on selected filter
        with total1:
            if selected_filter_name == "Today":
                # Extract data for total agents based on filter
                total_agent_manual_outbound = total_agent_manual_outbound_df.get('total_agent_manual_outbound', 0)
                total_agent_progressive_inbound = total_agent_progressive_inbound_df.get('total_agent_progressive_inbound', 0)
                total_agent_predictive = total_agent_predictive_df.get('total_agent_predictive', 0)
                total_value = total_agent_manual_outbound + total_agent_progressive_inbound + total_agent_predictive
                title = "Total Agents In Call"
                tmp_name = "Agents"
                # Prepare data for pie chart
                final_value_dict1 = {"value": total_agent_manual_outbound, "name": "Manual"}
                final_value_dict2 = {"value": total_agent_progressive_inbound, "name": "Progressive"}
                final_value_dict3 = {"value": total_agent_predictive, "name": "Predictive"}
                final_value_dict4 = {"value": total_value, "name": "Total Call"}
                final_value_list = [final_value_dict1, final_value_dict2, final_value_dict3,final_value_dict4]

            else:
                # Extract data for inbound calls if filter is not "Today"
                title = "Inbound Call"
                tmp_name = "Call"
                inbound_answered_call = int(inbound_answered_call_dict.get('inbound_answered_call', 0))
                inbound_call_abandon = int(inbound_call_abandon_dict.get('inbound_call_abandon', 0))

                # Prepare data for pie chart
                final_value_dict1 = {"value": inbound_answered_call, "name": "Answered Call"}
                final_value_dict2 = {"value": inbound_call_abandon, "name": "Abandon Call"}
                final_value_list = [final_value_dict1, final_value_dict2]

            # Check if all values are zero
            if all(item['value'] == 0 for item in final_value_list):
                filtered_data = final_value_list  # Keep original if all are zero
            else:
                filtered_data = [item for item in final_value_list if item['value'] != 0]  # Filter out zero values

            # Extract the "Total Call" value
            total_call_value = next((item['value'] for item in final_value_list if item['name'] == 'Total Call'),0)

            # Filter out the "Total Call" entry from the pie chart data
            filtered_data = [item for item in final_value_list if item['name'] != 'Total Call']

            # Define pie chart options
            options = {
                "title": [
                    {
                        "text": f"Total Calls: {total_call_value}",
                        "left": "center",
                        "top": "center",
                        "textStyle": {"fontSize": 12, "fontWeight": "bold"}
                    },
                    {
                        "text": title,  # The second title, e.g., "Call Distribution"
                        "left": "left",  # Position this title on the left
                        "top": "top",    # Position this title at the top
                        "textStyle": {"fontSize": 12}
                    }
                ],
                'toolbox': {
                    'feature': {
                        'saveAsImage': {'show': 'true'}
                    }
                },
                "tooltip": {"trigger": "item"},
                "legend": {
                    "top": "bottom",
                    "itemHeight": 14,
                    "itemWidth": 10,
                    "align": "auto",
                    "left": "center",
                },
                "series": [
                    {
                        "name": tmp_name,
                        "type": "pie",
                        "radius": ['40%', '70%'],
                        "label": {
                            "position": 'inside',
                            "formatter": '{c}',
                            "color": "#fff",
                            "fontSize": 10,
                        },
                        "percentPrecision": 0,
                        "emphasis": {
                            "label": {"show": "true"},
                            "itemStyle": {
                                "shadowBlur": 10,
                                "shadowOffsetX": 0,
                                "shadowColor": "rgba(0, 0, 0, 0.5)",
                            },
                        },
                        "color": ['#0a72c2', 'rgb(255,99,71)', '#00ccff'],
                        "data": filtered_data,  # Use the filtered data without "Total Call"
                    },
                ],
            }

            # Display the pie chart using st_echarts
            st_echarts(options=options)

        # Display pie chart for outbound call success and failure
        with total3:
            # Extract data for outbound call success and failure
            success_percentage = outbound_disconnected_within_and_after_20_dict.get('success_percentage', 0)
            failure_percentage = outbound_disconnected_within_and_after_20_dict.get('failure_percentage', 0)

            # Prepare data for pie chart
            final_value_dict1 = {"value": success_percentage, "name": "Success (Percentage)"}
            final_value_dict2 = {"value": failure_percentage, "name": "Failure (Percentage)"}
            final_value_list = [final_value_dict1, final_value_dict2]

            # Define pie chart options
            options = {
                "title": {
                    "text": "Call Success And Failure",
                    "left": "left",
                    "textStyle": {"fontSize": 12}
                },
                'toolbox': {
                    'feature': {
                        'saveAsImage': {'show': 'true'}
                    }
                },
                "tooltip": {"trigger": "item"},
                "legend": {
                    "top": "bottom",
                    "itemHeight": 14,
                    "itemWidth": 10,
                    "align": "auto",
                    "left": "center",
                },
                "dataset": [{"source": final_value_list, "bottom": "25%"}],
                "series": [
                    {
                        "name": 'Call',
                        "type": "pie",
                        "radius": ['40%', '70%'],
                        "label": {
                            "position": "inside",
                            "formatter": "{d}%",
                            "color": "#fff",
                            "fontSize": 10,
                        },
                        "percentPrecision": 0,
                        "emphasis": {
                            "label": {"show": "true"},
                            "itemStyle": {
                                "shadowBlur": 10,
                                "shadowOffsetX": 0,
                                "shadowColor": "rgba(0, 0, 0, 0.5)",
                            },
                        },
                        "color": ['#0a72c2', 'rgb(255,99,71)']
                    },
                ],
            }

            # Display the pie chart using st_echarts
            st_echarts(options=options)
    except Exception as err:
        # Log any errors that occur and print the stack trace for debugging
        log.error(str(err))
        traceback.print_exc()


def outbound_call_within_after_20_graphs(
    outbound_answered_within_and_after_20_dict,
    outbound_disconnected_within_and_after_20_dict,
    outbound_answered_call_dict,
    outbound_call_busy_dict,
    outbound_call_disconnected_dict,
    outbound_call_no_answered_dict,
    selected_filter_name,
    agent_live_dict,
    selected_campaign_type
):
    """
    Displays various outbound call metrics and statistics in the Streamlit app using pie charts.

    Args:
        outbound_answered_within_and_after_20_dict (dict): Dictionary with outbound answered call data.
        outbound_disconnected_within_and_after_20_dict (dict): Dictionary with outbound disconnected call data.
        outbound_answered_call_dict (dict): Dictionary with the number of answered outbound calls.
        outbound_call_busy_dict (dict): Dictionary with the number of busy outbound calls.
        outbound_call_disconnected_dict (dict): Dictionary with the number of disconnected outbound calls.
        outbound_call_no_answered_dict (dict): Dictionary with the number of no-answer outbound calls.
        selected_filter_name (str): Name of the selected filter to determine which data to display.
        agent_live_dict (dict): Dictionary with the status of agents.
        selected_campaign_type (str): Type of the selected campaign to determine which data to display.

    Returns:
        None
    """
    try:
        # Determine layout based on the filter and campaign type
        if selected_filter_name == "Today":
            total1, total3, total2 = st.columns([50, 1, 50])
        else:
            if selected_campaign_type == "ALL":
                total1, total3, total2 = st.columns([50, 1, 50])
            else:
                total1, total2, total3 = st.columns(3)

        # Display pie chart for outbound answered calls
        with total1:
            # Extract data for outbound answered calls
            outbound_answered_after_20 = outbound_answered_within_and_after_20_dict.get('outbound_answered_after_20', 0)
            outbound_answered_within_20 = outbound_answered_within_and_after_20_dict.get('outbound_answered_within_20', 0)

            # Prepare data for the pie chart
            final_value_dict1 = {"value": outbound_answered_after_20, "name": "Call Duration >= 20 Sec"}
            final_value_dict2 = {"value": outbound_answered_within_20, "name": "Call Duration < 20 Sec"}
            final_value_list = [final_value_dict1, final_value_dict2]

            # Define pie chart options
            options = {
                "title": {
                    "text": "Outbound Answered Call",
                    "left": "left",
                    "textStyle": {"fontSize": 12}
                },
                'toolbox': {
                    'feature': {
                        'saveAsImage': {'show': 'true'}
                    }
                },
                "tooltip": {"trigger": "item"},
                "legend": {
                    "top": "bottom",
                    "itemHeight": 14,
                    "itemWidth": 10,
                    "align": "auto",
                    "left": "center",
                },
                "dataset": [{"source": final_value_list, "bottom": "25%"}],
                "series": [
                    {
                        "name": 'Call',
                        "type": "pie",
                        "radius": ['40%', '70%'],
                        "label": {
                            "position": "inside",
                            "formatter": "{d}%",
                            "color": "#fff",
                            "fontSize": 10,
                        },
                        "percentPrecision": 0,
                        "emphasis": {
                            "label": {"show": "true"},
                            "itemStyle": {
                                "shadowBlur": 10,
                                "shadowOffsetX": 0,
                                "shadowColor": "rgba(0, 0, 0, 0.5)",
                            },
                        },
                        "color": ['rgb(255,99,71)', '#0a72c2']
                    },
                ],
            }

            # Display the pie chart using st_echarts
            st_echarts(options=options)

        # Display pie chart for agent status
        with total2:
            if selected_filter_name == "Today":
                # Prepare data and options for the live agents pie chart
                color_list = ['#00ccff', '#00ff5e', '#FFD301', 'rgb(255,99,71)', '#0a72c2']
                title = "Live Agents"
                tmp_name = "Agents"
                agent_away = int(agent_live_dict.get('agent_away', 0))
                agent_available = int(agent_live_dict.get('agent_available', 0))
                agent_busy = int(agent_live_dict.get('agent_busy', 0))
                agent_after_call_work = int(agent_live_dict.get('agent_after_call_work', 0))
                agent_total = int(agent_live_dict.get('agent_total', 0))

                final_value_dict1 = {"value": agent_away, "name": "Agent Not Ready"}
                final_value_dict2 = {"value": agent_available, "name": "Agent Available"}
                final_value_dict3 = {"value": agent_busy, "name": "Agent Busy"}
                final_value_dict4 = {"value": agent_after_call_work, "name": "Closure"}
                final_value_dict5 = {"value": agent_total, "name": "Total Agents"}
                final_value_list = [final_value_dict1, final_value_dict2, final_value_dict3, final_value_dict4, final_value_dict5]

            else:
                # Prepare data and options for the outbound call pie chart
                color_list = ['#0a72c2', '#FFD301', '#00ccff', 'rgb(255,99,71)']
                title = "Outbound Call"
                tmp_name = "Call"
                outbound_answered_call = int(outbound_answered_call_dict.get('outbound_answered_call', 0))
                outbound_call_busy = int(outbound_call_busy_dict.get('outbound_call_busy', 0))
                outbound_call_disconnected = int(outbound_call_disconnected_dict.get('outbound_call_disconnected', 0))
                outbound_call_no_answered = int(outbound_call_no_answered_dict.get('outbound_call_no_answered', 0))

                final_value_dict1 = {"value": outbound_answered_call, "name": "Answered Call"}
                final_value_dict2 = {"value": outbound_call_busy, "name": "Busy Call"}
                final_value_dict3 = {"value": outbound_call_disconnected, "name": "Disconnected Call"}
                final_value_dict4 = {"value": outbound_call_no_answered, "name": "Not Answered Call"}
                final_value_list = [final_value_dict1, final_value_dict2, final_value_dict3, final_value_dict4]

            # Define pie chart options
            options = {
                "title": {
                    "text": title,
                    "left": "left",
                    "textStyle": {"fontSize": 12}
                },
                'toolbox': {
                    'feature': {
                        'saveAsImage': {'show': 'true'}
                    }
                },
                "tooltip": {"trigger": "item"},
                "legend": {
                    "top": "bottom",
                    "itemHeight": 14,
                    "itemWidth": 10,
                    "align": "auto",
                    "left": "center",
                },
                "series": [
                    {
                        "name": tmp_name,
                        "type": "pie",
                        "radius": ['40%', '70%'],
                        "bottom": "5%",  # Adjust this value to move the chart upwards
                        "label": {
                            "position": 'inside',
                            "formatter": '{c}',
                            "color": "#fff",
                            "fontSize": 10,
                        },
                        "percentPrecision": 0,
                        "emphasis": {
                            "label": {"show": "true"},
                            "itemStyle": {
                                "shadowBlur": 10,
                                "shadowOffsetX": 0,
                                "shadowColor": "rgba(0, 0, 0, 0.5)",
                            },
                        },
                        "color": color_list,
                        "data": final_value_list,
                    },
                ],
            }

            # Display the pie chart using st_echarts
            st_echarts(options=options)

        # Display pie chart for outbound call success and failure if campaign type is "OUTBOUND"
        if selected_campaign_type == "OUTBOUND":
            with total3:
                # Extract data for outbound call success and failure
                success_percentage = outbound_disconnected_within_and_after_20_dict.get('success_percentage', 0)
                failure_percentage = outbound_disconnected_within_and_after_20_dict.get('failure_percentage', 0)

                # Prepare data for the pie chart
                final_value_dict1 = {"value": success_percentage, "name": "Success (Percentage)"}
                final_value_dict2 = {"value": failure_percentage, "name": "Failure (Percentage)"}
                final_value_list = [final_value_dict1, final_value_dict2]

                # Define pie chart options
                options = {
                    "title": {
                        "text": "Call Success And Failure",
                        "left": "left",
                        "textStyle": {"fontSize": 12}
                    },
                    'toolbox': {
                        'feature': {
                            'saveAsImage': {'show': 'true'}
                        }
                    },
                    "tooltip": {"trigger": "item"},
                    "legend": {
                        "top": "bottom",
                        "itemHeight": 14,
                        "itemWidth": 10,
                        "align": "auto",
                        "left": "center",
                    },
                    "dataset": [{"source": final_value_list, "bottom": "25%"}],
                    "series": [
                        {
                            "name": 'Call',
                            "type": "pie",
                            "radius": ['40%', '70%'],
                            "label": {
                                "position": "inside",
                                "formatter": "{d}%",
                                "color": "#fff",
                                "fontSize": 10,
                            },
                            "percentPrecision": 0,
                            "emphasis": {
                                "label": {"show": "true"},
                                "itemStyle": {
                                    "shadowBlur": 10,
                                    "shadowOffsetX": 0,
                                    "shadowColor": "rgba(0, 0, 0, 0.5)",
                                },
                            },
                            "color": ['#0a72c2', 'rgb(255,99,71)']
                        },
                    ],
                }

                # Display the pie chart using st_echarts
                st_echarts(options=options)

    except Exception as err:
        # Log any errors and print the stack trace for debugging
        log.error(str(err))
        traceback.print_exc()


def total_agent_live_and_in_call(
    selected_filter_name,
    agent_live_dict,
    total_agent_manual_outbound_df,
    total_agent_progressive_inbound_df,
    total_agent_predictive_df
):
    """
    Displays live agent status and total agents in call metrics in the Streamlit app using pie charts.

    Args:
        selected_filter_name (str): Name of the selected filter to determine which data to display.
        agent_live_dict (dict): Dictionary with the status of live agents.
        total_agent_manual_outbound_df (pd.DataFrame): DataFrame with total agents in manual outbound calls.
        total_agent_progressive_inbound_df (pd.DataFrame): DataFrame with total agents in progressive inbound calls.
        total_agent_predictive_df (pd.DataFrame): DataFrame with total agents in predictive calls.

    Returns:
        None
    """
    try:
        # Define columns for layout
        col1, col3, col2 = st.columns([50, 1, 50])

        # Display pie chart for live agent status
        with col1:
            if selected_filter_name == "Today":
                color_list = ['#00ccff', '#FFD301', '#00ff5e', 'rgb(255,99,71)', '#0a72c2']
                title = "Live Agents"
                tmp_name = "Agents"

                # Extract and convert agent data from dictionary
                agent_away = int(agent_live_dict.get('agent_away', 0))
                agent_available = int(agent_live_dict.get('agent_available', 0))
                agent_busy = int(agent_live_dict.get('agent_busy', 0))
                agent_after_call_work = int(agent_live_dict.get('agent_after_call_work', 0))
                agent_total = int(agent_live_dict.get('agent_total', 0))

                # Prepare data for the pie chart
                final_value_dict1 = {"value": agent_away, "name": "Agent Not Ready"}
                final_value_dict2 = {"value": agent_available, "name": "Agent Available"}
                final_value_dict3 = {"value": agent_busy, "name": "Agent Busy"}
                final_value_dict4 = {"value": agent_after_call_work, "name": "Closure"}
                final_value_dict5 = {"value": agent_total, "name": "Total Agents"}
                final_value_list = [final_value_dict1, final_value_dict2, final_value_dict3, final_value_dict4, final_value_dict5]

                # Check if all values are zero
                if all(item['value'] == 0 for item in final_value_list):
                    filtered_data = final_value_list  # Keep original if all are zero
                else:
                    filtered_data = [item for item in final_value_list if item['value'] != 0]  # Filter out zero values


                # Define pie chart options with two titles
                options = {
                    "title": [
                        {
                            "text": title,  # The second title, e.g., "Call Distribution"
                            "left": "left",  # Position this title on the left
                            "top": "top",    # Position this title at the top
                            "textStyle": {"fontSize": 12}
                        }
                    ],
                    'toolbox': {
                        'feature': {
                            'saveAsImage': {'show': 'true'}
                        }
                    },
                    "tooltip": {"trigger": "item"},
                    "legend": {
                        "top": "bottom",
                        "itemHeight": 14,
                        "itemWidth": 10,
                        "align": "auto",
                        "left": "center",
                    },
                    "series": [
                        {
                            "name": tmp_name,
                            "type": "pie",
                            "radius": ['40%', '70%'],
                            "label": {
                                "position": 'inside',
                                "formatter": '{c}',
                                "color": "#fff",
                                "fontSize": 10,
                            },
                            "percentPrecision": 0,
                            "emphasis": {
                                "label": {"show": "true"},
                                "itemStyle": {
                                    "shadowBlur": 10,
                                    "shadowOffsetX": 0,
                                    "shadowColor": "rgba(0, 0, 0, 0.5)",
                                },
                            },
                            "color": color_list,
                            "data": filtered_data,
                        },
                    ],
                }

                # Display the pie chart using st_echarts
                st_echarts(options=options)

        # Display pie chart for total agents in call
        with col2:
            if selected_filter_name == "Today":
                # Extract and convert agent data from DataFrames
                total_agent_manual_outbound = int(total_agent_manual_outbound_df.get('total_agent_manual_outbound', 0))
                total_agent_progressive_inbound = int(total_agent_progressive_inbound_df.get('total_agent_progressive_inbound', 0))
                total_agent_predictive = int(total_agent_predictive_df.get('total_agent_predictive', 0))
                total_value = total_agent_predictive + total_agent_progressive_inbound + total_agent_predictive
                title = "Total Agents In Call"
                tmp_name = "Agents"

                # Prepare data for the pie chart
                final_value_dict1 = {"value": total_agent_manual_outbound, "name": "Manual"}
                final_value_dict2 = {"value": total_agent_progressive_inbound, "name": "Progressive"}
                final_value_dict3 = {"value": total_agent_predictive, "name": "Predictive"}
                final_value_dict4 = {"value": total_value, "name": "Total Call"}
                final_value_list = [final_value_dict1, final_value_dict2, final_value_dict3,final_value_dict4]

                # Check if all values are zero
                if all(item['value'] == 0 for item in final_value_list):
                    filtered_data = final_value_list  # Keep original if all are zero
                else:
                    filtered_data = [item for item in final_value_list if item['value'] != 0]  # Filter out zero values

                # Extract the "Total Call" value
                total_call_value = next(item['value'] for item in final_value_list if item['name'] == 'Total Call')

                # Filter out the "Total Call" entry from the pie chart data
                filtered_data = [item for item in final_value_list if item['name'] != 'Total Call']

                # Define pie chart options with two titles
                options = {
                    "title": [
                        {
                            "text": f"Total Calls: {total_call_value}",
                            "left": "center",
                            "top": "center",
                            "textStyle": {"fontSize": 12, "fontWeight": "bold"}
                        },
                        {
                            "text": title,  # The second title, e.g., "Call Distribution"
                            "left": "left",  # Position this title on the left
                            "top": "top",    # Position this title at the top
                            "textStyle": {"fontSize": 12}
                        }
                    ],
                    'toolbox': {
                        'feature': {
                            'saveAsImage': {'show': 'true'}
                        }
                    },
                    "tooltip": {"trigger": "item"},
                    "legend": {
                        "top": "bottom",
                        "itemHeight": 14,
                        "itemWidth": 10,
                        "align": "auto",
                        "left": "center",
                    },
                    "series": [
                        {
                            "name": tmp_name,
                            "type": "pie",
                            "radius": ['40%', '70%'],
                            "label": {
                                "position": 'inside',
                                "formatter": '{c}',
                                "color": "#fff",
                                "fontSize": 10,
                            },
                            "percentPrecision": 0,
                            "emphasis": {
                                "label": {"show": "true"},
                                "itemStyle": {
                                    "shadowBlur": 10,
                                    "shadowOffsetX": 0,
                                    "shadowColor": "rgba(0, 0, 0, 0.5)",
                                },
                            },
                            "color": ['#0a72c2', 'rgb(255,99,71)', '#00ccff'],
                            "data": filtered_data,
                        },
                    ],
                }

                # Display the pie chart using st_echarts
                st_echarts(options=options)
    except Exception as err:
        # Log any errors and print the stack trace for debugging
        traceback.print_exc()
        log.error(str(err))


def only_inbound_and_outbound(
    inbound_abandon_within_and_after_20_dict,
    inbound_answered_within_and_after_20_dict,
    outbound_answered_within_and_after_20_dict,
    outbound_disconnected_within_and_after_20_dict,
    selected_campaign_type
):
    """
    Displays inbound and outbound call metrics in the Streamlit app using pie charts.

    Args:
        inbound_abandon_within_and_after_20_dict (dict): Dictionary with inbound call abandon data.
        inbound_answered_within_and_after_20_dict (dict): Dictionary with inbound call answered data.
        outbound_answered_within_and_after_20_dict (dict): Dictionary with outbound call answered data.
        outbound_disconnected_within_and_after_20_dict (dict): Dictionary with outbound call disconnected data.
        selected_campaign_type (str): Type of campaign, either "INBOUND" or "OUTBOUND".

    Returns:
        None
    """
    try:
        if selected_campaign_type == "INBOUND":
            # Define columns for layout
            col1, col2, col3 = st.columns(3)

            # Inbound Abandoned Calls
            with col1:
                inbound_abandon_after_20 = inbound_abandon_within_and_after_20_dict.get('inbound_abandon_after_20', 0)
                inbound_abandon_within_20 = inbound_abandon_within_and_after_20_dict.get('inbound_abandon_within_20', 0)

                final_value_dict1 = {"value": inbound_abandon_after_20, "name": "Call After 20 Sec"}
                final_value_dict2 = {"value": inbound_abandon_within_20, "name": "Call Within 20 Sec"}
                final_value_list = [final_value_dict1, final_value_dict2]

                # Define options for the pie chart
                options = {
                    "title": {
                        "text": "Inbound Abandoned Call",
                        "left": "left",
                        "textStyle": {"fontSize": 12}
                    },
                    'toolbox': {
                        'feature': {
                            'saveAsImage': {'show': 'true'}
                        }
                    },
                    "tooltip": {"trigger": "item"},
                    "legend": {
                        "top": "bottom",
                        "itemHeight": 14,
                        "itemWidth": 10,
                        "align": "auto",
                        "left": "center",
                    },
                    "dataset": [{"source": final_value_list, "bottom": "25%"}],
                    "series": [
                        {
                            "name": 'Call',
                            "type": "pie",
                            "radius": ['40%', '70%'],
                            "label": {
                                "position": "inside",
                                "formatter": "{d}%",
                                "color": "#fff",
                                "fontSize": 10,
                            },
                            "percentPrecision": 0,
                            "emphasis": {
                                "label": {"show": "true"},
                                "itemStyle": {
                                    "shadowBlur": 10,
                                    "shadowOffsetX": 0,
                                    "shadowColor": "rgba(0, 0, 0, 0.5)",
                                },
                            },
                            "color": ['rgb(255,99,71)', '#0a72c2']
                        },
                    ],
                }

                # Display the pie chart
                st_echarts(options=options)

            # Inbound Answered Calls
            with col2:
                inbound_answered_after_20 = inbound_answered_within_and_after_20_dict.get('inbound_answered_after_20', 0)
                inbound_answered_within_20 = inbound_answered_within_and_after_20_dict.get('inbound_answered_within_20', 0)

                final_value_dict1 = {"value": inbound_answered_after_20, "name": "Call After 20 Sec"}
                final_value_dict2 = {"value": inbound_answered_within_20, "name": "Call Within 20 Sec"}
                final_value_list = [final_value_dict1, final_value_dict2]

                # Define options for the pie chart
                options = {
                    "title": {
                        "text": "Inbound Answered Call",
                        "left": "left",
                        "textStyle": {"fontSize": 12}
                    },
                    'toolbox': {
                        'feature': {
                            'saveAsImage': {'show': 'true'}
                        }
                    },
                    "tooltip": {"trigger": "item"},
                    "legend": {
                        "top": "bottom",
                        "itemHeight": 14,
                        "itemWidth": 10,
                        "align": "auto",
                        "left": "center",
                    },
                    "dataset": [{"source": final_value_list, "bottom": "25%"}],
                    "series": [
                        {
                            "name": 'Call',
                            "type": "pie",
                            "radius": ['40%', '70%'],
                            "label": {
                                "position": "inside",
                                "formatter": "{d}%",
                                "color": "#fff",
                                "fontSize": 10,
                            },
                            "percentPrecision": 0,
                            "emphasis": {
                                "label": {"show": "true"},
                                "itemStyle": {
                                    "shadowBlur": 10,
                                    "shadowOffsetX": 0,
                                    "shadowColor": "rgba(0, 0, 0, 0.5)",
                                },
                            },
                            "color": ['rgb(255,99,71)', '#0a72c2']
                        },
                    ],
                }

                # Display the pie chart
                st_echarts(options=options)

            # Outbound Call Success and Failure
            with col3:
                success_percentage = outbound_disconnected_within_and_after_20_dict.get('success_percentage', 0)
                failure_percentage = outbound_disconnected_within_and_after_20_dict.get('failure_percentage', 0)

                final_value_dict1 = {"value": success_percentage, "name": "Success (Percentage)"}
                final_value_dict2 = {"value": failure_percentage, "name": "Failure (Percentage)"}
                final_value_list = [final_value_dict1, final_value_dict2]

                # Define options for the pie chart
                options = {
                    "title": {
                        "text": "Call Success And Failure",
                        "left": "left",
                        "textStyle": {"fontSize": 12}
                    },
                    'toolbox': {
                        'feature': {
                            'saveAsImage': {'show': 'true'}
                        }
                    },
                    "tooltip": {"trigger": "item"},
                    "legend": {
                        "top": "bottom",
                        "itemHeight": 14,
                        "itemWidth": 10,
                        "align": "auto",
                        "left": "center",
                    },
                    "dataset": [{"source": final_value_list, "bottom": "25%"}],
                    "series": [
                        {
                            "name": 'Call',
                            "type": "pie",
                            "radius": ['40%', '70%'],
                            "label": {
                                "position": "inside",
                                "formatter": "{d}%",
                                "color": "#fff",
                                "fontSize": 10,
                            },
                            "percentPrecision": 0,
                            "emphasis": {
                                "label": {"show": "true"},
                                "itemStyle": {
                                    "shadowBlur": 10,
                                    "shadowOffsetX": 0,
                                    "shadowColor": "rgba(0, 0, 0, 0.5)",
                                },
                            },
                            "color": ['#0a72c2', 'rgb(255,99,71)']
                        },
                    ],
                }

                # Display the pie chart
                st_echarts(options=options)

        elif selected_campaign_type == "OUTBOUND":
            # Define columns for layout
            col1, col3, col2 = st.columns([50, 1, 50])

            # Outbound Answered Calls
            with col1:
                outbound_answered_after_20 = outbound_answered_within_and_after_20_dict.get('outbound_answered_after_20', 0)
                outbound_answered_within_20 = outbound_answered_within_and_after_20_dict.get('outbound_answered_within_20', 0)

                final_value_dict1 = {"value": outbound_answered_after_20, "name": "Call After 20 Sec"}
                final_value_dict2 = {"value": outbound_answered_within_20, "name": "Call Within 20 Sec"}
                final_value_list = [final_value_dict1, final_value_dict2]

                # Define options for the pie chart
                options = {
                    "title": {
                        "text": "Outbound Answered Call",
                        "left": "left",
                        "textStyle": {"fontSize": 12}
                    },
                    'toolbox': {
                        'feature': {
                            'saveAsImage': {'show': 'true'}
                        }
                    },
                    "tooltip": {"trigger": "item"},
                    "legend": {
                        "top": "bottom",
                        "itemHeight": 14,
                        "itemWidth": 10,
                        "align": "auto",
                        "left": "center",
                    },
                    "dataset": [{"source": final_value_list, "bottom": "25%"}],
                    "series": [
                        {
                            "name": 'Call',
                            "type": "pie",
                            "radius": ['40%', '70%'],
                            "label": {
                                "position": "inside",
                                "formatter": "{d}%",
                                "color": "#fff",
                                "fontSize": 10,
                            },
                            "percentPrecision": 0,
                            "emphasis": {
                                "label": {"show": "true"},
                                "itemStyle": {
                                    "shadowBlur": 10,
                                    "shadowOffsetX": 0,
                                    "shadowColor": "rgba(0, 0, 0, 0.5)",
                                },
                            },
                            "color": ['rgb(255,99,71)', '#0a72c2']
                        },
                    ],
                }

                # Display the pie chart
                st_echarts(options=options)

            # Outbound Call Success and Failure
            with col2:
                success_percentage = outbound_disconnected_within_and_after_20_dict.get('success_percentage', 0)
                failure_percentage = outbound_disconnected_within_and_after_20_dict.get('failure_percentage', 0)

                final_value_dict1 = {"value": success_percentage, "name": "Success (Percentage)"}
                final_value_dict2 = {"value": failure_percentage, "name": "Failure (Percentage)"}
                final_value_list = [final_value_dict1, final_value_dict2]

                # Define options for the pie chart
                options = {
                    "title": {
                        "text": "Call Success And Failure",
                        "left": "left",
                        "textStyle": {"fontSize": 12}
                    },
                    'toolbox': {
                        'feature': {
                            'saveAsImage': {'show': 'true'}
                        }
                    },
                    "tooltip": {"trigger": "item"},
                    "legend": {
                        "top": "bottom",
                        "itemHeight": 14,
                        "itemWidth": 10,
                        "align": "auto",
                        "left": "center",
                    },
                    "dataset": [{"source": final_value_list, "bottom": "25%"}],
                    "series": [
                        {
                            "name": 'Call',
                            "type": "pie",
                            "radius": ['40%', '70%'],
                            "label": {
                                "position": "inside",
                                "formatter": "{d}%",
                                "color": "#fff",
                                "fontSize": 10,
                            },
                            "percentPrecision": 0,
                            "emphasis": {
                                "label": {"show": "true"},
                                "itemStyle": {
                                    "shadowBlur": 10,
                                    "shadowOffsetX": 0,
                                    "shadowColor": "rgba(0, 0, 0, 0.5)",
                                },
                            },
                            "color": ['#0a72c2', 'rgb(255,99,71)']
                        },
                    ],
                }

                # Display the pie chart
                st_echarts(options=options)

    except Exception as err:
        # Handle any exceptions
        traceback.print_exc()
        log.error(str(err))




def SLA_and_Call_status_dis_graphs(SLA_dict, call_status_disposition_dict, selected_campaign_type):
    """
    Displays SLA and call status disposition graphs in a Streamlit app.

    Args:
        SLA_dict (dict): Dictionary containing SLA data.
        call_status_disposition_dict (dict): Dictionary containing call status disposition data.
        selected_campaign_type (str): Type of campaign, either "INBOUND", "OUTBOUND", or "ALL".

    Returns:
        None
    """
    try:
        if selected_campaign_type == "ALL" or selected_campaign_type == "INBOUND":
            col1, col3, col2 = st.columns([50, 1, 50])
            with col1:
                SLA = SLA_dict.get('sla', 0)  # Extract SLA value, default to 0 if not found
                options = {
                    "title": {
                        "text": "SLA",
                        "left": "left",
                        "textStyle": {"fontSize": 12}
                    },
                    'toolbox': {
                        'feature': {
                            'saveAsImage': {'show': 'true'}
                        }
                    },
                    "tooltip": {
                        "formatter": 'SLA <br/>SCORE : {c}%'
                    },
                    "series": [
                        {
                            "type": 'gauge',
                            "axisLine": {
                                "lineStyle": {
                                    "width": 30,
                                    "color": [
                                        [0.3, 'rgb(255,99,71)'],  # Color for 0-30%
                                        [0.7, 'rgb(255, 191, 0)'],  # Color for 30-70%
                                        [1, '#00ff5e']  # Color for 70-100%
                                    ]
                                }
                            },
                            "pointer": {
                                "itemStyle": {
                                    "color": 'auto'
                                }
                            },
                            "axisTick": {
                                "distance": -30,
                                "length": 8,
                                "lineStyle": {
                                    "color": '#fff',
                                    "width": 2
                                }
                            },
                            "splitLine": {
                                "distance": -30,
                                "length": 40,
                                "lineStyle": {
                                    "color": '#fff',
                                    "width": 4
                                }
                            },
                            "axisLabel": {
                                "color": 'inherit',
                                "distance": 30,
                                "fontSize": 10
                            },
                            "detail": {
                                "valueAnimation": True,
                                "formatter": '{value}',
                                "color": 'inherit'
                            },
                            "data": [
                                {
                                    "value": SLA,
                                }
                            ]
                        }
                    ]
                }

                # Display the gauge chart using st_echarts
                st_echarts(options=options)

            with col2:
                call_status_disposition_dict = call_status_disposition_dict.get('call_status_disposition', {})

                try:
                    # Extract keys and values
                    keys_list = list(call_status_disposition_dict.keys())
                    values_list = list(call_status_disposition_dict.values())
                except:
                    keys_list = ['DC', 'DNC', 'abandon', 'answered', 'called_party', 'noans']
                    values_list = [0, 0, 0, 0, 0, 0]

                options = {
                    "title": {
                        "text": "Call Status Disposition",
                        "left": "left",
                        "textStyle": {"fontSize": 12}
                    },
                    'toolbox': {
                        'feature': {
                            "magicType": {"show": "true", "type": ['bar', 'line']},
                            "restore": {"show": "true"},
                            'saveAsImage': {'show': 'true'}
                        }
                    },
                    "tooltip": {
                        "trigger": 'axis',
                        "axisPointer": {
                            "type": 'shadow'
                        }
                    },
                    "grid": {
                        "left": '3%',
                        "right": '4%',
                        "bottom": '3%',
                        "containLabel": "true"
                    },
                    "xAxis": [
                        {
                            "type": 'category',
                            "data": keys_list,
                            "axisTick": {
                                "alignWithLabel": "true"
                            },
                            "axisLabel": {
                                "rotate": 45,  # Rotate x-axis labels by 45 degrees
                                "interval": 0,  # Display all labels
                                "margin": 10,  # Adjust margin to avoid overlapping
                                "formatter": "{value}"
                            }
                        }
                    ],
                    "yAxis": [
                        {
                            "type": 'value'
                        }
                    ],
                    "series": [
                        {
                            "name": 'Call',
                            "type": 'bar',
                            "barWidth": '60%',
                            "data": values_list,
                            "color": ['#0a72c2']
                        }
                    ]
                }

                # Display the bar chart using st_echarts
                st_echarts(options=options)

        elif selected_campaign_type == "OUTBOUND":
            col1, col2, col3 = st.columns([1, 70, 1])
            with col2:
                call_status_disposition_dict = call_status_disposition_dict.get('call_status_disposition', {})

                try:
                    # Extract keys and values
                    keys_list = list(call_status_disposition_dict.keys())
                    values_list = list(call_status_disposition_dict.values())
                except:
                    keys_list = ['DC', 'DNC', 'abandon', 'answered', 'called_party', 'noans']
                    values_list = [0, 0, 0, 0, 0, 0]

                options = {
                    "title": {
                        "text": "Call Status Disposition",
                        "left": "left",
                        "textStyle": {"fontSize": 12}
                    },
                    'toolbox': {
                        'feature': {
                            "magicType": {"show": "true", "type": ['bar', 'line']},
                            "restore": {"show": "true"},
                            'saveAsImage': {'show': 'true'}
                        }
                    },
                    "tooltip": {
                        "trigger": 'axis',
                        "axisPointer": {
                            "type": 'shadow'
                        }
                    },
                    "grid": {
                        "left": '3%',
                        "right": '4%',
                        "bottom": '3%',
                        "containLabel": "true"
                    },
                    "xAxis": [
                        {
                            "type": 'category',
                            "data": keys_list,
                            "axisTick": {
                                "alignWithLabel": "true"
                            },
                            "axisLabel": {
                                "rotate": 45,  # Rotate x-axis labels by 45 degrees
                                "interval": 0,  # Display all labels
                                "margin": 10,  # Adjust margin to avoid overlapping
                                "formatter": "{value}"
                            }
                        }
                    ],
                    "yAxis": [
                        {
                            "type": 'value'
                        }
                    ],
                    "series": [
                        {
                            "name": 'Call',
                            "type": 'bar',
                            "barWidth": '60%',
                            "data": values_list,
                            "color": ['#0a72c2']
                        }
                    ]
                }

                # Display the bar chart using st_echarts
                st_echarts(options=options)

    except Exception as err:
        # Log and print the error
        log.error(str(err))
        traceback.print_exc()


def aht_agentwise_top_10_and_aht_call_volume_hourly_graphs(aht_agentwise_dict, aht_and_call_volume_dict):
    """
    Displays two graphs: one showing Average Handling Time (AHT) for agents and call volume,
    and another showing call volume and AHT trends hourly.

    Args:
        aht_agentwise_dict (dict): Dictionary containing agent-wise AHT and call volume data.
        aht_and_call_volume_dict (dict): Dictionary containing hourly AHT and call volume data.

    Returns:
        None
    """
    try:
        # Define columns for layout
        col1, col3, col2 = st.columns([50, 1, 50])

        # Extract agent-wise data
        agent_id_list = aht_agentwise_dict.get('agent_id_list', [0]*10)
        agent_aht_list = aht_agentwise_dict.get('agent_aht_list', [0]*10)
        agent_call_volume = aht_agentwise_dict.get('agent_call_volume', [0]*10)

        # Set default values if lists are empty
        if not agent_id_list and not agent_aht_list and not agent_call_volume:
            agent_id_list = [0]*10
            agent_aht_list = [0]*10
            agent_call_volume = [0]*10

        with col1:
            option = {
                "title": {
                    "text": "AHT (Agent Performance)",
                    "left": "left",
                    "textStyle": {"fontSize": 12}
                },
                "tooltip": {
                    "trigger": 'axis',
                    "axisPointer": {
                        "type": 'cross',
                        "crossStyle": {
                            "color": '#999'
                        }
                    }
                },
                "toolbox": {
                    "feature": {
                        "magicType": {"show": "true", "type": ['bar', 'line']},
                        "restore": {"show": "true"},
                        "saveAsImage": {"show": "true"}
                    }
                },
                "legend": {
                    "bottom": 0,
                    "center": 0,
                    "data": ['AHT', 'Call Volume']
                },
                "xAxis": [
                    {
                        "type": 'category',
                        "data": agent_id_list,
                        "axisPointer": {
                            "type": 'shadow'
                        },
                        "axisLabel": {
                            "rotate": 45,
                            "interval": 0,
                            "margin": 10,
                            "formatter": "{value}"
                        }
                    }
                ],
                "yAxis": [
                    {
                        "type": 'value',
                        "name": 'AHT',
                        "axisLabel": {
                            "formatter": '{value}'
                        }
                    },
                    {
                        "type": 'value',
                        "name": 'Call Volume',
                        "axisLabel": {
                            "formatter": '{value}'
                        }
                    }
                ],
                "series": [
                    {
                        "name": 'AHT',
                        "type": 'bar',
                        "data": agent_aht_list,
                        "color": ['#0a72c2']
                    },
                    {
                        "name": 'Call Volume',
                        "smooth": 0.5,
                        "type": 'line',
                        "yAxisIndex": 1,
                        "data": agent_call_volume,
                        "color": ['rgb(255,99,71)']
                    }
                ]
            }
            st_echarts(options=option)

        # Extract hourly data
        hour_list = aht_and_call_volume_dict.get('hour_list',
                                                  ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10',
                                                   '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21',
                                                   '22', '23'])
        aht_value_list = aht_and_call_volume_dict.get('aht_value_list', [0]*24)
        call_volume_list = aht_and_call_volume_dict.get('call_volue_list', [0]*24)

        # Rearrange hour_list to move '00' to the end
        if '00' in hour_list:
            hour_list.remove('00')
            hour_list.append('00')

        with col2:
            options = {
                "title": {
                    "text": "Call Trend (Call Volume Vs AHT)",
                    "left": "left",
                    "textStyle": {"fontSize": 12}
                },
                "tooltip": {
                    "trigger": "axis"
                },
                "legend": {
                    "bottom": -5,
                    "center": 0,
                    "data": ['AHT (in seconds)', 'Call Volume (in number)']
                },
                "toolbox": {
                    "feature": {
                        "magicType": {"show": "true", "type": ['bar', 'line']},
                        "restore": {"show": "true"},
                        "saveAsImage": {"show": "true"}
                    }
                },
                "grid": {
                    "left": "3%",
                    "right": "4%",
                    "bottom": "3%",
                    "containLabel": "true"
                },
                "xAxis": [
                    {
                        "type": "category",
                        "boundaryGap": "false",
                        "axisLabel": {
                            "rotate": 45,
                            "interval": 0,
                            "margin": 10
                        },
                        "data": hour_list
                    }
                ],
                "yAxis": [{"type": "value"}],
                "series": [
                    {
                        "name": "AHT (in seconds)",
                        "type": "line",
                        "smooth": 0.5,
                        "stack": "Total",
                        "areaStyle": {},
                        "emphasis": {"focus": "series"},
                        "data": aht_value_list,
                        "color": ['#0a72c2']
                    },
                    {
                        "name": "Call Volume (in number)",
                        "type": "line",
                        "smooth": 0.5,
                        "stack": "Total",
                        "areaStyle": {},
                        "emphasis": {"focus": "series"},
                        "data": call_volume_list,
                        "color": ['rgb(255,99,71)']
                    }
                ]
            }
            st_echarts(options=options)
    except Exception as err:
        # Log and print the error
        log.error(str(err))
        traceback.print_exc()


def call_in_queue_and_ivr_graphs(call_in_queue_dict, ivr_performance_report_dict):
    """
    Displays two graphs: one for call queue times and another for IVR performance.

    Args:
        call_in_queue_dict (dict): Dictionary containing call queue data.
        ivr_performance_report_dict (dict): Dictionary containing IVR performance data.

    Returns:
        None
    """
    try:
        # Define columns for layout
        col1, col3, col2 = st.columns([50, 1, 50])

        # Extract call queue data
        phone_no_list = call_in_queue_dict.get('phone_no_list', [0])
        queue_time_list = call_in_queue_dict.get('queue_time_list', [0])

        # Set default values if lists are empty
        if not phone_no_list and not queue_time_list:
            phone_no_list = [0]
            queue_time_list = [0]

        with col1:
            # Configure options for the bar chart
            options = {
                "title": {
                    "text": "Top 5 Queue Calls",
                    "left": "left",
                    "textStyle": {"fontSize": 12}
                },
                'toolbox': {
                    'feature': {
                        "magicType": {"show": "true", "type": ['bar', 'line']},
                        "restore": {"show": "true"},
                        'saveAsImage': {'show': 'true'}
                    }
                },
                "tooltip": {
                    "trigger": 'axis',
                    "axisPointer": {"type": 'shadow'}
                },
                "grid": {
                    "left": '3%',
                    "right": '4%',
                    "bottom": '3%',
                    "containLabel": "true"
                },
                "xAxis": [
                    {
                        "type": 'category',
                        "data": phone_no_list,
                        "axisTick": {"alignWithLabel": "true"},
                        "axisLabel": {
                            "rotate": 45,
                            "interval": 0,
                            "margin": 10,
                            "formatter": "{value}"
                        }
                    }
                ],
                "yAxis": [{"type": 'value'}],
                "series": [
                    {
                        "name": 'Sec',
                        "type": 'bar',
                        "barWidth": '60%',
                        "data": queue_time_list,
                        "color": ['#0a72c2']
                    }
                ]
            }
            # Display the bar chart using st_echarts
            st_echarts(options=options)

        # Extract IVR performance data
        ivr_performance_dict = ivr_performance_report_dict.get('ivrperformance', {})
        exception = int(ivr_performance_dict.get('exception', 0))
        ivr_abandoned = int(ivr_performance_dict.get('ivr_abandoned', 0))
        call_to_agent = int(ivr_performance_dict.get('call_to_agent', 0))

        # Prepare data for the pie chart
        final_list = [
            #{"value": exception, "name": "Exception"}
            #{"value": ivr_abandoned, "name": "IVR Abandoned"},
            {"value": call_to_agent, "name": "Transferred To Campaign"}
        ]

        with col2:
            # Configure options for the pie chart
            options = {
                "title": {
                    "text": "IVR Live Performance",
                    "left": "left",
                    "textStyle": {"fontSize": 12}
                },
                'toolbox': {
                    'feature': {'saveAsImage': {'show': 'true'}}
                },
                "tooltip": {"trigger": "item"},
                "legend": {
                    "bottom": "bottom",
                    "itemHeight": 14,
                    "itemWidth": 10,
                    "align": "auto",
                    "left": "center"
                },
                "dataset": [{"source": final_list, "bottom": "25%"}],
                "series": [
                    {
                        "name": 'Call',
                        "type": "pie",
                        "radius": ['40%', '70%'],
                        "label": {
                            "position": "inside",
                            "formatter": "{d}%",
                            "color": "#fff",
                            "fontSize": 10
                        },
                        "percentPrecision": 0,
                        "emphasis": {
                            "label": {"show": "true"},
                            "itemStyle": {
                                "shadowBlur": 10,
                                "shadowOffsetX": 0,
                                "shadowColor": "rgba(0, 0, 0, 0.5)"
                            }
                        },
                        "color": ['#0a72c2', 'rgb(255,99,71)', '#00ff5e']
                    }
                ]
            }
            # Display the pie chart using st_echarts
            st_echarts(options=options)

    except Exception as err:
        # Log and print the error
        log.error(str(err))
        traceback.print_exc()


class NumpyEncoder(json.JSONEncoder):
    """
    Custom JSON encoder to handle NumPy data types.
    """
    def default(self, obj):
        import numpy as np
        """
        Override the default method to handle NumPy data types.

        Args:
            obj: The object to encode.

        Returns:
            The encoded object, or the default encoding if not handled.
        """
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def create_filter(selected_campaign_name, selected_campaign_type, username, start_date, end_date,selected_filter_name,average_handling_time_dict, average_wait_time_dict, average_wrapup_time_dict, average_call_duration_dict,abandon_rate_dict, call_back_Scheduled_dict, total_answered_call_dict, average_queue_time_dict,inbound_abandon_within_and_after_20_dict, inbound_answered_within_and_after_20_dict, inbound_answered_call_dict,inbound_call_abandon_dict, outbound_answered_within_and_after_20_dict, outbound_disconnected_within_and_after_20_dict,
outbound_answered_call_dict, outbound_call_busy_dict, outbound_call_disconnected_dict, outbound_call_no_answered_dict,SLA_dict, call_status_disposition_dict, aht_agentwise_dict, aht_and_call_volume_dict):
    """
    Creates a filter JSON file containing various metrics related to campaign performance.

    Args:
        selected_campaign_name (str): The name of the selected campaign.
        selected_campaign_type (str): The type of the selected campaign.
        username (str): The username of the person creating the filter.
        start_date (str): The start date of the filter in YYYY-MM-DD format.
        end_date (str): The end date of the filter in YYYY-MM-DD format.
        selected_filter_name (str): The name of the selected filter.
        average_handling_time_dict (dict): Dictionary containing average handling time data.
        average_wait_time_dict (dict): Dictionary containing average wait time data.
        average_wrapup_time_dict (dict): Dictionary containing average wrap-up time data.
        average_call_duration_dict (dict): Dictionary containing average call duration data.
        abandon_rate_dict (dict): Dictionary containing abandon rate data.
        call_back_Scheduled_dict (dict): Dictionary containing scheduled callback data.
        total_answered_call_dict (dict): Dictionary containing total answered call data.
        average_queue_time_dict (dict): Dictionary containing average queue time data.
        inbound_abandon_within_and_after_20_dict (dict): Dictionary containing inbound abandon data within and after 20 seconds.
        inbound_answered_within_and_after_20_dict (dict): Dictionary containing inbound answered data within and after 20 seconds.
        inbound_answered_call_dict (dict): Dictionary containing inbound answered call data.
        inbound_call_abandon_dict (dict): Dictionary containing inbound call abandon data.
        outbound_answered_within_and_after_20_dict (dict): Dictionary containing outbound answered data within and after 20 seconds.
        outbound_disconnected_within_and_after_20_dict (dict): Dictionary containing outbound disconnected data within and after 20 seconds.
        outbound_answered_call_dict (dict): Dictionary containing outbound answered call data.
        outbound_call_busy_dict (dict): Dictionary containing outbound call busy data.
        outbound_call_disconnected_dict (dict): Dictionary containing outbound call disconnected data.
        outbound_call_no_answered_dict (dict): Dictionary containing outbound call not answered data.
        SLA_dict (dict): Dictionary containing SLA data.
        call_status_disposition_dict (dict): Dictionary containing call status disposition data.
        aht_agentwise_dict (dict): Dictionary containing agent-wise AHT data.
        aht_and_call_volume_dict (dict): Dictionary containing AHT and call volume data.

    Returns:
        None
    """
    try:
        from datetime import datetime, timedelta

        # Get the current date
        today = datetime.now().date()

        # Calculate the date for yesterday
        yesterday_date = today - timedelta(days=1)

        # Create directory structure for saving the JSON file
        os.makedirs(filter_path, exist_ok=True)

        # Determine the file path based on whether a custom date filter is selected
        if selected_filter_name != "Customize Date":
            file_path = os.path.join(filter_path, selected_campaign_name, selected_filter_name, selected_campaign_type, f"{today}.json")
        else:
            # Create a directory for the date range if "Customize Date" is selected
            date_range_dir = f"{start_date}_{end_date}"
            file_path = os.path.join(filter_path, selected_campaign_name, selected_filter_name, selected_campaign_type, date_range_dir, f"{today}.json")
        
        # Path to the CSV file containing raw data
        tmp_path_csv = os.path.join(download_csv_row_data, selected_campaign_name, f"{yesterday_date}.csv")

        # Check if the CSV file exists
        if os.path.exists(tmp_path_csv):
            # Create the directory for the JSON file if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Check if the JSON file already exists
            if not os.path.exists(file_path):
                # Create a list of all the dictionaries to be included in the JSON file
                tmp_list = [
                    average_handling_time_dict, average_wait_time_dict, average_wrapup_time_dict, average_call_duration_dict,
                    abandon_rate_dict, call_back_Scheduled_dict, total_answered_call_dict, average_queue_time_dict,
                    inbound_abandon_within_and_after_20_dict, inbound_answered_within_and_after_20_dict, inbound_answered_call_dict,
                    inbound_call_abandon_dict, outbound_answered_within_and_after_20_dict, outbound_disconnected_within_and_after_20_dict,
                    outbound_answered_call_dict, outbound_call_busy_dict, outbound_call_disconnected_dict, outbound_call_no_answered_dict,
                    SLA_dict, call_status_disposition_dict, aht_agentwise_dict, aht_and_call_volume_dict
                ]

                # Convert the list of dictionaries to JSON using the custom encoder
                json_data = json.dumps(tmp_list, cls=NumpyEncoder, indent=4)

                # Write the JSON data to the file
                with open(file_path, 'w') as json_file:
                    json_file.write(json_data)
    except Exception as err:
        # Print stack trace and log the error if an exception occurs
        traceback.print_exc()
        log.error(str(err))


# ---- HIDE STREAMLIT STYLE ----
hide_st_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
        """
st.markdown(hide_st_style, unsafe_allow_html=True)


def main():
    # Read and apply custom CSS style
    style = read_style()  # Read the CSS style from a custom function
    st.markdown(f"<style>{style}</style>", unsafe_allow_html=True)  # Apply the custom CSS style to the Streamlit app

    # Access URL parameters and extract relevant data
    campaign_names_list, status, session, username = access_url_parm()  # Retrieve URL parameters, session, and username
    
    if campaign_names_list != None and status != None and session != None and username != None:
        # Check if there are campaign names or if the status is not empty
        if len(campaign_names_list) != 0 or status != "":
            # Proceed if the status is "SUCCESS"
            if status == "SUCCESS":
                dashboard_filter = dashboard_list()
                #print(dashboard_filter,"sssssssssssssssddddddddddddddfffffffffffff")

                # Add a link to the admin page
                st.markdown(
                    f"""
                        <a target="_self" type="button" href='{login_url}adminui.php' class="button button2">Admin</a>
                    """,
                    unsafe_allow_html=True,
                )
                
                if dashboard_filter == "telephony_dashboard" or dashboard_filter == None:
                    
                    count = st_autorefresh(interval=dashboard_reload_time, limit=1000000000, key="fizzbuzzcounter")
                    selected_campaign_name,selected_campaign_type,start_date, end_date, choose_analytics, selected_filter_name = select_box(campaign_names_list)
                    
                    # Display the dashboard data and image
                    st.markdown(
                       f"""
                           <div class="msg" id="dashboard_data_msg">
                               {choose_analytics}            
                           </div>
                       """,
                       unsafe_allow_html=True,
                    )

                    # If both start and end dates are specified
                    if len(str(start_date)) != 0 and len(str(end_date)) != 0:
                        # If the filter is "Today", auto-refresh the dashboard
                        if selected_filter_name == "Today":
                            with st.spinner('Please wait...'):
                                data = send_post_request(selected_campaign_name, start_date, end_date, selected_filter_name, selected_campaign_type)

                                average_handling_time_dict = data[0]
                                average_wait_time_dict = data[1]
                                average_wrapup_time_dict = data[2]
                                average_call_duration_dict = data[3]
                                abandon_rate_dict = data[4]
                                total_answered_call_dict = data[5]
                                call_back_Scheduled_dict = data[6]
                                agent_ideal_time_dict = data[7]
                                average_queue_time_dict = data[8]
                                inbound_abandon_within_and_after_20_dict = data[9]
                                inbound_answered_within_and_after_20_dict = data[10]
                                total_agent_manual_outbound_df = data[11]
                                total_agent_progressive_inbound_df = data[12]
                                total_agent_predictive_df = data[13]
                                outbound_answered_within_and_after_20_dict = data[14]
                                outbound_disconnected_within_and_after_20_dict = data[15]
                                agent_live_dict = data[16]
                                call_in_queue_dict = data[17]
                                SLA_dict = data[18]
                                call_status_disposition_dict = data[19]
                                aht_agentwise_dict = data[20]
                                aht_and_call_volume_dict = data[21]
                                ivr_performance_report_dict = data[22]

                            
                            # Display various metric graphs
                            metric_graphs_average(
                                average_handling_time_dict,
                                average_wait_time_dict,
                                average_wrapup_time_dict,
                                average_call_duration_dict
                            )

                            metric_graphs_rate_call(
                                abandon_rate_dict,
                                call_back_Scheduled_dict,
                                total_answered_call_dict,
                                average_queue_time_dict,
                                agent_ideal_time_dict,
                                selected_filter_name
                            )

                            # Prepare data for inbound and outbound call graphs
                            inbound_call_abandon_dict = {"inbound_call_abandon": 0}  # Initialize inbound call abandon data
                            inbound_answered_call_dict = {"inbound_answered_call": 0}  # Initialize inbound answered call data

                            if selected_campaign_type == "ALL":
                                # Display inbound call metrics for all types
                                inbound_call_within_after_20_graphs(
                                    inbound_abandon_within_and_after_20_dict,
                                    inbound_answered_within_and_after_20_dict,
                                    inbound_answered_call_dict,
                                    inbound_call_abandon_dict,
                                    selected_filter_name,
                                    total_agent_manual_outbound_df,
                                    total_agent_progressive_inbound_df,
                                    total_agent_predictive_df,
                                    outbound_disconnected_within_and_after_20_dict
                                )

                                # Initialize outbound call data
                                outbound_answered_call_dict, outbound_call_busy_dict, outbound_call_disconnected_dict, outbound_call_no_answered_dict = 0, 0, 0, 0

                                # Display outbound call metrics for all types
                                outbound_call_within_after_20_graphs(
                                    outbound_answered_within_and_after_20_dict,
                                    outbound_disconnected_within_and_after_20_dict,
                                    outbound_answered_call_dict,
                                    outbound_call_busy_dict,
                                    outbound_call_disconnected_dict,
                                    outbound_call_no_answered_dict,
                                    selected_filter_name,
                                    agent_live_dict,
                                    selected_campaign_type
                                )
                            elif selected_campaign_type in ["INBOUND", "OUTBOUND"]:
                                # Display inbound and/or outbound call metrics based on type
                                only_inbound_and_outbound(
                                    inbound_abandon_within_and_after_20_dict,
                                    inbound_answered_within_and_after_20_dict,
                                    outbound_answered_within_and_after_20_dict,
                                    outbound_disconnected_within_and_after_20_dict,
                                    selected_campaign_type
                                )
                                # Display total agent live and in-call metrics
                                total_agent_live_and_in_call(
                                    selected_filter_name,
                                    agent_live_dict,
                                    total_agent_manual_outbound_df,
                                    total_agent_progressive_inbound_df,
                                    total_agent_predictive_df
                                )

                            # Display SLA and call status disposition graphs
                            SLA_and_Call_status_dis_graphs(SLA_dict, call_status_disposition_dict, selected_campaign_type)

                            # Display AHT agent-wise and AHT call volume hourly graphs
                            aht_agentwise_top_10_and_aht_call_volume_hourly_graphs(aht_agentwise_dict, aht_and_call_volume_dict)

                            # Display call in queue and IVR performance graphs
                            call_in_queue_and_ivr_graphs(call_in_queue_dict, ivr_performance_report_dict)

                        else:
                            from datetime import datetime, timedelta  # Import necessary date and time classes

                            today = datetime.now().date()  # Get today's date
                            if selected_filter_name != "Customize Date":
                                # Construct the file path for the JSON data
                                file_path = os.path.join(filter_path, selected_campaign_name, selected_filter_name, selected_campaign_type, f"{today}.json")
                            else:
                                # Construct the file path for the JSON data with a custom date range
                                date_range_dir = f"{start_date}_{end_date}"
                                file_path = os.path.join(filter_path, selected_campaign_name, selected_filter_name, selected_campaign_type, date_range_dir, f"{today}.json")

                            data = send_post_request(selected_campaign_name, start_date, end_date, selected_filter_name, selected_campaign_type)

                            if not os.path.exists(file_path):
                                # If the JSON file does not exist, retrieve and process data
                                with st.spinner('Please wait...'):
                                    average_handling_time_dict = data[0]
                                    average_wait_time_dict = data[1]
                                    average_wrapup_time_dict = data[2]
                                    average_call_duration_dict = data[3]
                                    abandon_rate_dict = data[4]
                                    call_back_Scheduled_dict = data[5]
                                    total_answered_call_dict = data[6]
                                    average_queue_time_dict = data[7]
                                    inbound_abandon_within_and_after_20_dict = data[8]
                                    inbound_answered_within_and_after_20_dict = data[9]
                                    inbound_answered_call_dict = data[10]
                                    inbound_call_abandon_dict = data[11]
                                    outbound_answered_within_and_after_20_dict = data[12]
                                    outbound_disconnected_within_and_after_20_dict = data[13]
                                    outbound_answered_call_dict = data[14]
                                    outbound_call_busy_dict = data[15]
                                    outbound_call_disconnected_dict = data[16]
                                    outbound_call_no_answered_dict = data[17]
                                    SLA_dict = data[18]
                                    call_status_disposition_dict = data[19]
                                    aht_agentwise_dict = data[20]
                                    aht_and_call_volume_dict = data[21]
                            else:
                                # If the JSON file exists, read data from the file
                                with st.spinner('Please wait...'):
                                    import time
                                    time.sleep(2)  # Wait for 2 seconds
                                    with open(file_path, 'r') as json_file:
                                        data = json.load(json_file)  # Load data from the JSON file

                                    # Unpack data from the JSON file
                                    [
                                        average_handling_time_dict,
                                        average_wait_time_dict,
                                        average_wrapup_time_dict,
                                        average_call_duration_dict,
                                        abandon_rate_dict,
                                        call_back_Scheduled_dict,
                                        total_answered_call_dict,
                                        average_queue_time_dict,
                                        inbound_abandon_within_and_after_20_dict,
                                        inbound_answered_within_and_after_20_dict,
                                        inbound_answered_call_dict,
                                        inbound_call_abandon_dict,
                                        outbound_answered_within_and_after_20_dict,
                                        outbound_disconnected_within_and_after_20_dict,
                                        outbound_answered_call_dict,
                                        outbound_call_busy_dict,
                                        outbound_call_disconnected_dict,
                                        outbound_call_no_answered_dict,
                                        SLA_dict,
                                        call_status_disposition_dict,
                                        aht_agentwise_dict,
                                        aht_and_call_volume_dict
                                    ] = data

                             
                            # Display metric graphs based on the loaded data
                            metric_graphs_average(
                                average_handling_time_dict,
                                average_wait_time_dict,
                                average_wrapup_time_dict,
                                average_call_duration_dict
                            )

                            # Set agent ideal time data to 0 for daily filters
                            agent_ideal_time_dict = 0

                            metric_graphs_rate_call(
                                abandon_rate_dict,
                                call_back_Scheduled_dict,
                                total_answered_call_dict,
                                average_queue_time_dict,
                                agent_ideal_time_dict,
                                selected_filter_name
                            )

                            # Set total agent data to 0 for daily filters
                            total_agent_manual_outbound_df, total_agent_progressive_inbound_df, total_agent_predictive_df = 0, 0, 0

                            if selected_campaign_type == "ALL":
                                # Display inbound call metrics for all types
                                inbound_call_within_after_20_graphs(
                                    inbound_abandon_within_and_after_20_dict,
                                    inbound_answered_within_and_after_20_dict,
                                    inbound_answered_call_dict,
                                    inbound_call_abandon_dict,
                                    selected_filter_name,
                                    total_agent_manual_outbound_df,
                                    total_agent_progressive_inbound_df,
                                    total_agent_predictive_df,
                                    outbound_disconnected_within_and_after_20_dict
                                )
                            elif selected_campaign_type == "INBOUND":
                                # Display inbound call metrics only
                                inbound_call_within_after_20_graphs(
                                    inbound_abandon_within_and_after_20_dict,
                                    inbound_answered_within_and_after_20_dict,
                                    inbound_answered_call_dict,
                                    inbound_call_abandon_dict,
                                    selected_filter_name,
                                    total_agent_manual_outbound_df,
                                    total_agent_progressive_inbound_df,
                                    total_agent_predictive_df,
                                    outbound_disconnected_within_and_after_20_dict
                                )

                            # Set agent live data to 0 for daily filters
                            agent_live_dict = 0

                            if selected_campaign_type == "ALL":
                                # Display outbound call metrics for all types
                                outbound_call_within_after_20_graphs(
                                    outbound_answered_within_and_after_20_dict,
                                    outbound_disconnected_within_and_after_20_dict,
                                    outbound_answered_call_dict,
                                    outbound_call_busy_dict,
                                    outbound_call_disconnected_dict,
                                    outbound_call_no_answered_dict,
                                    selected_filter_name,
                                    agent_live_dict,
                                    selected_campaign_type
                                )
                            elif selected_campaign_type == "OUTBOUND":
                                # Display outbound call metrics only
                                outbound_call_within_after_20_graphs(
                                    outbound_answered_within_and_after_20_dict,
                                    outbound_disconnected_within_and_after_20_dict,
                                    outbound_answered_call_dict,
                                    outbound_call_busy_dict,
                                    outbound_call_disconnected_dict,
                                    outbound_call_no_answered_dict,
                                    selected_filter_name,
                                    agent_live_dict,
                                    selected_campaign_type
                                )

                            # Display SLA and call status disposition graphs
                            SLA_and_Call_status_dis_graphs(SLA_dict, call_status_disposition_dict, selected_campaign_type)

                            # Display AHT agent-wise and AHT call volume hourly graphs
                            aht_agentwise_top_10_and_aht_call_volume_hourly_graphs(aht_agentwise_dict, aht_and_call_volume_dict)

                            # Create or update filter data
                            create_filter(
                                selected_campaign_name,
                                selected_campaign_type,
                                username,
                                start_date,
                                end_date,
                                selected_filter_name,
                                average_handling_time_dict,
                                average_wait_time_dict,
                                average_wrapup_time_dict,
                                average_call_duration_dict,
                                abandon_rate_dict,
                                call_back_Scheduled_dict,
                                total_answered_call_dict,
                                average_queue_time_dict,
                                inbound_abandon_within_and_after_20_dict,
                                inbound_answered_within_and_after_20_dict,
                                inbound_answered_call_dict,
                                inbound_call_abandon_dict,
                                outbound_answered_within_and_after_20_dict,
                                outbound_disconnected_within_and_after_20_dict,
                                outbound_answered_call_dict,
                                outbound_call_busy_dict,
                                outbound_call_disconnected_dict,
                                outbound_call_no_answered_dict,
                                SLA_dict,
                                call_status_disposition_dict,
                                aht_agentwise_dict,
                                aht_and_call_volume_dict
                            )
                elif dashboard_filter == "campaign_dashboard":
                    cmp_details_main()
                elif dashboard_filter == "agent_dashboard":
                    agent_details_main()

            else:
                # If the status is not "SUCCESS", show a thank you message and sign-in link
                st.markdown(
                    f"""
                        <div class="container">
                            <p class="pr">Thank you for using C-Zentrix</p>
                            <div class="frt">
                                <p>Please close the browser window for security reasons</p>
                                <p class="cl"><a target="_self" href="{login_url}login.php" target="">Sign in</a></p>
                            </div>
                        </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            # If URL parameters are missing, show an error message
            st.error("Please Check Url..")
    else:
        # If the status is not "SUCCESS", show a thank you message and sign-in link
        st.markdown(
            f"""
                <div class="container">
                    <p class="pr">Thank you for using C-Zentrix</p>
                    <div class="frt">
                        <p>Please close the browser window for security reasons</p>
                        <p class="cl"><a target="_self" href="{login_url}login.php" target="">Sign in</a></p>
                    </div>
                </div>
            """,
            unsafe_allow_html=True,
        )

# Run the main function if this script is executed
if __name__ == "__main__":
    main()



