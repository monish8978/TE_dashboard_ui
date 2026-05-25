from settings import login_url,cmp_api_end_url,camp_api_url,main_log_path
from streamlit_echarts import st_echarts
from streamlit_autorefresh import st_autorefresh
from datetime import timedelta
import streamlit as st
import pandas as pd
import traceback
import threading
import datetime
import requests
import logging
import json
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


def sidebar_filter(campaign_names_list):
    try:
        selected_campaign_name = st.selectbox("Select Campaign Name", campaign_names_list)
        # return campaign name
        return selected_campaign_name
    except Exception as err:
        log.error(str(err))
        traceback.print_exc()


def campaign_type_filter():
    try:
        campaign_type_list = ["ALL","INBOUND","OUTBOUND"]
        
        selected_campaign_type = st.selectbox("Select Campaign Type", campaign_type_list)
        # return campaign name
        return selected_campaign_type
    except Exception as err:
        log.error(str(err))
        traceback.print_exc()


def get_date_range():
    try:
        from datetime import datetime, timedelta

        today = datetime.now() - timedelta(days=0)

        # Get yesterday's date
        yesterday = datetime.now() - timedelta(days=1)

        # Calculate the start date (7 days ago from yesterday)
        seven_day_date = yesterday - timedelta(days=7)

        # Calculate the start date (30 days ago from yesterday)
        thirty_day_date = yesterday - timedelta(days=30)

        # Calculate the start date (3 months ago from yesterday)
        three_months_date = yesterday - timedelta(days=3*30)

        # Calculate the start date (6 months ago from yesterday)
        six_months_date = yesterday - timedelta(days=6*30)

        # Calculate the start date (365 days ago from yesterday)
        year_date = yesterday - timedelta(days=365)

        # Create a list containing only the first and last dates
        today_list = [today.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')]

        # Create a list containing only the first and last dates
        yesterday_list = [yesterday.strftime('%Y-%m-%d'), yesterday.strftime('%Y-%m-%d')]

        # Create a list containing only the first and last dates
        seven_day_list = [seven_day_date.strftime('%Y-%m-%d'), yesterday.strftime('%Y-%m-%d')]

        # Create a list containing only the first and last dates
        thirty_day_list = [thirty_day_date.strftime('%Y-%m-%d'), yesterday.strftime('%Y-%m-%d')]

        # Create a list containing only the first and last dates
        three_months_list = [three_months_date.strftime('%Y-%m-%d'), yesterday.strftime('%Y-%m-%d')]

        # Create a list containing only the first and last dates
        six_months_list = [six_months_date.strftime('%Y-%m-%d'), yesterday.strftime('%Y-%m-%d')]

        # Create a list containing only the first and last dates
        year_date_list = [year_date.strftime('%Y-%m-%d'), yesterday.strftime('%Y-%m-%d')]

        date_range_dict = {"Today":today_list,"Yesterday":yesterday_list,"Last 7 Days":seven_day_list,"Last Thirty Days":thirty_day_list,"Last 3 Months":three_months_list,"Last 6 Months":six_months_list,"Last Year":year_date_list}

        return date_range_dict

    except Exception as err:
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
        filter_list = ["Yesterday", "Last 7 Days", "Last Thirty Days", "Last 3 Months", "Last 6 Months", "Last Year", "Customize Date"]

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


def sidebar_date_picker(selected_campaign_name):
    try:
        from datetime import timedelta
        today = datetime.datetime.now()
        # start date default
        default_start_date_yesterday = today - timedelta(days=365)
        # end date default
        default_end_date_yesterday = today - timedelta(days=1)
        # with st.sidebar:
        d = st.date_input(
            "Select Date Range",
            (default_start_date_yesterday,default_end_date_yesterday),
        )
        start_date = ""
        end_date = ""
        if len(d) == 2:
            start_date = d[0]
            end_date = d[1]

        if len(str(start_date)) != 0 and len(str(end_date)) != 0:
            choose_analytics = choose_analytics = "<p>" + "" + selected_campaign_name + " From " + str(start_date) + " to " + str(end_date) + "." + "</p>"
            choose_analytics = ""
        else:
            choose_analytics = "<p>" + "Please Select Both date Start and End...." + "</p>"

        # return start date and end date
        return start_date, end_date,choose_analytics
    except Exception as err:
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
        response = requests.post(cmp_api_end_url, headers=headers, data=json.dumps(data))

        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            data = data["data"]
        else:
            data = [[{'campaign_name': 'Asian_POC', 'count': 0}], [{'campaign_type': 'INBOUND', 'count': 0}], [{'campaign_type': 'OUTBOUND', 'count': 0}], [{'dialer_type': 'AUTO DIAL', 'count': 0}], [{'dialer_type': 'PREVIEW', 'count': 0}], [{'dialer_type': 'PROGRESSIVE', 'count': 0}], [{'circle': 'UP(East)', 'count': 0}], [{'call_status_disposition': 'answered', 'call_duration': 0, 'circle': 'UP(East)', 'hour': 00, 'datetime_combined': '2025-06-30 15:00:00'}], [{'circle': 'Reliance Jio', 'operator': 'Reliance Jio'}], [{'circle': 'Reliance Jio', 'operator': 'Reliance Jio'}], [{'call_status_disposition': 'answered', 'call_duration': 0, 'operator': 'Reliance Jio', 'hour': 0}], [{'call_status_disposition': 'answered', 'operator': 'Reliance Jio'}], [{'call_status_disposition': 'answered', 'count': 0}], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [{'value': 0, 'name': '00'}, {'value': 0, 'name': '01'}, {'value': 0, 'name': '02'}, {'value': 0, 'name': '03'}, {'value': 0, 'name': '04'}, {'value': 0, 'name': '05'}, {'value': 0, 'name': '06'}, {'value': 0, 'name': '07'}, {'value': 0, 'name': '08'}, {'value': 0, 'name': '09'}, {'value': 0, 'name': '10'}, {'value': 0, 'name': '11'}, {'value': 0, 'name': '12'}, {'value': 0, 'name': '13'}, {'value': 0, 'name': '14'}, {'value': 0, 'name': '15'}, {'value': 0, 'name': '16'}, {'value': 0, 'name': '17'}, {'value': 0, 'name': '18'}, {'value': 0, 'name': '19'}, {'value': 0, 'name': '20'}, {'value': 0, 'name': '21'}, {'value': 0, 'name': '22'}, {'value': 0, 'name': '23'}], [{'name': 'UP(East)', 'type': 'line', 'smooth': 0.6, 'stack': 'Total', 'areaStyle': {}, 'emphasis': {'focus': 'series'}, 'data': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]}], ['UP(East)']]

        return data


    except Exception as e:
        data = [[{'campaign_name': 'Asian_POC', 'count': 0}], [{'campaign_type': 'INBOUND', 'count': 0}], [{'campaign_type': 'OUTBOUND', 'count': 0}], [{'dialer_type': 'AUTO DIAL', 'count': 0}], [{'dialer_type': 'PREVIEW', 'count': 0}], [{'dialer_type': 'PROGRESSIVE', 'count': 0}], [{'circle': 'UP(East)', 'count': 0}], [{'call_status_disposition': 'answered', 'call_duration': 0, 'circle': 'UP(East)', 'hour': 00, 'datetime_combined': '2025-06-30 15:00:00'}], [{'circle': 'Reliance Jio', 'operator': 'Reliance Jio'}], [{'circle': 'Reliance Jio', 'operator': 'Reliance Jio'}], [{'call_status_disposition': 'answered', 'call_duration': 0, 'operator': 'Reliance Jio', 'hour': 0}], [{'call_status_disposition': 'answered', 'operator': 'Reliance Jio'}], [{'call_status_disposition': 'answered', 'count': 0}], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [{'value': 0, 'name': '00'}, {'value': 0, 'name': '01'}, {'value': 0, 'name': '02'}, {'value': 0, 'name': '03'}, {'value': 0, 'name': '04'}, {'value': 0, 'name': '05'}, {'value': 0, 'name': '06'}, {'value': 0, 'name': '07'}, {'value': 0, 'name': '08'}, {'value': 0, 'name': '09'}, {'value': 0, 'name': '10'}, {'value': 0, 'name': '11'}, {'value': 0, 'name': '12'}, {'value': 0, 'name': '13'}, {'value': 0, 'name': '14'}, {'value': 0, 'name': '15'}, {'value': 0, 'name': '16'}, {'value': 0, 'name': '17'}, {'value': 0, 'name': '18'}, {'value': 0, 'name': '19'}, {'value': 0, 'name': '20'}, {'value': 0, 'name': '21'}, {'value': 0, 'name': '22'}, {'value': 0, 'name': '23'}], [{'name': 'UP(East)', 'type': 'line', 'smooth': 0.6, 'stack': 'Total', 'areaStyle': {}, 'emphasis': {'focus': 'series'}, 'data': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]}], ['UP(East)']]

        return data


