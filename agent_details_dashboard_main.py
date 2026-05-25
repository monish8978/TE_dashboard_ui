# import config file
from settings import camp_api_url,main_log_path,login_url,agent_api_end_url
from streamlit_autorefresh import st_autorefresh
from streamlit_echarts import st_echarts
import pandas as pd
import streamlit as st
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
        filter_list = ["Yesterday", "Last 7 Days", "Last Thirty Days", "Last 3 Months", "Last 6 Months", "Last Year"]

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
       col1, col2, col3, col4 = st.columns([33.33,33.33,33.33,0.1])

       # Create a sidebar with a select box to choose the filter
       with col1:
           selected_campaign_name = sidebar_filter(campaign_names_list)
       with col2:
           start_date, end_date, choose_analytics, selected_filter_name = filter_for_date_wise(selected_campaign_name)
           if selected_filter_name == "Customize Date":
               with col3:
                   start_date, end_date, choose_analytics = sidebar_date_picker(selected_campaign_name)

       return selected_campaign_name,start_date, end_date, choose_analytics, selected_filter_name
    except Exception as err:
        # Log any errors that occur and print the stack trace for debugging
        log.error(str(err))
        traceback.print_exc()


def send_post_request(selected_campaign_name, start_date, end_date):
    # The payload (data) to be sent in the request body
    data = {
        "selected_campaign_name": selected_campaign_name,
        "start_date": str(start_date),
        "end_date": str(end_date)
    }


    # Headers to specify that we are sending JSON data
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        # Send the POST request
        response = requests.post(agent_api_end_url, headers=headers, data=json.dumps(data))

        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            data = data["data"]
        else:
            data = ['00:00:00', '00:00:00', '00:00:00', '00:00:00', '00:00:00', '00:00:00', '00:00:00', 0, [{'agent_id': 0, 'agent_name': 'Nishant Saxena', 'Productive_Hours': '0 days 00:00:00'}],[{'agent_id': 0, 'agent_name': 'Nishant Saxena', 'Unproductive_Hours': '0 days 00:00:00'}],[{'agent_id': 0, 'agent_name': 'Nishant Saxena', 'call_start_date_time': '0000-00-00 00:00:00', 'Wait_Time': 0}],[{'agent_id': 0, 'agent_name': 'Nishant Saxena', 'Wrapup_Time': 0}],[{'agent_id': 0, 'agent_name': 'Nishant Saxena', 'Call_Duration': 0}],[{'agent_id': 0, 'agent_name': 'Nishant Saxena', 'Talk_Time': 0}],[{'agent_id': 0, 'agent_name': 'Nishant Saxena', 'Queue_Time': 0}],[{'agent_id': 0, 'day_name': '0', 'Score': 0, 'Normalized_Score': 0}],[{'hour': 9, 'Score': 0, 'Normalized_Score': 0}],[{'hour': 9, 'wrapup_time': 0, 'call_duration': 0, 'wait_time': 0, 'hold_time': 0, 'Agent_Talk_Time': 0, 'Agent_Queue_Time': 0}],[{'months': 7, 'wrapup_time': 0, 'call_duration': 0, 'wait_time': 0, 'hold_time': 0, 'Agent_Talk_Time': 0, 'Agent_Queue_Time': 0}],[{'days': 15, 'wrapup_time':0, 'call_duration': 0, 'wait_time': 0, 'hold_time': 0, 'Agent_Talk_Time': 0, 'Agent_Queue_Time': 0}]]
        return data


    except Exception as e:
        data = ['00:00:00', '00:00:00', '00:00:00', '00:00:00', '00:00:00', '00:00:00', '00:00:00', 0, [{'agent_id': 0, 'agent_name': 'Nishant Saxena', 'Productive_Hours': '0 days 00:00:00'}],[{'agent_id': 0, 'agent_name': 'Nishant Saxena', 'Unproductive_Hours': '0 days 00:00:00'}],[{'agent_id': 0, 'agent_name': 'Nishant Saxena', 'call_start_date_time': '0000-00-00 00:00:00', 'Wait_Time': 0}],[{'agent_id': 0, 'agent_name': 'Nishant Saxena', 'Wrapup_Time': 0}],[{'agent_id': 0, 'agent_name': 'Nishant Saxena', 'Call_Duration': 0}],[{'agent_id': 0, 'agent_name': 'Nishant Saxena', 'Talk_Time': 0}],[{'agent_id': 0, 'agent_name': 'Nishant Saxena', 'Queue_Time': 0}],[{'agent_id': 0, 'day_name': '0', 'Score': 0, 'Normalized_Score': 0}],[{'hour': 9, 'Score': 0, 'Normalized_Score': 0}],[{'hour': 9, 'wrapup_time': 0, 'call_duration': 0, 'wait_time': 0, 'hold_time': 0, 'Agent_Talk_Time': 0, 'Agent_Queue_Time': 0}],[{'months': 7, 'wrapup_time': 0, 'call_duration': 0, 'wait_time': 0, 'hold_time': 0, 'Agent_Talk_Time': 0, 'Agent_Queue_Time': 0}],[{'days': 15, 'wrapup_time':0, 'call_duration': 0, 'wait_time': 0, 'hold_time': 0, 'Agent_Talk_Time': 0, 'Agent_Queue_Time': 0}]]
        return data


def avg_metric_graphs_first(
    avg_productive_hour,avg_unproductive_hour,avg_wait_time_sec,avg_wrapup_time_sec
):
    try:
        total1, total2, total3, total4 = st.columns(4)
        with total1:
            # Use st.markdown to create HTML content with the icon
            st.markdown(f"""
                        <div class="sm-grids-green">
                            <p class="sm-grid-title">Average Productive Hours</p>
                            <div class="sm-grids-counts-green">
                                <p>
                                    {avg_productive_hour}
                                </p>
                                <i class="fa-solid fa-hourglass-half sm-grid-icon-green"></i>
                            </div>
                        </div>

            """, unsafe_allow_html=True)

        with total2:
             # Use st.markdown to create HTML content with the icon
            st.markdown(f"""
                        <div class="sm-grids-red">
                            <p class="sm-grid-title">Average UnProductive Hours</p>
                            <div class="sm-grids-counts-red">
                                <p>
                                    {avg_unproductive_hour}
                                </p>
                                <i class="fa-solid fa-hourglass-half sm-grid-icon-red"></i>
                            </div>
                        </div>

            """, unsafe_allow_html=True)

        with total3:
             # Use st.markdown to create HTML content with the icon
            st.markdown(f"""
                        <div class="sm-grids-org">
                            <p class="sm-grid-title">Average Wait Time</p>
                            <div class="sm-grids-counts-org">
                                <p>
                                    {avg_wait_time_sec}
                                </p>
                                <i class="fa-solid fa-clock sm-grid-icon-org"></i>
                            </div>
                        </div>

            """, unsafe_allow_html=True)

        with total4:
             # Use st.markdown to create HTML content with the icon
            st.markdown(f"""
                        <div class="sm-grids-voilet">
                            <p class="sm-grid-title">Average Wrapup Time</p>
                            <div class="sm-grids-counts-voilet">
                                <p>
                                    {avg_wrapup_time_sec}
                                </p>
                                <i class="fa-solid fa-clock sm-grid-icon-voilet"></i>
                            </div>
                        </div>

            """, unsafe_allow_html=True)
    except Exception as err:
        log.error(str(err))
        traceback.print_exc()

