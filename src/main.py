import pandas as pd
import os
import logging
import sys
import argparse
import json
import time
from db_handler import DBHandler
from prospect_matcher import ProspectMatcher


def main(args: list[str]):
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('samplead-excersize.log')
            ]
        )
    args = parse_args(args)
    
    db_handler = DBHandler()
    
    try:
        #log total matches count from db
        metches_count = db_handler.query('SELECT COUNT(*) FROM prospects_users_matches')
        logging.info(f"BEFORE running prospects users matches logic, total matches in db: {metches_count}")
        
        # run matching logic
        start_time = time.time()
        run_prospects_users_matches_logic(args, db_handler)
        end_time = time.time()
        total_runtime = end_time - start_time
        logging.info(f"Total run time: {total_runtime:.2f} seconds")
        
        # log total matches count from db
        metches_count = db_handler.query('SELECT COUNT(*) FROM prospects_users_matches')
        logging.info(f"AFTER running prospects users matches logic, total matches in db: {metches_count}")
        
    finally:
        db_handler.close()
        
        
   
def run_prospects_users_matches_logic(args: dict, db_handler: DBHandler):
    logging.info(f"running prospects users matches logic with args: {args}")
    
    country_regions_map = get_json_data(args.country_regions_map_path)
    users_locations_settings = get_json_data(args.users_locations_settings_path)
    logging.info(f"loaded country regions map of len: {len(country_regions_map)}")
    logging.info(f"loaded users locations settings of len: {len(users_locations_settings)}")
    
    try:
        prospects = pd.read_csv(args.prospects_path)
        logging.info(f"loaded prospects of size: {prospects.shape}")
    except Exception as e:
        logging.error(f"Failed to read prospects file at {args.prospects_path}: {e}")
        raise
    
    matcher = ProspectMatcher(country_regions_map, users_locations_settings)
    
    prospects_users_matches_df = matcher.match_prospects(prospects)
    logging.info(f"prospects users matches of size: {prospects_users_matches_df.shape}")

    db_handler.upsert_prospects_users_matches(prospects_users_matches_df)
    return prospects_users_matches_df


def parse_args(args: list[str]) -> dict:
    parser = argparse.ArgumentParser(description="Samplead Excersize Main Program")
    parser.add_argument("-c", "--country-regions-map-path", type=str, default="data/country-to-regions-mapping.json", help="Path to the country regions map file")
    parser.add_argument("-u", "--users-locations-settings-path", type=str, default="data/users-locations-settings.json", help="Path to the users locations settings file")
    parser.add_argument("-p", "--prospects-path", type=str, required=True, help="Path to the prospects file")
    
    parsed_args = parser.parse_args(args)
    logging.info(f"{parsed_args=}")
    
    return parsed_args

def get_json_data(json_file_path: str) -> dict:
    if not os.path.exists(json_file_path):
        raise FileNotFoundError(f"json file not found at {json_file_path}")

    with open(json_file_path, 'r') as f:
        return json.load(f)


if __name__ == "__main__":
    args = sys.argv[1:]  #exclude the script name (sys.argv[0])
    main(args)