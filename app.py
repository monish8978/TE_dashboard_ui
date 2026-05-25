# Importing the sys module for system-specific parameters and functions
import sys

# Importing the streamlit cli module as stcli
from streamlit import cli as stcli

# Entry point of the script
if __name__ == '__main__':
    # Setting the system arguments to run the Streamlit app
    sys.argv = ["streamlit", "run", "main.py"]

    # Running the Streamlit app using the main function from the streamlit cli module
    # and exiting the script with the exit code returned by the main function
    sys.exit(stcli.main())

