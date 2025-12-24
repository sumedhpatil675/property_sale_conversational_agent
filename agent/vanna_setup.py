import os
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
    chroma_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vanna_chroma_db")
    
    config = {
        "api_key": api_key,
        "model": "gpt-3.5-turbo",
        "path": chroma_path
    }
    
    vn = MyVanna(config=config)
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db.sqlite3")
    vn.connect_to_sqlite(db_path)
    
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
    
    training_data = vn.get_training_data()
    # If empty or we want to force retrain (for now assume check is enough)
    if training_data is None or len(training_data) < 5:
        print("Training Vanna with Property DDL...")
        vn.train(ddl=ddl)
        vn.train(documentation="The 'agent_property' table contains real estate projects and units for sale.")
        vn.train(documentation="The column 'property_type' indicates if it is an apartment, villa, or townhouse. Use this for filtering type.")
        vn.train(documentation="The column 'unit_type' often contains specific model names or bedroom counts (e.g. '2 BR') and is less reliable for filtering than 'property_type' or 'bedrooms'.")
        
        vn.train(sql="SELECT * FROM agent_property WHERE city = 'Chicago' AND price < 1000000")
        vn.train(question="Find 2 bedroom apartments in Chicago", sql="SELECT * FROM agent_property WHERE city = 'Chicago' AND bedrooms = 2 AND property_type = 'apartment'")
        vn.train(question="Show me villas in Dubai", sql="SELECT * FROM agent_property WHERE city = 'Dubai' AND property_type = 'villa'")
        
        # New training for details
        vn.train(question="Tell me about Sobha Crest", sql="SELECT * FROM agent_property WHERE name LIKE '%Sobha Crest%'")
        vn.train(question="What are the amenities at Beachgate?", sql="SELECT features, facilities, description FROM agent_property WHERE name LIKE '%Beachgate%'")
        vn.train(question="Give me details of Project X", sql="SELECT * FROM agent_property WHERE name LIKE '%Project X%'")
        
        # Explicit training to avoid unit_type filtering
        vn.train(question="Find 2 bedroom apartments in Dubai", sql="SELECT * FROM agent_property WHERE city = 'Dubai' AND bedrooms = 2 AND property_type = 'apartment'")
    
    return vn