def avg_metric_graphs_second(
    avg_call_duration_sec,avg_talk_time_sec,avg_queue_time_sec,avg_score
):
    try:
        total1, total2, total3, total4 = st.columns(4)
        with total1:
            # Use st.markdown to create HTML content with the icon
            st.markdown(f"""
                        <div class="sm-grids-teal-green">
                            <p class="sm-grid-title">Average Call Duration</p>
                            <div class="sm-grids-counts-teal-green">
                                <p>
                                    {avg_call_duration_sec}
                                </p>
                                <i class="fa-solid fa-clock sm-grid-icon-teal-green"></i>
                            </div>
                        </div>

            """, unsafe_allow_html=True)

        with total2:
             # Use st.markdown to create HTML content with the icon
            st.markdown(f"""
                        <div class="sm-grids-LightSalmon">
                            <p class="sm-grid-title">Average Talk Time</p>
                            <div class="sm-grids-counts-LightSalmon">
                                <p>
                                    {avg_talk_time_sec}
                                </p>
                                <i class="fa-solid fa-clock sm-grid-icon-LightSalmon"></i>
                            </div>
                        </div>

            """, unsafe_allow_html=True)

        with total3:
             # Use st.markdown to create HTML content with the icon
            st.markdown(f"""
                        <div class="sm-grids-Olive">
                            <p class="sm-grid-title">Average Queue Time</p>
                            <div class="sm-grids-counts-Olive">
                                <p>
                                    {avg_queue_time_sec}
                                </p>
                                <i class="fa-solid fa-clock sm-grid-icon-Olive"></i>
                            </div>
                        </div>

            """, unsafe_allow_html=True)

        with total4:
             # Use st.markdown to create HTML content with the icon
            st.markdown(f"""
                        <div class="sm-grids-Fuchsia">
                            <p class="sm-grid-title">Average Score</p>
                            <div class="sm-grids-counts-Fuchsia">
                                <p>
                                    {avg_score}
                                </p>
                                <i class="fa-solid fa-stopwatch-20 sm-grid-icon-Fuchsia"></i>
                            </div>
                        </div>

            """, unsafe_allow_html=True)
    except Exception as err:
        log.error(str(err))
        traceback.print_exc()


def productive_and_unproductive_graphs(productive_df,unproductive_df):
    try:
        col1,col2,col3 = st.columns([50,1,50])
        with col1:
            if not productive_df.empty:
                # Ensure that the Productive_Hours column is of type string
                productive_df['Productive_Hours'] = productive_df['Productive_Hours'].astype(str)

                # Extracting the time part from the Productive_Hours column and converting to hours
                productive_df['Total_Hours'] = productive_df['Productive_Hours'].apply(
                    lambda x: int(x.split(' ')[-1].split(':')[0]) + 
                            int(x.split(' ')[-1].split(':')[1]) / 60 + 
                            int(x.split(' ')[-1].split(':')[2]) / 3600
                )
                # Round the Total_Hours to 2 decimal places
                productive_df['Total_Hours'] = productive_df['Total_Hours'].round(3)
                # Sort the DataFrame based on 'Total_Hours' in descending order and get the top 10 agents
                productive_df = productive_df.sort_values(by='Total_Hours', ascending=False).head(10)
                agent_name_list = productive_df['agent_id'].tolist()
                # Extracting the time part from the Productive_Hours column
                productive_hours_list = productive_df['Total_Hours'].tolist()
            else:
                agent_name_list = []
                productive_hours_list = []

            options = {
                "title": {
                    "text": "Productive Hour (Top 10 Agent)",
                    "left": "left",
                    "textStyle": {
                        "fontSize": 12
                    }
                },
                'toolbox': {
                    'feature': {
                        "magicType": {
                            "show": "true",
                            "type": ['bar','line'] 
                        },
                        "restore": { 
                            "show": "true" 
                        },
                        'saveAsImage': {
                            'show': 'true'
                        }

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
                    "data": agent_name_list,
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
                        "name": 'Productive Hours',
                        "type": 'bar',
                        "smooth": 0.5,
                        "barWidth": '60%',
                        "data": productive_hours_list,
                        "color": ['#0a72c2']
                    }
                ]
            }
            # Display the pie chart using st_echarts
            st_echarts(options=options)
        
        with col3:
            if not unproductive_df.empty:
                # Ensure that the Productive_Hours column is of type string
                unproductive_df['Unproductive_Hours'] = unproductive_df['Unproductive_Hours'].astype(str)

                # Extracting the time part from the Productive_Hours column and converting to hours
                unproductive_df['Total_Hours'] = unproductive_df['Unproductive_Hours'].apply(
                    lambda x: int(x.split(' ')[-1].split(':')[0]) + 
                            int(x.split(' ')[-1].split(':')[1]) / 60 + 
                            int(x.split(' ')[-1].split(':')[2]) / 3600
                )
                # Round the Total_Hours to 2 decimal places
                unproductive_df['Total_Hours'] = unproductive_df['Total_Hours'].round(3)
                # Sort the DataFrame based on 'Total_Hours' in descending order and get the top 10 agents
                unproductive_df = unproductive_df.sort_values(by='Total_Hours', ascending=False).head(10)
                unproductive_hour_agent_name_list = unproductive_df['agent_id'].tolist()
                # Extracting the time part from the Productive_Hours column
                unproductive_hour_list = unproductive_df['Total_Hours'].tolist()
            else:
                unproductive_hour_agent_name_list = []
                unproductive_hour_list = []

            # Define the options dictionary for the ECharts
            options = {
                 "title": {
                    "text": "Unproductive Hours (Top 10 Agent)",
                    "left": "left",
                    "textStyle": {
                        "fontSize": 12
                    }
                },
                "tooltip": {
                    "trigger": "axis",
                    "axisPointer": {
                        "label": {
                            "backgroundColor": "#6a7985"
                        }
                    }
                },
                 "toolbox": {
                    "feature": {
                        "magicType": {
                            "show": "true",
                            "type": ['bar','line']
                        },
                        "restore": {
                            "show": "true"
                        },
                        "saveAsImage": {
                            "show": "true"
                        }
                    }
                },
                "grid": {
                    "left": "3%",
                    "right": "4%",
                    "bottom": "3%",
                    "containLabel": True
                },
                "xAxis": [
                    {
                        "type": "category",
                        "boundaryGap": False,
                        "axisLabel": {
                            "rotate": 45,  # Rotate x-axis labels by 45 degrees
                            "interval": 0,  # Display all labels
                            "margin": 10  # Adjust margin to avoid overlapping
                        },
                        "data": unproductive_hour_agent_name_list
                    }
                ],
                "yAxis": [
                    {
                        "type": "value"
                    }
                ],
                "series": [
                    {
                        "name": "Unproductive Hours",
                        "type": "line",
                        "smooth": 0.5,
                        "stack": "Total",
                        # "areaStyle": {},
                        "emphasis": {
                            "focus": "series"
                        },
                        "data": unproductive_hour_list,
                        "color": ['#0a72c2'],
                    }
                ]
            }

            # Display the ECharts graph
            st_echarts(options=options)
    except Exception as err:
        log.error(str(err))
        traceback.print_exc()


