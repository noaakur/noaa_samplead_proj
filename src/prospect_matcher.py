import logging
import pandas as pd


class ProspectMatcher:
    # prospect touser matching logic based on location preferences.
    
    def __init__(self, country_regions_map: dict, users_locations_settings: dict):
        # country_regions_map: mapping of location codes to regions
        # users_locations_settings: user location preferences (include/exclude)

        self.country_regions_map = country_regions_map
        self.users_locations_settings = users_locations_settings
        self.reverse_map = self._create_reverse_mapping(country_regions_map)
        self.users_locations_df = self._create_user_location_df()
        
        logging.info(f"ProspectMatcher initialized with {len(users_locations_settings)} users")
        logging.info(f"User location matrix shape: {self.users_locations_df.shape}")
    
    def match_prospects(self, prospects: pd.DataFrame) -> pd.DataFrame:

        if prospects.empty:
            return pd.DataFrame(columns=prospects.columns)
        
        # transform users_locations_df to a simple df(user_id, location) for df merge  
        enabled_locations = []
        for user_id in self.users_locations_df.index:
            # get all locations where this user has True
            user_locations = self.users_locations_df.loc[user_id]
            enabled = user_locations[user_locations == True].index.tolist()
            for loc in enabled:
                enabled_locations.append({'user_id': user_id, 'location': loc})
        
        enabled_df = pd.DataFrame(enabled_locations)
        
        if enabled_df.empty:
            return pd.DataFrame(columns=prospects.columns)
        
        prospects_copy = prospects.copy()
        
        # for US prospects, use state; for non-US, use country
        prospects_copy['location'] = prospects_copy.apply(
            lambda row: row['company_state'] if row['company_country'] == 'US' and pd.notna(row['company_state'])
                        else row['company_country'],
            axis=1
        )
        
        # merge prospects with enabled locations
        matched = prospects_copy.merge(
            enabled_df,
            on=['user_id', 'location'],
            how='inner'
        )
        
        return matched[prospects.columns]
    
    def match_prospects_iterative(self, prospects: pd.DataFrame) -> pd.DataFrame:
        matches = []
        
        for idx, row in prospects.iterrows():
            user_id = row['user_id']
            country = row['company_country']
            state = row['company_state']
            
            #skip if user doesnt exist in users_locations_df
            if user_id not in self.users_locations_df.index:
                continue
            
            #for US, check state; for other countries, check country
            if country == 'US':
                #if state column exists and if state in user's include list
                if pd.notna(state) and state in self.users_locations_df.columns:
                    if self.users_locations_df.loc[user_id, state]:
                        matches.append(idx)
            else:
                #if country column exists and if country in user's include list
                if country in self.users_locations_df.columns:
                    if self.users_locations_df.loc[user_id, country]:
                        matches.append(idx)
        
        return prospects.loc[matches] if matches else pd.DataFrame(columns=prospects.columns)
    
    def _create_reverse_mapping(self, mapping_data: dict) -> dict:
        # mapping regions to list of location codes
        reverse_map = {}
        
        for location_code, regions in mapping_data.items():     
            for region in regions:
                if region not in reverse_map:
                    reverse_map[region] = []
                reverse_map[region].append(location_code)
        
        return reverse_map
    
    def _create_user_location_df(self) -> pd.DataFrame:
        # a df of user location preferences.

        users_data = self.users_locations_settings
        mapping_data = self.country_regions_map
        
        user_ids = list(set(users_data.keys()))
        country_codes = sorted(mapping_data.keys())
        df = pd.DataFrame(
            False, #default to False
            index=user_ids,
            columns=country_codes
        )
        df.index.name = "user_id"

        for user_id, settings in users_data.items():
            location_include = settings.get("location_include") or [] 
            location_exclude = settings.get("location_exclude") or []
            
            #handle include locations
            locations_to_include = set()
            for item in location_include:
                if item == "All":
                    locations_to_include.update(country_codes)
                elif item in country_codes:
                    locations_to_include.update([item])
                elif item in self.reverse_map:
                    locations_to_include.update(self.reverse_map[item])
                else:
                    #unknown location
                    logging.warning(f"Unknown location {item} in include: {user_id=} settings: {location_include=}")
            
            #handle exclude locations
            locations_to_exclude = set()
            for item in location_exclude:
                if item == "All":
                    locations_to_exclude.update(country_codes)
                elif item in country_codes:
                    locations_to_exclude.update([item])
                elif item in self.reverse_map:
                    locations_to_exclude.update(self.reverse_map[item])
                else:
                    #unknown location
                    logging.warning(f"Unknown location {item} in include: {user_id=} settings: {location_exclude=}")
            
            df.loc[user_id,list(locations_to_include)] = True
            conflicts = locations_to_include & locations_to_exclude
            if conflicts:
                df.loc[user_id,list(conflicts)] = False
                logging.info(f"User {user_id}: Exclude overriding include for {len(conflicts)} locations")
                logging.info(f"Conflicting locations: {conflicts}")
            
        return df

