import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load .env file
load_dotenv()
logger.info("Loaded .env file for DB connection")

def get_db_connection():
    try:
        host = os.getenv('MYSQL_HOST', 'localhost')
        dbname = os.getenv('MYSQL_DBNAME', 'ingres_db')
        user = os.getenv('MYSQL_USER', 'root')
        password = os.getenv('MYSQL_PASSWORD', '')
        port = os.getenv('MYSQL_PORT', 3306)

        connection_string = f"mysql+pymysql://{user}:{password}@{host}:{port}/{dbname}"
        engine = create_engine(connection_string)
        logger.info(f"Connected to MySQL database: {dbname} at {host}:{port}")
        return engine
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        raise

if __name__ == '__main__':
    # Test connection
    conn = get_db_connection()
    with conn.connect() as connection:
        result = connection.execute("SELECT 1").fetchall()
        logger.info(f"Test query result: {result}")