def metric_graphs(
    total_call_count_data_set_df,
    total_inbound_call_data_set_df,
    total_outbound_call_data_set_df,
    auto_dial_df,
    preview_df,
    progressive_df,
    selected_campaign_type
):
    try:
        if selected_campaign_type == "ALL":
            total1, total2, total3, total4, total5, total6 = st.columns(6)
        elif selected_campaign_type == "INBOUND":
            total1,total2, total4, total5,total6 = st.columns(5)
        elif selected_campaign_type == "OUTBOUND":
            total1,total3, total4, total5,total6 = st.columns(5)

        with total1:
            if not total_call_count_data_set_df.empty:
                total_count = total_call_count_data_set_df["count"].iloc[0]
            else:
                total_count = 0
            # Use st.markdown to create HTML content with the icon
            st.markdown(f"""
                        <div class="sm-grids">
                            <p class="sm-grid-title">Total Calls</p>
                            <div class="sm-grids-counts">
                                <p>
                                    {total_count:,.0f}
                                </p>
                                <i class="fa-solid fa-phone sm-grid-icon"></i>
                            </div>
                        </div>

            """, unsafe_allow_html=True)

        if selected_campaign_type == "INBOUND" or selected_campaign_type == "ALL":
            with total2:
                if not total_inbound_call_data_set_df.empty:
                    inbound_values = total_inbound_call_data_set_df["count"].iloc[0]
                else:
                    inbound_values = 0
                # Use st.markdown to create HTML content with the icon
                st.markdown(f"""
                            <div class="sm-grids-green">
                                <p class="sm-grid-title">Total Inbound Calls</p>
                                <div class="sm-grids-counts-green">
                                    <p>
                                        {inbound_values:,.0f}
                                    </p>
                                    <i class="fa-solid fa-arrow-down sm-grid-icon-green"></i>
                                </div>
                            </div>

                """, unsafe_allow_html=True)

        if selected_campaign_type == "OUTBOUND" or selected_campaign_type == "ALL":
            with total3:
                if not total_outbound_call_data_set_df.empty:
                    outbound_values = total_outbound_call_data_set_df["count"].iloc[0]
                else:
                    outbound_values = 0
                # Use st.markdown to create HTML content with the icon
                st.markdown(f"""
                        <div class="sm-grids-red">
                            <p class="sm-grid-title">Total Outbound Calls</p>
                            <div class="sm-grids-counts-red">
                                <p>
                                    {outbound_values:,.0f}
                                </p>
                                <i class="fa-solid fa-arrow-up sm-grid-icon-red"></i>
                            </div>
                        </div>

                """, unsafe_allow_html=True)

        with total4:
            if not auto_dial_df.empty:
                auto_dial_values = auto_dial_df["count"].iloc[0]
            else:
                auto_dial_values = 0
             # Use st.markdown to create HTML content with the icon
            st.markdown(f"""
                        <div class="sm-grids-org">
                            <p class="sm-grid-title">Total Auto Dial Calls</p>
                            <div class="sm-grids-counts-org">
                                <p>
                                    {auto_dial_values:,.0f}
                                </p>
                                <i class="fa-solid fa-tty sm-grid-icon-org"></i>
                            </div>
                        </div>

            """, unsafe_allow_html=True)

        with total5:
            if not preview_df.empty:
                pre_call = preview_df["count"].iloc[0]
            else:
                pre_call = 0
             # Use st.markdown to create HTML content with the icon
            st.markdown(f"""
                        <div class="sm-grids-voilet">
                            <p class="sm-grid-title">Total Preview Calls</p>
                            <div class="sm-grids-counts-voilet">
                                <p>
                                    {pre_call:,.0f}
                                </p>
                                <i class="fa-solid fa-eye sm-grid-icon-voilet"></i>
                            </div>
                        </div>

            """, unsafe_allow_html=True)

        with total6:
            if not progressive_df.empty:
                pro_call = progressive_df["count"].iloc[0]
            else:
                pro_call = 0
             # Use st.markdown to create HTML content with the icon
            st.markdown(f"""
                        <div class="sm-grids-teal-green">
                            <p class="sm-grid-title">Total Progressive Calls</p>
                            <div class="sm-grids-counts-teal-green">
                                <p>
                                    {pro_call:,.0f}
                                </p>
                                <i class="fa-solid fa-phone-volume sm-grid-icon-teal-green"></i>
                            </div>
                        </div>

            """, unsafe_allow_html=True)

    except Exception as err:
        log.error(str(err))
        traceback.print_exc()

