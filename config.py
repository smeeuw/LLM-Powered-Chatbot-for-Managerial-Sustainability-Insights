from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from sqlalchemy import create_engine
from llama_index.core import SQLDatabase


#the directory to save the information on the Database
TABLEINFO_DIR = "CSR_Tableinfo"
#the name of the llm
MODEL_NAME = "llama3:70b"
#engine of the Database
ENGINE = create_engine("sqlite:///chatDB.db")
#The llm and the embedding. The Large language Model can be changed here
LLM = Ollama(model=MODEL_NAME, request_timeout=1200.0)
EMBED_MODEL = OllamaEmbedding(model_name=MODEL_NAME)
#the Database
SQL_DATABASE = SQLDatabase(ENGINE)