def wait_time_graphs(wait_time_df,hourly_trends_df,month_trends_df,days_trends_df,selected_filter_name):
    try:
        col1,col2,col3 = st.columns([50,1,50])
        with col1:
            if not wait_time_df.empty:
                wait_time_df['Wait_Time'] = wait_time_df['Wait_Time'] / 60
                wait_time_df['Wait_Time'] = wait_time_df['Wait_Time'].round(0)
                # Sort the DataFrame based on 'Wait_Time' in descending order and get the top 10 agents
                wait_time_df = wait_time_df.sort_values(by='Wait_Time', ascending=False).head(10)
                # Extracting the time part from the agent_name column
                agent_name_list = wait_time_df['agent_id'].tolist()
                # Extracting the time part from the Productive_Hours column
                wait_time_list = wait_time_df['Wait_Time'].tolist()
            else:
                agent_name_list = []
                wait_time_list = []

            options = {
                "title": {
                    "text": "Wait Time (Top 10 Agent)",
                    "left": "left",
                    "textStyle": {
                        "fontSize": 12
                    }
                },
                'toolbox': {
                    'feature': {
                        "magicType": { 
                            "show": "true", 
                            "type": ['bar','line'] 
                        },
                        "restore": {
                            "show": "true" 
                        },
                        'saveAsImage': { 
                            'show': 'true' 
                        }
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
                    "data": agent_name_list,
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
                        "name": 'Wait Time (In Min)',
                        "type": 'bar',
                        "smooth": 0.5,
                        "barWidth": '60%',
                        "data": wait_time_list,
                        "color": ['#0a72c2']
                    }
                ]
            }
            # Display the pie chart using st_echarts
            st_echarts(options=options)
        
        with col3:
            if selected_filter_name == "Yesterday" or selected_filter_name == "Last 7 Days":
                title_name = "(Hourly)"
                tmp_list = ['00','01','02','03','04','05','06','07','08','09','10','11','12','13','14','15','16','17','18','19','20','21','22','23']
                tmp_wait_time_list = []
                if not hourly_trends_df.empty:
                    hourly_trends_df['wait_time'] = hourly_trends_df['wait_time'] / 60
                    hourly_trends_df['wait_time'] = hourly_trends_df['wait_time'].round(0)
                    # Extracting the time part from the hour column
                    hour_list = hourly_trends_df['hour'].tolist()
                    # Extracting the time part from the wait_time column
                    wait_time_list = hourly_trends_df['wait_time'].tolist()

                    hour_list_1 = []
                    for hour in hour_list:
                        # Check if the integer has a single digit
                        if isinstance(hour, int) and len(str(hour)) == 1:
                            tmp_hour = "0"+str(hour)
                            hour_list_1.append(tmp_hour)
                        else:
                            tmp_hour = str(hour)
                            hour_list_1.append(tmp_hour)

                    # Create a dictionary from hour_list and wait_time_values for quick lookup
                    wait_time_dict = dict(zip(hour_list_1, wait_time_list))

                    # Create the result list with default value 0.0 for all hours
                    tmp_wait_time_list = [wait_time_dict.get(hour, 0.0) for hour in tmp_list]
            elif selected_filter_name == "Last Thirty Days":
                title_name = "(Days)"
                tmp_list = ['01','02','03','04','05','06','07','08','09','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24','25','26','27','28','29','30','31']
                tmp_wait_time_list = []
                if not days_trends_df.empty:
                    days_trends_df['wait_time'] = days_trends_df['wait_time'] / 60
                    days_trends_df['wait_time'] = days_trends_df['wait_time'].round(0)
                    # Extracting the time part from the hour column
                    hour_list = days_trends_df['days'].tolist()
                    # Extracting the time part from the wait_time column
                    wait_time_list = days_trends_df['wait_time'].tolist()

                    hour_list_1 = []
                    for hour in hour_list:
                        # Check if the integer has a single digit
                        if isinstance(hour, int) and len(str(hour)) == 1:
                            tmp_hour = "0"+str(hour)
                            hour_list_1.append(tmp_hour)
                        else:
                            tmp_hour = str(hour)
                            hour_list_1.append(tmp_hour)

                    # Create a dictionary from hour_list and wait_time_values for quick lookup
                    wait_time_dict = dict(zip(hour_list_1, wait_time_list))

                    # Create the result list with default value 0.0 for all hours
                    tmp_wait_time_list = [wait_time_dict.get(hour, 0.0) for hour in tmp_list]
            elif selected_filter_name in ["Last 3 Months","Last 6 Months","Last Year"]:
                title_name = "(Monthly)"
                tmp_list = ['01','02','03','04','05','06','07','08','09','10','11','12']
                tmp_wait_time_list = []
                if not month_trends_df.empty:
                    month_trends_df['wait_time'] = month_trends_df['wait_time'] / 60
                    month_trends_df['wait_time'] = month_trends_df['wait_time'].round(0)
                    # Extracting the time part from the hour column
                    hour_list = month_trends_df['months'].tolist()
                    # Extracting the time part from the wait_time column
                    wait_time_list = month_trends_df['wait_time'].tolist()

                    hour_list_1 = []
                    for hour in hour_list:
                        # Check if the integer has a single digit
                        if isinstance(hour, int) and len(str(hour)) == 1:
                            tmp_hour = "0"+str(hour)
                            hour_list_1.append(tmp_hour)
                        else:
                            tmp_hour = str(hour)
                            hour_list_1.append(tmp_hour)

                    # Create a dictionary from hour_list and wait_time_values for quick lookup
                    wait_time_dict = dict(zip(hour_list_1, wait_time_list))

                    # Create the result list with default value 0.0 for all hours
                    tmp_wait_time_list = [wait_time_dict.get(hour, 0.0) for hour in tmp_list]

            # Define the options dictionary for the ECharts
            options = {
                 "title": {
                    "text": f"Wait Time Trends {title_name}",
                    "left": "left",
                    "textStyle": {
                        "fontSize": 12
                    }
                },
                "tooltip": {
                    "trigger": "axis",
                    "axisPointer": {
                        "label": {
                            "backgroundColor": "#6a7985"
                        }
                    }
                },
                 "toolbox": {
                    "feature": {
                        "magicType": {
                            "show": "true",
                            "type": ['bar','line']
                        },
                        "restore": {
                            "show": "true"
                        },
                        "saveAsImage": {
                            "show": "true"
                        }
                    }
                },
                "grid": {
                    "left": "3%",
                    "right": "4%",
                    "bottom": "3%",
                    "containLabel": True
                },
                "xAxis": [
                    {
                        "type": "category",
                        "boundaryGap": False,
                        "axisLabel": {
                            "rotate": 45,  # Rotate x-axis labels by 45 degrees
                            "interval": 0,  # Display all labels
                            "margin": 10  # Adjust margin to avoid overlapping
                        },
                        "data": tmp_list
                    }
                ],
                "yAxis": [
                    {
                        "type": "value"
                    }
                ],
                "series": [
                    {
                        "name": "Wait Time (In Min)",
                        "type": "line",
                        "smooth": 0.5,
                        "stack": "Total",
                        # "areaStyle": {},
                        "emphasis": {
                            "focus": "series"
                        },
                        "data": tmp_wait_time_list,
                        "color": ['#0a72c2'],
                    }
                ]
            }

            # Display the ECharts graph
            st_echarts(options=options)
    except Exception as err:
        traceback.print_exc()
        log.error(str(err))