def region_call_and_success_failure_graphs(
    success_failure_region_wise_data_set_df,
):
    try:
        df = success_failure_region_wise_data_set_df
        oper_df_ans = df.loc[
            (df["call_status_disposition"] == "answered") & (df["call_duration"] > 5)
        ]

        df_test = oper_df_ans.groupby(['call_status_disposition','circle'])["circle"].size().reset_index(name='call_count')

        oper_df_exc = df.loc[df["call_status_disposition"] != "answered"]

        df_oper_df_exc = oper_df_exc.groupby(['circle'])["circle"].size().reset_index(name='call_count')

        tmp_list = []
        for i,row in df_test.iterrows():
            number_of_call_ans = row['call_count']
            circle_name = row['circle']

            oper_df_exc = df_oper_df_exc[df_oper_df_exc['circle'] == circle_name]

            number_of_call_uns = oper_df_exc["circle"].count()

            success_percentage = (
                number_of_call_ans / (number_of_call_ans + number_of_call_uns)
            ) * 100

            success_percentage = round(success_percentage,2)

            failure_percentage = (
                number_of_call_uns / (number_of_call_ans + number_of_call_uns)
            ) * 100

            failure_percentage = round(failure_percentage,2)

            data = {"circle":circle_name,"Success": success_percentage, "Failure": failure_percentage,"call_count":number_of_call_ans}
            tmp_list.append(data)

        merged_df_main = pd.DataFrame(tmp_list)

        if not merged_df_main.empty:
            circle_list = merged_df_main['circle'].tolist()
            success_list = merged_df_main['Success'].tolist()
            failure_list = merged_df_main['Failure'].tolist()
            call_count_list = merged_df_main['call_count'].tolist()
        else:
            circle_list = []
            success_list = []
            failure_list = []
            call_count_list = []

        col1, col2,col3 = st.columns([50, 50,1])

        with col1:
            option = {
                "title": {
                    "text": "Region Wise Success",
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
                        "magicType": { "show": "true", "type": ['bar','line'] },
                        "restore": { "show": "true" },
                        "saveAsImage": { "show": "true" }
                    }
                },
                "legend": {
                    # "bottom": 0,
                    # "center": 0,
                    "data": ['Success','Call Volume']
                },
                "xAxis": [
                    {
                    "type": 'category',
                    "data": circle_list,
                    "axisPointer": {
                        "type": 'shadow'
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
                    "type": 'value',
                    "name": 'Success',
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
                    "name": 'Success',
                    "type": 'bar',
                    "data": success_list,
                    "color": ['#0a72c2']
                    },
                    {
                    "name": 'Call Volume',
                    "smooth": 0.5,
                    "type": 'line',
                    "yAxisIndex": 1,
                    "data": call_count_list,
                    "color": ['rgb(255,99,71)'],
                    }
                ]
            }
            st_echarts(options=option)




        oper_df_ans = df.loc[
            (df["call_status_disposition"] == "answered") & (df["call_duration"] > 5)
        ]

        df_test = oper_df_ans.groupby(['call_status_disposition','hour'])["hour"].size().reset_index(name='call_count')

        oper_df_exc = df.loc[(df["call_status_disposition"] != "answered")]

        df_oper_df_exc = oper_df_exc.groupby(['hour','call_status_disposition'])["hour"].size().reset_index(name='call_count')

        tmp_list = []
        for i,row in df_test.iterrows():
            number_of_call_ans = row['call_count']
            tmp_hour = row['hour']

            oper_df_exc = df_oper_df_exc[(df_oper_df_exc['hour'] == tmp_hour)]

            number_of_call_uns = oper_df_exc["hour"].count()

            tmp_call_count_list = number_of_call_ans + number_of_call_uns

            success_percentage = (
                number_of_call_ans / (number_of_call_ans + number_of_call_uns)
            ) * 100

            success_percentage = round(success_percentage,2)

            failure_percentage = (
                number_of_call_uns / (number_of_call_ans + number_of_call_uns)
            ) * 100

            failure_percentage = round(failure_percentage,2)


            data = {"Success": success_percentage, "Failure": failure_percentage,"call_count":tmp_call_count_list,"hour":tmp_hour}
            tmp_list.append(data)

        merged_df_main = pd.DataFrame(tmp_list)

        if not merged_df_main.empty:
            success_list = merged_df_main['Success'].tolist()
            failure_list = merged_df_main['Failure'].tolist()
            call_count_list = merged_df_main['call_count'].tolist()
            hour = merged_df_main['hour'].tolist()
        else:
            success_list = []
            failure_list = []
            call_count_list = []
            hour = []

        with col2:
            option = {
                "title": {
                    "text": "Hour Wise Success",
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
                        "magicType": { "show": "true", "type": ['bar','line'] },
                        "restore": { "show": "true" },
                        "saveAsImage": { "show": "true" }
                    }
                },
                "legend": {
                    # "bottom": 0,
                    # "center": 0,
                    "data": ['Success','Call Volume']
                },
                "xAxis": [
                    {
                    "type": 'category',
                    "data": hour,
                    "axisPointer": {
                        "type": 'shadow'
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
                    "type": 'value',
                    "name": 'Success',
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
                    "name": 'Success',
                    "type": 'bar',
                    "data": success_list,
                    "color": ['#0a72c2']
                    },
                    {
                    "name": 'Call Volume',
                    "smooth": 0.5,
                    "type": 'line',
                    "yAxisIndex": 1,
                    "data": call_count_list,
                    "color": ['rgb(255,99,71)'],
                    }
                ]
            }
            st_echarts(options=option)


    except Exception as err:
        log.error(str(err))
        traceback.print_exc()


