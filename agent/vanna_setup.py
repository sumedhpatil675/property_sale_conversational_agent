import os
import pandas as pd
import sqlite3

try:
    from vanna.openai import OpenAI_Chat
    from vanna.chromadb import ChromaDB_VectorStore
except ImportError:
    from vanna.legacy.openai.openai_chat import OpenAI_Chat
    from vanna.legacy.chromadb.chromadb_vector import ChromaDB_VectorStore

class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)

def get_vanna_instance():
    api_key = os.getenv("OPENAI_API_KEY")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    chroma_path = os.path.join(base_dir, "vanna_chroma_db")
    db_path = os.path.join(base_dir, "db.sqlite3")
    
    config = {
        "api_key": api_key,
        "model": "gpt-4o",
        "path": chroma_path
    }
    
    vn = MyVanna(config=config)
    
    # Override run_sql to use local sqlite connection directly
    vn.run_sql = lambda sql: pd.read_sql(sql, sqlite3.connect(db_path))
    vn.run_sql_is_set = True
    
    return vn

def setup_vanna_training():
    vn = get_vanna_instance()
    
    # New DDL for Property table
    ddl = """
    CREATE TABLE IF NOT EXISTS agent_property (
        id integer PRIMARY KEY AUTOINCREMENT,
        name varchar(255),
        bedrooms integer,
        bathrooms integer,
        completion_status varchar(100),
        unit_type varchar(100),
        developer_name varchar(255),
        price decimal,
        area_sq_mtrs real,
        property_type varchar(100),
        city varchar(100),
        country varchar(100),
        completion_date varchar(100),
        features text,
        facilities text,
        description text
    );
    """
    
    # Check if we need to retrain or add more examples
    # Since we are enhancing, let's just add them. Vanna handles duplicates usually or we just add.
    
    print("Enhancing Vanna Training...")
    vn.train(ddl=ddl)
    
    # Documentation to clarify columns
    vn.train(documentation="ALWAYS use 'property_type' column for filtering by type (apartment, villa, townhouse, penthouse, studio).")
    vn.train(documentation="NEVER use 'unit_type' for filtering property types like apartment or villa. It is unreliable.")
    vn.train(documentation="For 'studio', use property_type = 'Apartment' AND bedrooms = 0 OR property_type = 'Studio'.")
    vn.train(documentation="For 'off-plan', check completion_status = 'off-plan'.")
    vn.train(documentation="If searching for a specific area/community (e.g., Dubai Marina, Palm Jumeirah) and 'city' is generic (e.g., Dubai), SEARCH in 'name' AND 'description' columns using LIKE operator.")
    vn.train(documentation="For amenities (pool, gym, etc.), search in 'features' AND 'facilities' columns.")
    vn.train(documentation="If payment plan is requested, search for keywords in 'description' column since there is no payment_plan column.")
    vn.train(documentation="If searching for properties designed by a specific brand, designer or developer (e.g., Elie Saab, Fendi, Cavalli, MDC Investments), SEARCH in 'developer_name', 'name' AND 'description' columns using LIKE operator.")
    vn.train(documentation="'Silver Land Properties' is the name of the real estate agency. Do NOT filter by developer_name = 'Silver Land Properties' unless explicitly requested as a developer. Generally ignore 'Silver Land Properties' in the query.")
    
    # Correct SQL Examples
    vn.train(question="Find 2 bedroom apartments in Dubai", sql="SELECT * FROM agent_property WHERE city = 'Dubai' AND bedrooms = 2 AND property_type = 'apartment'")
    vn.train(question="Show me properties designed by MDC Investments LLC", sql="SELECT * FROM agent_property WHERE developer_name LIKE '%MDC Investments%' OR description LIKE '%MDC Investments%'")
    vn.train(question="Show me villas designed by Elie Saab", sql="SELECT * FROM agent_property WHERE (name LIKE '%Elie Saab%' OR description LIKE '%Elie Saab%') AND property_type = 'villa'")
    vn.train(question="I want a villa in Arabian Ranches", sql="SELECT * FROM agent_property WHERE (city = 'Arabian Ranches' OR name LIKE '%Arabian Ranches%' OR description LIKE '%Arabian Ranches%') AND property_type = 'villa'")
    vn.train(question="Show me penthouses in Downtown", sql="SELECT * FROM agent_property WHERE (city = 'Downtown' OR name LIKE '%Downtown%' OR description LIKE '%Downtown%') AND property_type = 'penthouse'")
    vn.train(question="Do you have studios for rent?", sql="SELECT * FROM agent_property WHERE property_type = 'studio' AND completion_status = 'rent'")
    vn.train(question="Looking for a house", sql="SELECT * FROM agent_property WHERE property_type IN ('villa', 'townhouse')")
    vn.train(question="Show me Emaar off-plan projects", sql="SELECT * FROM agent_property WHERE developer_name LIKE '%Emaar%' AND completion_status = 'off-plan'")
    vn.train(question="Search for properties under 1 million", sql="SELECT * FROM agent_property WHERE price < 1000000")
    vn.train(question="I want a 2 bedroom apartment in Dubai under 2 million", sql="SELECT * FROM agent_property WHERE city = 'Dubai' AND bedrooms = 2 AND property_type = 'apartment' AND price < 2000000")
    vn.train(question="Find a 3 bedroom villa in Dubai for less than 5 million", sql="SELECT * FROM agent_property WHERE city = 'Dubai' AND bedrooms = 3 AND property_type = 'villa' AND price < 5000000")
    vn.train(question="Show me apartments in Downtown with 1 bedroom under 1.5M", sql="SELECT * FROM agent_property WHERE (city = 'Downtown' OR name LIKE '%Downtown%' OR description LIKE '%Downtown%') AND property_type = 'apartment' AND bedrooms = 1 AND price < 1500000")
    vn.train(question="Do you have any 4 bedroom villas in Palm Jumeirah over 10 million?", sql="SELECT * FROM agent_property WHERE (city = 'Palm Jumeirah' OR name LIKE '%Palm Jumeirah%' OR description LIKE '%Palm Jumeirah%') AND property_type = 'villa' AND bedrooms = 4 AND price > 10000000")
    vn.train(question="What is the payment plan?", sql="SELECT description FROM agent_property WHERE description LIKE '%payment plan%' OR description LIKE '%installment%'")
    vn.train(question="Any properties with a pool?", sql="SELECT * FROM agent_property WHERE features LIKE '%pool%' OR facilities LIKE '%pool%'")
    vn.train(question="Find properties in Dubai Marina", sql="SELECT * FROM agent_property WHERE city = 'Dubai Marina' OR name LIKE '%Dubai Marina%' OR description LIKE '%Dubai Marina%'")

    return vn