def wrapup_time_graphs(wrapup_time_df,hourly_trends_df,month_trends_df,days_trends_df,selected_filter_name):
    try:
        col1,col2,col3 = st.columns([50,1,50])
        with col1:
            if not wrapup_time_df.empty:
                wrapup_time_df['Wrapup_Time'] = wrapup_time_df['Wrapup_Time'] / 60
                wrapup_time_df['Wrapup_Time'] = wrapup_time_df['Wrapup_Time'].round(0)
                # Sort the DataFrame based on 'Wait_Time' in descending order and get the top 10 agents
                wrapup_time_df = wrapup_time_df.sort_values(by='Wrapup_Time', ascending=False).head(10)
                # Extracting the time part from the agent_name column
                agent_name_list = wrapup_time_df['agent_id'].tolist()
                # Extracting the time part from the Productive_Hours column
                wait_time_list = wrapup_time_df['Wrapup_Time'].tolist()
            else:
                agent_name_list = []
                wait_time_list = []

            options = {
                "title": {
                    "text": "Wrapup Time (Top 10 Agent)",
                    "left": "left",
                    "textStyle": {
                        "fontSize": 12
                    }
                },
                'toolbox': {
                    'feature': {
                        "magicType": { 
                            "show": "true", 
                            "type": ['bar','line'] 
                        },
                        "restore": {
                            "show": "true" 
                        },
                        'saveAsImage': { 
                            'show': 'true' 
                        }
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
                    "data": agent_name_list,
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
                        "name": 'Wrapup Time (In Min)',
                        "type": 'bar',
                        "smooth": 0.5,
                        "barWidth": '60%',
                        "data": wait_time_list,
                        "color": ['#0a72c2']
                    }
                ]
            }
            # Display the pie chart using st_echarts
            st_echarts(options=options)
        
        with col3:
            if selected_filter_name == "Yesterday" or selected_filter_name == "Last 7 Days":
                tmp_list = ['00','01','02','03','04','05','06','07','08','09','10','11','12','13','14','15','16','17','18','19','20','21','22','23']
                wrapup_time_lsit = []
                title_name = "(Hourly)"
                if not hourly_trends_df.empty:
                    hourly_trends_df['wrapup_time'] = hourly_trends_df['wrapup_time'] / 60
                    hourly_trends_df['wrapup_time'] = hourly_trends_df['wrapup_time'].round(0)
                    # Extracting the time part from the hour column
                    hour_list = hourly_trends_df['hour'].tolist()
                    # Extracting the time part from the wait_time column
                    wrapup_time_list = hourly_trends_df['wrapup_time'].tolist()

                    hour_list_1 = []
                    for hour in hour_list:
                        # Check if the integer has a single digit
                        if isinstance(hour, int) and len(str(hour)) == 1:
                            tmp_hour = "0"+str(hour)
                            hour_list_1.append(tmp_hour)
                        else:
                            tmp_hour = str(hour)
                            hour_list_1.append(tmp_hour)

                    # Create a dictionary from hour_list and wrapup_time_values for quick lookup
                    wrapup_time_dict = dict(zip(hour_list_1, wrapup_time_list))

                    # Create the result list with default value 0.0 for all hours
                    wrapup_time_lsit = [wrapup_time_dict.get(hour, 0.0) for hour in tmp_list]
            elif selected_filter_name == "Last Thirty Days":
                title_name = "(Days)"
                tmp_list = ['01','02','03','04','05','06','07','08','09','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24','25','26','27','28','29','30','31']
                wrapup_time_lsit = []
                if not days_trends_df.empty:
                    days_trends_df['wrapup_time'] = days_trends_df['wrapup_time'] / 60
                    days_trends_df['wrapup_time'] = days_trends_df['wrapup_time'].round(0)
                    # Extracting the time part from the hour column
                    hour_list = days_trends_df['days'].tolist()
                    # Extracting the time part from the wait_time column
                    wrapup_time_list = days_trends_df['wrapup_time'].tolist()

                    hour_list_1 = []
                    for hour in hour_list:
                        # Check if the integer has a single digit
                        if isinstance(hour, int) and len(str(hour)) == 1:
                            tmp_hour = "0"+str(hour)
                            hour_list_1.append(tmp_hour)
                        else:
                            tmp_hour = str(hour)
                            hour_list_1.append(tmp_hour)

                    # Create a dictionary from hour_list and wrapup_time_values for quick lookup
                    wrapup_time_dict = dict(zip(hour_list_1, wrapup_time_list))

                    # Create the result list with default value 0.0 for all hours
                    wrapup_time_lsit = [wrapup_time_dict.get(hour, 0.0) for hour in tmp_list]
            elif selected_filter_name in ["Last 3 Months","Last 6 Months","Last Year"]:
                title_name = "(Monthly)"
                tmp_list = ['01','02','03','04','05','06','07','08','09','10','11','12']
                wrapup_time_lsit = []
                if not month_trends_df.empty:
                    month_trends_df['wrapup_time'] = month_trends_df['wrapup_time'] / 60
                    month_trends_df['wrapup_time'] = month_trends_df['wrapup_time'].round(0)
                    # Extracting the time part from the hour column
                    hour_list = month_trends_df['months'].tolist()
                    # Extracting the time part from the wait_time column
                    wrapup_time_list = month_trends_df['wrapup_time'].tolist()

                    hour_list_1 = []
                    for hour in hour_list:
                        # Check if the integer has a single digit
                        if isinstance(hour, int) and len(str(hour)) == 1:
                            tmp_hour = "0"+str(hour)
                            hour_list_1.append(tmp_hour)
                        else:
                            tmp_hour = str(hour)
                            hour_list_1.append(tmp_hour)

                    # Create a dictionary from hour_list and wrapup_time_values for quick lookup
                    wrapup_time_dict = dict(zip(hour_list_1, wrapup_time_list))

                    # Create the result list with default value 0.0 for all hours
                    wrapup_time_lsit = [wrapup_time_dict.get(hour, 0.0) for hour in tmp_list]
                

            # Define the options dictionary for the ECharts
            options = {
                 "title": {
                    "text": f"Wrapup Time Trends {title_name}",
                    "left": "left",
                    "textStyle": {
                        "fontSize": 12
                    }
                },
                "tooltip": {
                    "trigger": "axis",
                    "axisPointer": {
                        "label": {
                            "backgroundColor": "#6a7985"
                        }
                    }
                },
                 "toolbox": {
                    "feature": {
                        "magicType": {
                            "show": "true",
                            "type": ['bar','line']
                        },
                        "restore": {
                            "show": "true"
                        },
                        "saveAsImage": {
                            "show": "true"
                        }
                    }
                },
                "grid": {
                    "left": "3%",
                    "right": "4%",
                    "bottom": "3%",
                    "containLabel": True
                },
                "xAxis": [
                    {
                        "type": "category",
                        "boundaryGap": False,
                        "axisLabel": {
                            "rotate": 45,  # Rotate x-axis labels by 45 degrees
                            "interval": 0,  # Display all labels
                            "margin": 10  # Adjust margin to avoid overlapping
                        },
                        "data": tmp_list
                    }
                ],
                "yAxis": [
                    {
                        "type": "value"
                    }
                ],
                "series": [
                    {
                        "name": "Wrapup Time (In Min)",
                        "type": "line",
                        "smooth": 0.5,
                        "stack": "Total",
                        # "areaStyle": {},
                        "emphasis": {
                            "focus": "series"
                        },
                        "data": wrapup_time_lsit,
                        "color": ['#0a72c2'],
                    }
                ]
            }

            # Display the ECharts graph
            st_echarts(options=options)
    except Exception as err:
        traceback.print_exc()
        log.error(str(err))