def operator_call_count_hourly_graphs(
    airtel_operator,
    other_operator,
    Reliance_operator,
    BSNL_MTNL_operator,
    Vodafone_operator,
):
    try:
        col1, col2,col3 = st.columns([70, 1,1])
        with col1:
            options = {
                "title": {
                    "color": ["red", "green", "blue", "yellow", "orange"],
                    "text": "Hourly Operator Call Count",
                    "left": "left",
                    "textStyle": {"fontSize": 12}
                },
                "tooltip": {
                    "trigger": "axis",
                    "axisPointer": {
                        "type": "cross",
                        "label": {"backgroundColor": "#6a7985"},
                    },
                },
                "legend": {
                    "left": "right",
                    "data": [
                        "Airtel",
                        "Others",
                        "Reliance Jio",
                        "BSNL/MTNL",
                        "Vodafone Idea",
                    ],
                },
                "grid": {
                    "left": "3%",
                    "right": "4%",
                    "bottom": "3%",
                    "containLabel": "true",
                },
                "xAxis": {
                    "type": "category",
                    "boundaryGap": "false",
                    "data": [
                        "00",
                        "01",
                        "02",
                        "03",
                        "04",
                        "05",
                        "06",
                        "07",
                        "08",
                        "09",
                        "10",
                        "11",
                        "12",
                        "13",
                        "14",
                        "15",
                        "16",
                        "17",
                        "18",
                        "19",
                        "20",
                        "21",
                        "22",
                        "23",
                    ],
                },
                "yAxis": {"type": "value"},
                "series": [
                    {
                        "name": "Airtel",
                        "type": "line",
                        "smooth": 0.6,
                        "stack": "Total",
                        "areaStyle": {},
                            "emphasis": {
                                "focus": 'series'
                        },
                        "data": airtel_operator,
                        "color": "#FFD301"
                    },
                    {
                        "name": "Others",
                        "type": "line",
                        "smooth": 0.6,
                        "stack": "Total",
                        "areaStyle": {},
                            "emphasis": {
                                "focus": 'series'
                        },
                        "data": other_operator,
                        "color": "#00ccff"
                    },
                    {
                        "name": "Reliance Jio",
                        "type": "line",
                        "smooth": 0.6,
                        "stack": "Total",
                        "areaStyle": {},
                            "emphasis": {
                                "focus": 'series'
                        },
                        "data": Reliance_operator,
                        "color": "#00ff5e"
                    },
                    {
                        "name": "BSNL/MTNL",
                        "type": "line",
                        "smooth": 0.6,
                        "stack": "Total",
                        "areaStyle": {},
                            "emphasis": {
                                "focus": 'series'
                        },
                        "data": BSNL_MTNL_operator,
                        "color": "rgb(255,99,71)"
                    },
                    {
                        "name": "Vodafone Idea",
                        "type": "line",
                        "smooth": 0.6,
                        "stack": "Total",
                        "areaStyle": {},
                            "emphasis": {
                                "focus": 'series'
                        },
                        "data": Vodafone_operator,
                        "color": "#0a72c2"
                    },
                ],
            }
            st_echarts(options=options)
    except Exception as err:
        log.error(str(err))
        traceback.print_exc()


