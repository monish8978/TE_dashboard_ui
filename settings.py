# domain of the current server
domain = "http://172.16.1.247"  # IP address used for API and server interactions

api_url = 'http://172.16.1.247:50002'

# API endpoint URL for retrieving data
api_end_url = f'{api_url}/get-data'  # Endpoint to fetch data from the API

cmp_api_end_url = f'{api_url}/get-data-cmp'  # Endpoint to fetch data from the API

agent_api_end_url = f'{api_url}/get-data-agent'  # Endpoint to fetch data from the API

agent_list_api_url = f'{api_url}/agent-list'

skill_list_api_url = f'{api_url}/skill-list'

list_name_api_url = f'{api_url}/list-name'

# API URL for accessing the campaign name list
camp_api_url = "http://172.16.1.247/apps/czAppHandler.php"  # Endpoint to retrieve campaign names

# Login URL for the application
login_url = domain + "/"  # URL for user login

# Path to main log file
main_log_path = '/var/log/czentrix/TE_dashboard/main.log'  # Log file for main application events

# Log path for UI service checks
log_path_check_service_ui = '/var/log/czentrix/TE_dashboard/service_check_ui.log'  # Log file for monitoring UI service status

# Path to store filter-related files
filter_path = "/var/log/czentrix/TE_dashboard/filter/"  # Directory for filter-related files

# Paths for downloading historical and live data in CSV format
download_csv_row_data = '/var/log/czentrix/TE_dashboard/download_csv_row_data/hitorical_data/'  # Directory for historical data CSV
# download_csv_live_current_row_data = '/var/log/czentrix/TE_dashboard/download_csv_row_data/live_data/' # (Commented out) Directory for live data CSV

dashboard_names_list = ["Telephony Dashboard","Campaign Details Dashboard"]

# Dashboard reload time in milliseconds
dashboard_reload_time = 50000  # Interval for refreshing the dashboard (in milliseconds)