def call_duration_graphs(call_duration_df,hourly_trends_df,month_trends_df,days_trends_df,selected_filter_name):
    try:
        col1,col2,col3 = st.columns([50,1,50])
        with col1:
            if not call_duration_df.empty:
                call_duration_df['Call_Duration'] = call_duration_df['Call_Duration'] / 60
                call_duration_df['Call_Duration'] = call_duration_df['Call_Duration'].round(0)
                # Sort the DataFrame based on 'Call_Duration' in descending order and get the top 10 agents
                call_duration_df = call_duration_df.sort_values(by='Call_Duration', ascending=False).head(10)
                # Extracting the time part from the agent_name column
                agent_name_list = call_duration_df['agent_id'].tolist()
                # Extracting the time part from the Productive_Hours column
                call_duration_list = call_duration_df['Call_Duration'].tolist()
            else:
                agent_name_list = []
                call_duration_list = []


            options = {
                "title": {
                    "text": "Call Duration (Top 10 Agent)",
                    "left": "left",
                    "textStyle": {
                        "fontSize": 12
                    }
                },
                'toolbox': {
                    'feature': {
                        "magicType": {
                            "show": "true",
                            "type": ['bar','line']
                        },
                        "restore": {
                            "show": "true"
                        },
                        'saveAsImage': {
                            'show': 'true'
                        }
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
                    "data": agent_name_list,
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
                        "name": 'Call Duration (In Min)',
                        "type": 'bar',
                        "smooth": 0.5,
                        "barWidth": '60%',
                        "data": call_duration_list,
                        "color": ['#0a72c2']
                    }
                ]
            }
            # Display the pie chart using st_echarts
            st_echarts(options=options)
        
        with col3:
            if selected_filter_name == "Yesterday" or selected_filter_name == "Last 7 Days":
                tmp_list = ['00','01','02','03','04','05','06','07','08','09','10','11','12','13','14','15','16','17','18','19','20','21','22','23']
                call_duration_lsit = []
                title_name = "(Hourly)"
                if not hourly_trends_df.empty:
                    hourly_trends_df['call_duration'] = hourly_trends_df['call_duration'] / 60
                    hourly_trends_df['call_duration'] = hourly_trends_df['call_duration'].round(0)
                    # Extracting the time part from the hour column
                    hour_list = hourly_trends_df['hour'].tolist()
                    # Extracting the time part from the wait_time column
                    call_duration_list = hourly_trends_df['call_duration'].tolist()

                    hour_list_1 = []
                    for hour in hour_list:
                        # Check if the integer has a single digit
                        if isinstance(hour, int) and len(str(hour)) == 1:
                            tmp_hour = "0"+str(hour)
                            hour_list_1.append(tmp_hour)
                        else:
                            tmp_hour = str(hour)
                            hour_list_1.append(tmp_hour)

                    # Create a dictionary from hour_list and wrapup_time_values for quick lookup
                    call_duration_dict = dict(zip(hour_list_1, call_duration_list))

                    # Create the result list with default value 0.0 for all hours
                    call_duration_lsit = [call_duration_dict.get(hour, 0.0) for hour in tmp_list]
            elif selected_filter_name == "Last Thirty Days":
                title_name = "(Days)"
                tmp_list = ['01','02','03','04','05','06','07','08','09','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24','25','26','27','28','29','30','31']
                call_duration_lsit = []
                if not days_trends_df.empty:
                    days_trends_df['call_duration'] = days_trends_df['call_duration'] / 60
                    days_trends_df['call_duration'] = days_trends_df['call_duration'].round(0)
                    # Extracting the time part from the hour column
                    hour_list = days_trends_df['days'].tolist()
                    # Extracting the time part from the wait_time column
                    call_duration_list = days_trends_df['call_duration'].tolist()

                    hour_list_1 = []
                    for hour in hour_list:
                        # Check if the integer has a single digit
                        if isinstance(hour, int) and len(str(hour)) == 1:
                            tmp_hour = "0"+str(hour)
                            hour_list_1.append(tmp_hour)
                        else:
                            tmp_hour = str(hour)
                            hour_list_1.append(tmp_hour)

                    # Create a dictionary from hour_list and wrapup_time_values for quick lookup
                    call_duration_dict = dict(zip(hour_list_1, call_duration_list))

                    # Create the result list with default value 0.0 for all hours
                    call_duration_lsit = [call_duration_dict.get(hour, 0.0) for hour in tmp_list]
            elif selected_filter_name in ["Last 3 Months","Last 6 Months","Last Year"]:
                title_name = "(Monthly)"
                tmp_list = ['01','02','03','04','05','06','07','08','09','10','11','12']
                call_duration_lsit = []
                if not month_trends_df.empty:
                    month_trends_df['call_duration'] = month_trends_df['call_duration'] / 60
                    month_trends_df['call_duration'] = month_trends_df['call_duration'].round(0)
                    # Extracting the time part from the hour column
                    hour_list = month_trends_df['months'].tolist()
                    # Extracting the time part from the wait_time column
                    call_duration_list = month_trends_df['call_duration'].tolist()

                    hour_list_1 = []
                    for hour in hour_list:
                        # Check if the integer has a single digit
                        if isinstance(hour, int) and len(str(hour)) == 1:
                            tmp_hour = "0"+str(hour)
                            hour_list_1.append(tmp_hour)
                        else:
                            tmp_hour = str(hour)
                            hour_list_1.append(tmp_hour)

                    # Create a dictionary from hour_list and wrapup_time_values for quick lookup
                    call_duration_dict = dict(zip(hour_list_1, call_duration_list))

                    # Create the result list with default value 0.0 for all hours
                    call_duration_lsit = [call_duration_dict.get(hour, 0.0) for hour in tmp_list]

            # Define the options dictionary for the ECharts
            options = {
                 "title": {
                    "text": f"Call Duration Trends {title_name}",
                    "left": "left",
                    "textStyle": {
                        "fontSize": 12
                    }
                },
                "tooltip": {
                    "trigger": "axis",
                    "axisPointer": {
                        "label": {
                            "backgroundColor": "#6a7985"
                        }
                    }
                },
                 "toolbox": {
                    "feature": {
                        "magicType": {
                            "show": "true",
                            "type": ['bar','line']
                        },
                        "restore": {
                            "show": "true"
                        },
                        "saveAsImage": {
                            "show": "true"
                        }
                    }
                },
                "grid": {
                    "left": "3%",
                    "right": "4%",
                    "bottom": "3%",
                    "containLabel": True
                },
                "xAxis": [
                    {
                        "type": "category",
                        "boundaryGap": False,
                        "axisLabel": {
                            "rotate": 45,  # Rotate x-axis labels by 45 degrees
                            "interval": 0,  # Display all labels
                            "margin": 10  # Adjust margin to avoid overlapping
                        },
                        "data": tmp_list
                    }
                ],
                "yAxis": [
                    {
                        "type": "value"
                    }
                ],
                "series": [
                    {
                        "name": "Call Duration (In Min)",
                        "type": "line",
                        "smooth": 0.5,
                        "stack": "Total",
                        # "areaStyle": {},
                        "emphasis": {
                            "focus": "series"
                        },
                        "data": call_duration_lsit,
                        "color": ['#0a72c2'],
                    }
                ]
            }

            # Display the ECharts graph
            st_echarts(options=options)
    except Exception as err:
        log.error(str(err))
        traceback.print_exc()


