import os
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from contextlib import contextmanager


class DBHandler:
    
    def __init__(self):
        self.db_user = os.getenv('POSTGRES_USER', 'dbuser')
        self.db_password = os.getenv('POSTGRES_PASSWORD', 'dbpassword')
        self.db_host = os.getenv('DB_HOST', 'localhost')
        self.db_port = os.getenv('DB_PORT', '5432')
        self.db_name = os.getenv('POSTGRES_DB', 'samplead_db')
        
        #build database URL
        self.db_url = (
            f"postgresql://{self.db_user}:{self.db_password}@"
            f"{self.db_host}:{self.db_port}/{self.db_name}"
        )
        
        self._engine =None
        logging.info(f"DBHandler initialized with connection to {self.db_host}:{self.db_port}/{self.db_name}")
    
    @property
    def engine(self):
        # lazy-load the database engine.
        if self._engine is None:
            self._engine = create_engine(self.db_url)
            logging.info("Database engine created")
        return self._engine
    
    @contextmanager
    def get_connection(self):
        # context manager for database connections.
        conn = self.engine.connect()
        try:
            yield conn
        finally:
            conn.close()
    
    def upsert_prospects_users_matches(self, prospects_users_matches_df: pd.DataFrame) -> None:
        if prospects_users_matches_df.empty:
            logging.info("No prospects users matches to upsert")
            return
        
        # validate required columns
        required_columns = ['user_id', 'prospect_id', 'company_country', 'company_state']
        for col in required_columns:
            if col not in prospects_users_matches_df.columns:
                raise ValueError(f"Required column '{col}' not found in DataFrame")
        
        # handle NaN values by replacing with None
        df_to_insert = prospects_users_matches_df[required_columns].copy()
        df_to_insert['company_state'] = df_to_insert['company_state'].where(
            df_to_insert['company_state'].notna(), None
        )
        df_to_insert['company_country'] = df_to_insert['company_country'].where(
            df_to_insert['company_country'].notna(), None
        )
        
        # df to list of dictionaries for bulk insert
        records = df_to_insert.to_dict('records')
        
        # query with ON CONFLICT clause for upsert
        upsert_query = text("""
            INSERT INTO prospects_users_matches 
                (user_id, prospect_id, company_country, company_state)
            VALUES (:user_id, :prospect_id, :company_country, :company_state)
            ON CONFLICT (user_id, prospect_id) 
            DO UPDATE SET
                company_country = EXCLUDED.company_country,
                company_state = EXCLUDED.company_state,
                created_at = CURRENT_TIMESTAMP
        """)
        
        try:
            # bulk insert using connection context manager
            with self.engine.begin() as conn: 
                conn.execute(upsert_query, records)
            
            logging.info(f"Successfully upserted {len(prospects_users_matches_df)} prospects users matches")
            
        except Exception as e:
            logging.error(f"Error upserting prospects users matches: {e}")
            raise
    
    def query(self, query_str: str) -> pd.DataFrame or int or None:
        # execute a SQL query and return appropriate result.
        try:
            with self.get_connection() as conn:
                result = conn.execute(text(query_str))
                
                # check if query returns rows (SELECT queries)
                if result.returns_rows:
                    df = pd.DataFrame(result.fetchall(), columns=result.keys())
                    logging.info(f"Query executed successfully. Returned {len(df)} rows")
                    return df
                else:
                    # INSERT, UPDATE, DELETE queries - return affected row count
                    rowcount = result.rowcount
                    logging.info(f"Query executed successfully. Affected {rowcount} rows")
                    return rowcount
                    
        except Exception as e:
            logging.error(f"Error executing query: {e}")
            raise
    
    def close(self) -> None:
        # clouse and cleanup
        if self._engine is not None:
            self._engine.dispose()
            logging.info("Database engine disposed")
            self._engine = None