def region_call_count_hourly_graphs(
    region_call_count_hour_data_set_df,state_list
):
    try:
        col1, col2,col3 = st.columns([70, 1,1])
        with col1:
            options = {
                "title": {
                    # "color": ["red", "green", "blue", "yellow", "orange"],
                    "text": "Hourly Region Call Count",
                    "left": "left",
                    "textStyle": {"fontSize": 12}
                },
                "tooltip": {
                    "trigger": "axis",
                    "axisPointer": {
                        "type": "cross",
                        "label": {"backgroundColor": "#6a7985"},
                    },
                },
                # "legend": {
                #     "left": "right",
                #     "data": state_list,
                # },
                "grid": {
                    "left": "3%",
                    "right": "4%",
                    "bottom": "3%",
                    "containLabel": "true",
                },
                "xAxis": {
                    "type": "category",
                    "boundaryGap": "false",
                    "data": [
                        "00",
                        "01",
                        "02",
                        "03",
                        "04",
                        "05",
                        "06",
                        "07",
                        "08",
                        "09",
                        "10",
                        "11",
                        "12",
                        "13",
                        "14",
                        "15",
                        "16",
                        "17",
                        "18",
                        "19",
                        "20",
                        "21",
                        "22",
                        "23",
                    ],
                },
                "yAxis": {"type": "value"},
                "series": region_call_count_hour_data_set_df
            }
            st_echarts(options=options)
    except Exception as err:
        log.error(str(err))
        traceback.print_exc()