def talk_time_graphs(talk_time_df,hourly_trends_df,month_trends_df,days_trends_df,selected_filter_name):
    try:
        col1,col2,col3 = st.columns([50,1,50])
        with col1:
            if not talk_time_df.empty:
                talk_time_df['Talk_Time'] = talk_time_df['Talk_Time'] / 60
                talk_time_df['Talk_Time'] = talk_time_df['Talk_Time'].round(0)
                # Sort the DataFrame based on 'Call_Duration' in descending order and get the top 10 agents
                talk_time_df = talk_time_df.sort_values(by='Talk_Time', ascending=False).head(10)
                # Extracting the time part from the agent_name column
                agent_name_list = talk_time_df['agent_id'].tolist()
                # Extracting the time part from the Productive_Hours column
                talk_time_list = talk_time_df['Talk_Time'].tolist()
            else:
                agent_name_list = []
                talk_time_list = []

            options = {
                "title": {
                    "text": "Talk Time (Top 10 Agent)",
                    "left": "left",
                    "textStyle": {
                        "fontSize": 12
                    }
                },
                'toolbox': {
                    'feature': {
                        "magicType": {
                            "show": "true",
                            "type": ['bar','line']
                        },
                        "restore": {
                            "show": "true"
                        },
                        'saveAsImage': {
                            'show': 'true'
                        }
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
                    "data": agent_name_list,
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
                        "name": 'Talk Time (In Min)',
                        "type": 'bar',
                        "smooth": 0.5,
                        "barWidth": '60%',
                        "data": talk_time_list,
                        "color": ['#0a72c2']
                    }
                ]
            }
            # Display the pie chart using st_echarts
            st_echarts(options=options)
        
        with col3:
            if selected_filter_name == "Yesterday" or selected_filter_name == "Last 7 Days":
                tmp_list = ['00','01','02','03','04','05','06','07','08','09','10','11','12','13','14','15','16','17','18','19','20','21','22','23']
                talk_time_list = []
                title_name = "(Hourly)"
                if not hourly_trends_df.empty:
                    hourly_trends_df['Agent_Talk_Time'] = hourly_trends_df['Agent_Talk_Time'] / 60
                    hourly_trends_df['Agent_Talk_Time'] = hourly_trends_df['Agent_Talk_Time'].round(0)
                    # Extracting the time part from the hour column
                    hour_list = hourly_trends_df['hour'].tolist()
                    # Extracting the time part from the wait_time column
                    talk_time_list = hourly_trends_df['Agent_Talk_Time'].tolist()

                    hour_list_1 = []
                    for hour in hour_list:
                        # Check if the integer has a single digit
                        if isinstance(hour, int) and len(str(hour)) == 1:
                            tmp_hour = "0"+str(hour)
                            hour_list_1.append(tmp_hour)
                        else:
                            tmp_hour = str(hour)
                            hour_list_1.append(tmp_hour)

                    # Create a dictionary from hour_list and wrapup_time_values for quick lookup
                    talk_time_dict = dict(zip(hour_list_1, talk_time_list))

                    # Create the result list with default value 0.0 for all hours
                    talk_time_list = [talk_time_dict.get(hour, 0.0) for hour in tmp_list]
            elif selected_filter_name == "Last Thirty Days":
                title_name = "(Days)"
                tmp_list = ['01','02','03','04','05','06','07','08','09','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24','25','26','27','28','29','30','31']
                talk_time_list = []
                if not days_trends_df.empty:
                    days_trends_df['Agent_Talk_Time'] = days_trends_df['Agent_Talk_Time'] / 60
                    days_trends_df['Agent_Talk_Time'] = days_trends_df['Agent_Talk_Time'].round(0)
                    # Extracting the time part from the hour column
                    hour_list = days_trends_df['days'].tolist()
                    # Extracting the time part from the wait_time column
                    talk_time_list = days_trends_df['Agent_Talk_Time'].tolist()

                    hour_list_1 = []
                    for hour in hour_list:
                        # Check if the integer has a single digit
                        if isinstance(hour, int) and len(str(hour)) == 1:
                            tmp_hour = "0"+str(hour)
                            hour_list_1.append(tmp_hour)
                        else:
                            tmp_hour = str(hour)
                            hour_list_1.append(tmp_hour)

                    # Create a dictionary from hour_list and wrapup_time_values for quick lookup
                    talk_time_dict = dict(zip(hour_list_1, talk_time_list))

                    # Create the result list with default value 0.0 for all hours
                    talk_time_list = [talk_time_dict.get(hour, 0.0) for hour in tmp_list]
            elif selected_filter_name in ["Last 3 Months","Last 6 Months","Last Year"]:
                title_name = "(Monthly)"
                tmp_list = ['01','02','03','04','05','06','07','08','09','10','11','12']
                talk_time_list = []
                if not month_trends_df.empty:
                    month_trends_df['Agent_Talk_Time'] = month_trends_df['Agent_Talk_Time'] / 60
                    month_trends_df['Agent_Talk_Time'] = month_trends_df['Agent_Talk_Time'].round(0)
                    # Extracting the time part from the hour column
                    hour_list = month_trends_df['months'].tolist()
                    # Extracting the time part from the wait_time column
                    talk_time_list = month_trends_df['Agent_Talk_Time'].tolist()

                    hour_list_1 = []
                    for hour in hour_list:
                        # Check if the integer has a single digit
                        if isinstance(hour, int) and len(str(hour)) == 1:
                            tmp_hour = "0"+str(hour)
                            hour_list_1.append(tmp_hour)
                        else:
                            tmp_hour = str(hour)
                            hour_list_1.append(tmp_hour)

                    # Create a dictionary from hour_list and wrapup_time_values for quick lookup
                    talk_time_dict = dict(zip(hour_list_1, talk_time_list))

                    # Create the result list with default value 0.0 for all hours
                    talk_time_list = [talk_time_dict.get(hour, 0.0) for hour in tmp_list]

            # Define the options dictionary for the ECharts
            options = {
                 "title": {
                    "text": f"Talk Time Trends {title_name}",
                    "left": "left",
                    "textStyle": {
                        "fontSize": 12
                    }
                },
                "tooltip": {
                    "trigger": "axis",
                    "axisPointer": {
                        "label": {
                            "backgroundColor": "#6a7985"
                        }
                    }
                },
                 "toolbox": {
                    "feature": {
                        "magicType": {
                            "show": "true",
                            "type": ['bar','line']
                        },
                        "restore": {
                            "show": "true"
                        },
                        "saveAsImage": {
                            "show": "true"
                        }
                    }
                },
                "grid": {
                    "left": "3%",
                    "right": "4%",
                    "bottom": "3%",
                    "containLabel": True
                },
                "xAxis": [
                    {
                        "type": "category",
                        "boundaryGap": False,
                        "axisLabel": {
                            "rotate": 45,  # Rotate x-axis labels by 45 degrees
                            "interval": 0,  # Display all labels
                            "margin": 10  # Adjust margin to avoid overlapping
                        },
                        "data": tmp_list
                    }
                ],
                "yAxis": [
                    {
                        "type": "value"
                    }
                ],
                "series": [
                    {
                        "name": "Talk Time (In Min)",
                        "type": "line",
                        "smooth": 0.5,
                        "stack": "Total",
                        # "areaStyle": {},
                        "emphasis": {
                            "focus": "series"
                        },
                        "data": talk_time_list,
                        "color": ['#0a72c2'],
                    }
                ]
            }

            # Display the ECharts graph
            st_echarts(options=options)
    except Exception as err:
        log.error(str(err))
        traceback.print_exc()


