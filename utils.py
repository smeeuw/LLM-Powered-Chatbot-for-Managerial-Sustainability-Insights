from llama_index.core import SQLDatabase, VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.core.llms import ChatResponse
from llama_index.core.schema import TextNode
from typing import Dict, List
from pathlib import Path
from sqlalchemy import text
from config import EMBED_MODEL, SQL_DATABASE, ENGINE
from llama_index.core.objects import (
    SQLTableNodeMapping,
    ObjectIndex,
    SQLTableSchema,
)
import os
import re

#Creating the VectorStoreIndex for the LLM to work
#adapted from https://docs.llamaindex.ai/en/stable/examples/pipeline/query_pipeline_sql/
def index_all_tables(
    sql_database: SQLDatabase, table_index_dir: str = "table_index_dir"
) -> Dict[str, VectorStoreIndex]:
    """Index all tables."""
    if not Path(table_index_dir).exists():
        os.makedirs(table_index_dir)

    vector_index_dict = {}
    engine = sql_database.engine
    for table_name in sql_database.get_usable_table_names():
        print(f"Indexing rows in table: {table_name}")
        if not os.path.exists(f"{table_index_dir}/{table_name}"):
            # get all rows from table
            with engine.connect() as conn:
                cursor = conn.execute(text(f'SELECT * FROM "{table_name}"'))
                result = cursor.fetchall()
                row_tups = []
                for row in result:
                    row_tups.append(tuple(row))

            # index each row, put into vector store index
            nodes = [TextNode(text=str(t)) for t in row_tups]

            # put into vector store index (use OpenAIEmbeddings by default)
            index = VectorStoreIndex(nodes,
                                     embed_model=EMBED_MODEL,)

            # save index
            index.set_index_id("vector_index")
            index.storage_context.persist(f"{table_index_dir}/{table_name}")
        else:
            # rebuild storage context
            storage_context = StorageContext.from_defaults(
                persist_dir=f"{table_index_dir}/{table_name}"
            )
            # load index
            index = load_index_from_storage(
                storage_context, index_id="vector_index"
            )
        vector_index_dict[table_name] = index

    return vector_index_dict

#adapted from https://docs.llamaindex.ai/en/stable/examples/pipeline/query_pipeline_sql/
def create_obj_retriever(table_infos,sql_database):
    # add a SQLTableSchema for each table
    table_node_mapping = SQLTableNodeMapping(sql_database)
    table_schema_objs = [
        SQLTableSchema(table_name=t.tablename, context_str=t.tablesummary)
        for t in table_infos
    ]  

    
    obj_index = ObjectIndex.from_objects(
        table_schema_objs,
        table_node_mapping,
        VectorStoreIndex,
        embed_model=EMBED_MODEL,
    ) 
    return obj_index.as_retriever(similarity_top_k=5)


#Building a context string for the LLM to get better results   
#adapted from https://docs.llamaindex.ai/en/stable/examples/pipeline/query_pipeline_sql/ 
def get_table_context_and_rows_str(
    query_str: str, table_schema_objs: List[SQLTableSchema]
):
    """Get table context string."""
    context_strs = []
    vector_index_dict = index_all_tables(SQL_DATABASE)
    for table_schema_obj in table_schema_objs:
        # first append table info + additional context
        table_info = SQL_DATABASE.get_single_table_info(
            table_schema_obj.table_name
        )
        if table_schema_obj.context_str:
            table_opt_context = " The table description is: "
            table_opt_context += table_schema_obj.context_str
            table_info += table_opt_context

        # also lookup vector index to return relevant table rows
        vector_retriever = vector_index_dict[
            table_schema_obj.table_name
        ].as_retriever(similarity_top_k=5)
        relevant_nodes = vector_retriever.retrieve(query_str)
        if len(relevant_nodes) > 0:
            table_row_context = "\nHere are some relevant example rows (values in the same order as columns above)\n"
            for node in relevant_nodes:
                table_row_context += str(node.get_content()) + "\n"
            table_info += table_row_context

        context_strs.append(table_info)
    return "\n\n".join(context_strs)

#adapted from https://docs.llamaindex.ai/en/stable/examples/pipeline/query_pipeline_sql/
def parse_response_to_sql(response: ChatResponse) -> str:
    """Parse response to SQL."""
    response = response.message.content
    sql_query_start = response.find("SQLQuery:")
    if sql_query_start != -1:
        response = response[sql_query_start:]
        if response.startswith("SQLQuery:"):
            response = response[len("SQLQuery:") :]
    sql_result_start = response.find("SQLResult:")
    if sql_result_start != -1:
        response = response[:sql_result_start]
    return response.strip().strip("```").strip()

def create_level_values_string(table_infos):
    # Initialisieren des Ergebnis-Dictionaries für die Level-Werte mit Sets
     levels = {
        'level1': set(),
        'level2': set(),
        'level3': set(),
        'level4': set()
     }
     if table_infos:
        import re
        for table_info in table_infos:
            level_values = table_info.level_values
            parts = re.split(r'(level[1-4]:)', level_values)
            temp_levels = {'level1': [], 'level2': [], 'level3': [], 'level4': []}
            current_level = None
            for part in parts:
                if 'level' in part:
                    current_level = part[:-1].strip()  
                elif current_level:
                    temp_levels[current_level].append(part.strip())
            for key in temp_levels:
                levels[key].update(temp_levels[key])

     for key in levels:
        levels[key] = ', '.join(levels[key])

     return levels
 
 
def convert_result(context_str):
    context = context_str[0].text

    # Muster für Zahlen in Klammern, z.B. (1532,)
    pattern_numbers = re.compile(r'\((\d+(?:\.\d+)?),?\)')
    matches_numbers = pattern_numbers.findall(context)
    
    # Muster für Tupel, z.B. ('LPG', 13255.77)
    pattern_tuples = re.compile(r"\('(\w+)',\s*(\d+(?:\.\d+)?)\)")
    matches_tuples = pattern_tuples.findall(context)
    
    result_list = []
    
    if matches_numbers:
        result_list.extend(matches_numbers)
    
    if matches_tuples:
        formatted_tuples = [f"{key}= {value}" for key, value in matches_tuples]
        result_list.extend(formatted_tuples)
    
    if result_list:
        result_str = ', '.join(result_list)
        return result_str
    else:
        return ""