def over_all_call_count_hourly_graphs(over_all_call_count_hourly_data_set_value,over_all_call_status_dis_data_set_df):
    try:
        col1, col2,col3 = st.columns([50, 50,1])
        with col1:
            options = {
                "title": {
                    "text": "Hourly Call Count",
                    "left": "left",
                    "textStyle": {"fontSize": 12}
                },
                "tooltip": {
                    "trigger": "axis",
                },
                "grid": {
                    "left": "3%",
                    "right": "4%",
                    "bottom": "3%",
                    "containLabel": "true",
                },
                "xAxis": [
                    {
                        "type": "category",
                        "boundaryGap": "false",
                        "data": [
                            "00",
                            "01",
                            "02",
                            "03",
                            "04",
                            "05",
                            "06",
                            "07",
                            "08",
                            "09",
                            "10",
                            "11",
                            "12",
                            "13",
                            "14",
                            "15",
                            "16",
                            "17",
                            "18",
                            "19",
                            "20",
                            "21",
                            "22",
                            "23",
                        ],
                    }
                ],
                "yAxis": [{"type": "value"}],
                "series": [
                    {
                        "name": "Call Count",
                        "type": "line",
                        "smooth": 0.6,
                        "stack": "Total",
                        "areaStyle": {},
                        "emphasis": {"focus": "series"},
                        "data": over_all_call_count_hourly_data_set_value,
                        "color": "#0a72c2",
                    }
                ],
            }
            st_echarts(options=options)

        if over_all_call_status_dis_data_set_df.empty:
            pie_data_list = [{"value":0,"name":"Access From"}]
        else:
            pie_data_list = []
        for i, row in over_all_call_status_dis_data_set_df.iterrows():
            pie_data_dict = {
                "value": row["count"],
                "name": row["call_status_disposition"],
            }
            pie_data_list.append(pie_data_dict)
        with col2:
            color_list = [
                 "rgb(255,99,71)","#0a72c2", "#33FFF2",
                "#FFB533", "#8D33FF", "#FF33E3", "#33FFBD", "#FFC733",
                "#33A6FF","#33FF57"
            ]
            options = {
                "title": {
                    "text": "Call Status Disposition Call Count",
                    "left": "left",
                    "textStyle": {"fontSize": 12}
                },
                "tooltip": {"trigger": "item"},
                "legend": {
                    "top": "bottom",
                    "itemHeight": 14,
                    "itemWidth": 10,
                    "align": "auto",
                    "left": "center"
                },
                "dataset": [{"source": pie_data_list, "bottom": "25%"}],
                "series": [
                    {
                        "type": "pie",
                        "radius": "50%",
                        "color": color_list
                    },
                    {
                        "type": "pie",
                        "radius": "50%",
                        "label": {
                            "position": "inside",
                            "formatter": "{d}%",
                            "color": "black",
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
                    }
                ]
            }
            st_echarts(options=options)

    except Exception as err:
        log.error(str(err))
        traceback.print_exc()

def operator_call_and_success_failure_graphs(
    success_failure_operator_wise_data_set_df,
):
    try:
        df = success_failure_operator_wise_data_set_df
        oper_df_ans = df.loc[
            (df["call_status_disposition"] == "answered") & (df["call_duration"] > 5)
        ]

        df_test = oper_df_ans.groupby(['call_status_disposition','operator'])["operator"].size().reset_index(name='call_count')

        oper_df_exc = df.loc[df["call_status_disposition"] != "answered"]

        df_oper_df_exc = oper_df_exc.groupby(['operator'])["operator"].size().reset_index(name='call_count')

        tmp_list = []
        for i,row in df_test.iterrows():
            number_of_call_ans = row['call_count']
            operator_name = row['operator']

            oper_df_exc = df_oper_df_exc[df_oper_df_exc['operator'] == operator_name]
            number_of_call_uns = oper_df_exc["operator"].count()

            success_percentage = (
                number_of_call_ans / (number_of_call_ans + number_of_call_uns)
            ) * 100

            success_percentage = round(success_percentage,2)

            failure_percentage = (
                number_of_call_uns / (number_of_call_ans + number_of_call_uns)
            ) * 100

            failure_percentage = round(failure_percentage,2)


            data = {"operator":operator_name,"Success": success_percentage, "Failure": failure_percentage,"call_count":number_of_call_ans}
            tmp_list.append(data)

        merged_df_main = pd.DataFrame(tmp_list)

        if not merged_df_main.empty:
            operator_list = merged_df_main['operator'].tolist()
            success_list = merged_df_main['Success'].tolist()
            failure_list = merged_df_main['Failure'].tolist()
            call_count_list = merged_df_main['call_count'].tolist()
        else:
            operator_list = []
            success_list = []
            failure_list = []
            call_count_list = []


        col1, col2, col3 = st.columns([50, 50,1])

        with col1:
            option = {
                "title": {
                    "text": "Operator Wise Success",
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
                        "magicType": { "show": "true", "type": ['bar','line'] },
                        "restore": { "show": "true" },
                        "saveAsImage": { "show": "true" }
                    }
                },
                "legend": {
                    # "bottom": 0,
                    # "center": 0,
                    "data": ['Success','Call Volume']
                },
                "xAxis": [
                    {
                    "type": 'category',
                    "data": operator_list,
                    "axisPointer": {
                        "type": 'shadow'
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
                    "type": 'value',
                    "name": 'Success',
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
                    "name": 'Success',
                    "type": 'bar',
                    "data": success_list,
                    "color": ['#0a72c2']
                    },
                    {
                    "name": 'Call Volume',
                    "smooth": 0.5,
                    "type": 'line',
                    "yAxisIndex": 1,
                    "data": call_count_list,
                    "color": ['rgb(255,99,71)'],
                    }
                ]
            }
            st_echarts(options=option)

        oper_df_ans = df.loc[
            (df["call_status_disposition"] == "answered") & (df["call_duration"] > 5)
        ]

        df_test = oper_df_ans.groupby(['call_status_disposition','hour'])["hour"].size().reset_index(name='call_count')

        oper_df_exc = df.loc[df["call_status_disposition"] != "answered"]

        df_oper_df_exc = oper_df_exc.groupby(['hour'])["hour"].size().reset_index(name='call_count')

        tmp_list = []
        for i,row in df_test.iterrows():
            number_of_call_ans = row['call_count']
            tmp_hour = row['hour']

            oper_df_exc = df_oper_df_exc[df_oper_df_exc['hour'] == tmp_hour]
            number_of_call_uns = oper_df_exc["hour"].count()

            tmp_call_count_list = number_of_call_ans + number_of_call_uns

            success_percentage = (
                number_of_call_ans / (number_of_call_ans + number_of_call_uns)
            ) * 100

            success_percentage = round(success_percentage,2)

            failure_percentage = (
                number_of_call_uns / (number_of_call_ans + number_of_call_uns)
            ) * 100

            failure_percentage = round(failure_percentage,2)


            data = {"hour":tmp_hour,"Success": success_percentage, "Failure": failure_percentage,"call_count":tmp_call_count_list}
            tmp_list.append(data)

        merged_df_main = pd.DataFrame(tmp_list)

        if not merged_df_main.empty:
            success_list = merged_df_main['Success'].tolist()
            failure_list = merged_df_main['Failure'].tolist()
            call_count_list = merged_df_main['call_count'].tolist()
            hour = merged_df_main['hour'].tolist()
        else:
            success_list = []
            failure_list = []
            call_count_list = []
            hour = []

        with col2:
            option = {
                "title": {
                    "text": "Hour Wise Success",
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
                        "magicType": { "show": "true", "type": ['bar','line'] },
                        "restore": { "show": "true" },
                        "saveAsImage": { "show": "true" }
                    }
                },
                "legend": {
                    # "bottom": 0,
                    # "center": 0,
                    "data": ['Success','Call Volume']
                },
                "xAxis": [
                    {
                    "type": 'category',
                    "data": hour,
                    "axisPointer": {
                        "type": 'shadow'
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
                    "type": 'value',
                    "name": 'Success',
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
                    "name": 'Success',
                    "type": 'bar',
                    "data": success_list,
                    "color": ['#0a72c2']
                    },
                    {
                    "name": 'Call Volume',
                    "smooth": 0.5,
                    "type": 'line',
                    "yAxisIndex": 1,
                    "data": call_count_list,
                    "color": ['rgb(255,99,71)'],
                    }
                ]
            }
            st_echarts(options=option)
    except Exception as err:
        log.error(str(err))
        traceback.print_exc()


def main():
    campaign_names_list,status,session,username = access_url_parm()

    if len(campaign_names_list) != 0 or status != "":
        if status == "SUCCESS":
            count = st_autorefresh(interval=86400000, limit=1000000000, key="fizzbuzzcounter")

            selected_campaign_name,selected_campaign_type,start_date, end_date, choose_analytics, selected_filter_name = select_box(campaign_names_list)

            st.markdown(
                f"""
                    <div class="msg" id="dashboard_data_msg">
                        {choose_analytics}
                    </div>
                """,
                unsafe_allow_html=True,
            )

            if len(str(start_date)) != 0 and len(str(end_date)) != 0:

                if selected_filter_name == "Today":
                    pass
                else:
                    final_data_list = send_post_request(selected_campaign_name, start_date, end_date, selected_filter_name, selected_campaign_type)

                    total_call_count_data_set_df = pd.DataFrame(final_data_list[0])
                    total_inbound_call_data_set_df = pd.DataFrame(final_data_list[1])
                    total_outbound_call_data_set_df = pd.DataFrame(final_data_list[2])
                    auto_dial_df = pd.DataFrame(final_data_list[3])
                    preview_df = pd.DataFrame(final_data_list[4])
                    progressive_df = pd.DataFrame(final_data_list[5])
                    success_failure_region_wise_data_set_df = pd.DataFrame(final_data_list[7])
                    success_failure_operator_wise_data_set_df  = pd.DataFrame(final_data_list[10])
                    region_call_count_hour_data_set_df = final_data_list[19]
                    state_list = final_data_list[20]
                    over_all_call_status_dis_data_set_df       = pd.DataFrame(final_data_list[12])
                    airtel_operator = final_data_list[13]
                    other_operator = final_data_list[14]
                    Reliance_operator = final_data_list[15]
                    BSNL_MTNL_operator = final_data_list[16]
                    Vodafone_operator = final_data_list[17]
                    over_all_call_count_hourly_data_set_value = final_data_list[18]

                    metric_graphs(
                        total_call_count_data_set_df,
                        total_inbound_call_data_set_df,
                        total_outbound_call_data_set_df,
                        auto_dial_df,
                        preview_df,
                        progressive_df,
                        selected_campaign_type
                    )

                    rw_op_list = ["Region Wise Data","Operator Wise Data"]
                    rw_ow = st.selectbox("Select Data Region and Operator Wise", rw_op_list)

                    if rw_ow == "Region Wise Data":
                        region_call_and_success_failure_graphs(
                            success_failure_region_wise_data_set_df,
                        )
                        region_call_count_hourly_graphs(region_call_count_hour_data_set_df,state_list)
                    else:
                        operator_call_and_success_failure_graphs(
                            success_failure_operator_wise_data_set_df,
                        )
                        operator_call_count_hourly_graphs(
                            airtel_operator,
                            other_operator,
                            Reliance_operator,
                            BSNL_MTNL_operator,
                            Vodafone_operator,
                        )

                    over_all_call_count_hourly_graphs(
                        over_all_call_count_hourly_data_set_value,
                        over_all_call_status_dis_data_set_df,
                    )

        else:
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
        st.error("Please Check Url..")


if __name__ == "__main__":
    main()