def queue_time_graphs(queue_time_df,hourly_trends_df,month_trends_df,days_trends_df,selected_filter_name):
    try:
        col1, col2,col3 = st.columns([50, 1, 50])
        with col1:
            if not queue_time_df.empty:
                queue_time_df['Queue_Time'] = queue_time_df['Queue_Time'] / 60
                queue_time_df['Queue_Time'] = queue_time_df['Queue_Time'].round(0)
                # Sort the DataFrame based on 'Queue_Time' in descending order and get the top 10 agents
                queue_time_df = queue_time_df.sort_values(by='Queue_Time', ascending=False).head(10)
                queue_time_agent_name_list = queue_time_df['agent_id'].tolist()
                # Extracting the time part from the Productive_Hours column
                queue_time_list = queue_time_df['Queue_Time'].tolist()
            else:
                queue_time_agent_name_list = []
                queue_time_list = []

            # Define the options dictionary for the ECharts
            options = {
                "title": {
                    "text": "Queue Time (Top 10 Agent)",
                    "left": "left",
                    "textStyle": {
                        "fontSize": 12
                    }
                },
                'toolbox': {
                    'feature': {
                        "magicType": {
                            "show": "true",
                            "type": ['bar','line']
                        },
                        "restore": {
                            "show": "true"
                        },
                        'saveAsImage': {
                            'show': 'true'
                        }
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
                    "data": queue_time_agent_name_list,
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
                        "name": 'Queue Time (In Min)',
                        "type": 'bar',
                        "smooth": 0.5,
                        "barWidth": '60%',
                        "data": queue_time_list,
                        "color": ['#0a72c2']
                    }
                ]
            }
            # Display the pie chart using st_echarts
            st_echarts(options=options)

        with col3:
            if selected_filter_name == "Yesterday" or selected_filter_name == "Last 7 Days":
                tmp_list = ['00','01','02','03','04','05','06','07','08','09','10','11','12','13','14','15','16','17','18','19','20','21','22','23']
                queue_time_list = []
                title_name = "(Hourly)"
                if not hourly_trends_df.empty:
                    hourly_trends_df['Agent_Queue_Time'] = hourly_trends_df['Agent_Queue_Time'] / 60
                    hourly_trends_df['Agent_Queue_Time'] = hourly_trends_df['Agent_Queue_Time'].round(0)
                    # Extracting the time part from the hour column
                    hour_list = hourly_trends_df['hour'].tolist()
                    # Extracting the time part from the wait_time column
                    queue_time_list = hourly_trends_df['Agent_Queue_Time'].tolist()

                    hour_list_1 = []
                    for hour in hour_list:
                        # Check if the integer has a single digit
                        if isinstance(hour, int) and len(str(hour)) == 1:
                            tmp_hour = "0"+str(hour)
                            hour_list_1.append(tmp_hour)
                        else:
                            tmp_hour = str(hour)
                            hour_list_1.append(tmp_hour)

                    # Create a dictionary from hour_list and wrapup_time_values for quick lookup
                    queue_time_dict = dict(zip(hour_list_1, queue_time_list))

                    # Create the result list with default value 0.0 for all hours
                    queue_time_list = [queue_time_dict.get(hour, 0.0) for hour in tmp_list]
            elif selected_filter_name == "Last Thirty Days":
                title_name = "(Days)"
                tmp_list = ['01','02','03','04','05','06','07','08','09','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24','25','26','27','28','29','30','31']
                queue_time_list = []
                if not days_trends_df.empty:
                    days_trends_df['Agent_Queue_Time'] = days_trends_df['Agent_Queue_Time'] / 60
                    days_trends_df['Agent_Queue_Time'] = days_trends_df['Agent_Queue_Time'].round(0)
                    # Extracting the time part from the hour column
                    hour_list = days_trends_df['days'].tolist()
                    # Extracting the time part from the wait_time column
                    queue_time_list = days_trends_df['Agent_Queue_Time'].tolist()

                    hour_list_1 = []
                    for hour in hour_list:
                        # Check if the integer has a single digit
                        if isinstance(hour, int) and len(str(hour)) == 1:
                            tmp_hour = "0"+str(hour)
                            hour_list_1.append(tmp_hour)
                        else:
                            tmp_hour = str(hour)
                            hour_list_1.append(tmp_hour)

                    # Create a dictionary from hour_list and wrapup_time_values for quick lookup
                    queue_time_dict = dict(zip(hour_list_1, queue_time_list))

                    # Create the result list with default value 0.0 for all hours
                    queue_time_list = [queue_time_dict.get(hour, 0.0) for hour in tmp_list]
            elif selected_filter_name in ["Last 3 Months","Last 6 Months","Last Year"]:
                title_name = "(Monthly)"
                tmp_list = ['01','02','03','04','05','06','07','08','09','10','11','12']
                queue_time_list = []
                if not month_trends_df.empty:
                    month_trends_df['Agent_Queue_Time'] = month_trends_df['Agent_Queue_Time'] / 60
                    month_trends_df['Agent_Queue_Time'] = month_trends_df['Agent_Queue_Time'].round(0)
                    # Extracting the time part from the hour column
                    hour_list = month_trends_df['months'].tolist()
                    # Extracting the time part from the wait_time column
                    queue_time_list = month_trends_df['Agent_Queue_Time'].tolist()

                    hour_list_1 = []
                    for hour in hour_list:
                        # Check if the integer has a single digit
                        if isinstance(hour, int) and len(str(hour)) == 1:
                            tmp_hour = "0"+str(hour)
                            hour_list_1.append(tmp_hour)
                        else:
                            tmp_hour = str(hour)
                            hour_list_1.append(tmp_hour)

                    # Create a dictionary from hour_list and wrapup_time_values for quick lookup
                    queue_time_dict = dict(zip(hour_list_1, queue_time_list))

                    # Create the result list with default value 0.0 for all hours
                    queue_time_list = [queue_time_dict.get(hour, 0.0) for hour in tmp_list]

            # Define the options dictionary for the ECharts
            options = {
                 "title": {
                    "text": f"Queue Time Trends {title_name}",
                    "left": "left",
                    "textStyle": {
                        "fontSize": 12
                    }
                },
                "tooltip": {
                    "trigger": "axis",
                    "axisPointer": {
                        "label": {
                            "backgroundColor": "#6a7985"
                        }
                    }
                },
                 "toolbox": {
                    "feature": {
                        "magicType": {
                            "show": "true",
                            "type": ['bar','line']
                        },
                        "restore": {
                            "show": "true"
                        },
                        "saveAsImage": {
                            "show": "true"
                        }
                    }
                },
                "grid": {
                    "left": "3%",
                    "right": "4%",
                    "bottom": "3%",
                    "containLabel": True
                },
                "xAxis": [
                    {
                        "type": "category",
                        "boundaryGap": False,
                        "axisLabel": {
                            "rotate": 45,  # Rotate x-axis labels by 45 degrees
                            "interval": 0,  # Display all labels
                            "margin": 10  # Adjust margin to avoid overlapping
                        },
                        "data": tmp_list
                    }
                ],
                "yAxis": [
                    {
                        "type": "value"
                    }
                ],
                "series": [
                    {
                        "name": "Queue Time (In Min)",
                        "type": "line",
                        "smooth": 0.5,
                        "stack": "Total",
                        # "areaStyle": {},
                        "emphasis": {
                            "focus": "series"
                        },
                        "data": queue_time_list,
                        "color": ['#0a72c2'],
                    }
                ]
            }

            # Display the ECharts graph
            st_echarts(options=options)
    except Exception as err:
        traceback.print_exc()
        log.error(str(err))


