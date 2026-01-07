"""
This module handles user interaction to set configurations, etc. for the script
"""
import json

"""
- set configs based on the arguments supplied 
"""

def ensure_valid_mode(args, valid_modes):
    # ask the User to input a valid 
    while not(args.mode in valid_modes):
        args.mode = input(f"Please input a valid mode, {valid_modes}: ")

"""
TODO: add try/catch handling for there not being this property, etc.
"""
def get_airtable_user_key():
    print("Retrieving data from Airtable requires a valid User Key")
    user_file = input("Input a path to a JSON or YAML file containing your user key:")
    # TODO: add YAML handling
    with open(user_file) as f:
        user_data = json.load(f)
        return user_data["airtable_api_key"]