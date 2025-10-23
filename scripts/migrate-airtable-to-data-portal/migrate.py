import migrate
import argparse

parser = argparse.ArgumentParser()

parser.add_argument("-m", "--mode", help="Set the mode of data input, either 'airtable' or 'csv'")
parser.add_argument("-c", "--config", help="Specify a path to a directory containing configuration files")

args = parser.parse_args()

# ensures that the flag for 'mode' is passed correctly
migrate.user.ensure_valid_mode(args, migrate.config.VALID_MODES)

# set configurations based on the passed arguments
migrate.config.set_configs(args)

"""
call a wrangle.py function to get data based on the mode
"""
migrate.wrangle.get_data()

"""
call a transform.py function to parse data
"""