def agent_score_graphs(agent_score_df,agent_score_hourly_df):
    try:
        col1, col2,col3 = st.columns([50, 1, 50])
        with col1:
            if not agent_score_df.empty:
                # Extracting the time part from the Score column
                agent_id_list = agent_score_df['agent_id'].tolist()
                # Extracting the time part from the Score column
                score_list = agent_score_df['Normalized_Score'].tolist()
            else:
                agent_id_list = []
                score_list = []
    
            # Define the options dictionary for the ECharts
            options = {
                "title": {
                    "text": "Score (Top 10 Agent Hourly)",
                    "left": "left",
                    "textStyle": {
                        "fontSize": 12
                    }
                },
                'toolbox': {
                    'feature': {
                        "magicType": {
                            "show": "true",
                            "type": ['bar','line']
                        },
                        "restore": {
                            "show": "true"
                        },
                        'saveAsImage': {
                            'show': 'true'
                        }
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
                    "data": agent_id_list,
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
                        "name": 'Score',
                        "type": 'bar',
                        "smooth": 0.5,
                        "barWidth": '60%',
                        "data": score_list,
                        "color": ['#0a72c2']
                    }
                ]
            }
            # Display the pie chart using st_echarts
            st_echarts(options=options)

        with col3:
            if not agent_score_hourly_df.empty:
                # Extracting the time part from the Score column
                hour_list = agent_score_hourly_df['hour'].tolist()
                # Extracting the time part from the Score column
                score_list = agent_score_hourly_df['Normalized_Score'].tolist()
            else:
                hour_list = []
                score_list = []

            tmp_hour_list = ['00','01','02','03','04','05','06','07','08','09','10','11','12','13','14','15','16','17','18','19','20','21','22','23']

            hour_list_1 = []
            for hour in hour_list:
                # Check if the integer has a single digit
                if isinstance(hour, int) and len(str(hour)) == 1:
                    tmp_hour = "0"+str(hour)
                    hour_list_1.append(tmp_hour)
                else:
                    tmp_hour = str(hour)
                    hour_list_1.append(tmp_hour)

            # Create a dictionary from hour_list and wait_time_values for quick lookup
            score_list_dict = dict(zip(hour_list_1, score_list))

            # Create the result list with default value 0.0 for all hours
            score_list = [score_list_dict.get(hour, 0.0) for hour in tmp_hour_list]

            # Define the options dictionary for the ECharts
            options = {
                    "title": {
                    "text": "Scrore (Hourly)",
                    "left": "left",
                    "textStyle": {
                        "fontSize": 12
                    }
                },
                "tooltip": {
                    "trigger": "axis",
                    "axisPointer": {
                        "label": {
                            "backgroundColor": "#6a7985"
                        }
                    }
                },
                    "toolbox": {
                    "feature": {
                        "magicType": {
                            "show": "true",
                            "type": ['bar','line']
                        },
                        "restore": {
                            "show": "true"
                        },
                        "saveAsImage": {
                            "show": "true"
                        }
                    }
                },
                "grid": {
                    "left": "3%",
                    "right": "4%",
                    "bottom": "3%",
                    "containLabel": True
                },
                "xAxis": [
                    {
                        "type": "category",
                        "boundaryGap": False,
                        "axisLabel": {
                            "rotate": 45,  # Rotate x-axis labels by 45 degrees
                            "interval": 0,  # Display all labels
                            "margin": 10  # Adjust margin to avoid overlapping
                        },
                        "data": tmp_hour_list
                    }
                ],
                "yAxis": [
                    {
                        "type": "value"
                    }
                ],
                "series": [
                    {
                        "name": "Score",
                        "type": "line",
                        "smooth": 0.5,
                        "stack": "Total",
                        # "areaStyle": {},
                        "emphasis": {
                            "focus": "series"
                        },
                        "data": score_list,
                        "color": ['#0a72c2'],
                    }
                ]
            }

            # Display the ECharts graph
            st_echarts(options=options)
    except Exception as err:
        traceback.print_exc()
        log.error(str(err))


def main():
    campaign_names_list,status,session,username = access_url_parm()
    if len(campaign_names_list) != 0 or status != "":
        if status == "SUCCESS":
            count = st_autorefresh(interval=86400000, limit=1000000000, key="fizzbuzzcounter")

            selected_campaign_name,start_date, end_date, choose_analytics, selected_filter_name = select_box(campaign_names_list)

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
                    final_data_list = send_post_request(selected_campaign_name, start_date, end_date)

                    avg_productive_hour = final_data_list[0]
                    avg_unproductive_hour = final_data_list[1]
                    avg_wait_time_sec = final_data_list[2]
                    avg_wrapup_time_sec = final_data_list[3]
                    avg_call_duration_sec = final_data_list[4]
                    avg_talk_time_sec = final_data_list[5]
                    avg_queue_time_sec = final_data_list[6]
                    avg_score = final_data_list[7]
                    productive_df = pd.DataFrame(final_data_list[8])
                    unproductive_df = pd.DataFrame(final_data_list[9])
                    wait_time_df = pd.DataFrame(final_data_list[10])
                    wrapup_time_df = pd.DataFrame(final_data_list[11])
                    call_duration_df = pd.DataFrame(final_data_list[12])
                    talk_time_df = pd.DataFrame(final_data_list[13])
                    queue_time_df = pd.DataFrame(final_data_list[14])
                    agent_score_df = pd.DataFrame(final_data_list[15])
                    agent_score_hourly_df = pd.DataFrame(final_data_list[16])
                    hourly_trends_df = pd.DataFrame(final_data_list[17])
                    month_trends_df = pd.DataFrame(final_data_list[18])
                    days_trends_df = pd.DataFrame(final_data_list[19]) 

                    avg_metric_graphs_first(avg_productive_hour,avg_unproductive_hour,avg_wait_time_sec,avg_wrapup_time_sec)
                    avg_metric_graphs_second(avg_call_duration_sec,avg_talk_time_sec,avg_queue_time_sec,avg_score)
                    wait_time_graphs(wait_time_df,hourly_trends_df,month_trends_df,days_trends_df,selected_filter_name)
                    wrapup_time_graphs(wrapup_time_df,hourly_trends_df,month_trends_df,days_trends_df,selected_filter_name)
                    productive_and_unproductive_graphs(productive_df,unproductive_df)
                    call_duration_graphs(call_duration_df,hourly_trends_df,month_trends_df,days_trends_df,selected_filter_name)
                    talk_time_graphs(talk_time_df,hourly_trends_df,month_trends_df,days_trends_df,selected_filter_name)
                    queue_time_graphs(queue_time_df,hourly_trends_df,month_trends_df,days_trends_df,selected_filter_name)
                    agent_score_graphs(agent_score_df,agent_score_hourly_df)
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
