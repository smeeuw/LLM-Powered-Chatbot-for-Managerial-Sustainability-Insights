
from llama_index.core.bridge.pydantic import BaseModel, Field
from pathlib import Path
from typing import Dict, List
from config import TABLEINFO_DIR, LLM, ENGINE
from sqlalchemy import MetaData
import pandas as pd
from llama_index.core.objects import (
    SQLTableNodeMapping,
    ObjectIndex,
    SQLTableSchema,
)
import json
from llama_index.core.program import LLMTextCompletionProgram
from prompts import TABLE_INFO_PROMPT


#structure of the table information
#adapted from https://docs.llamaindex.ai/en/stable/examples/pipeline/query_pipeline_sql/
class TableInfo(BaseModel):
    """Information regarding a structured table."""

    tablename: str = Field(
        ..., description="the same tablename from the datasource"
    )
    tablesummary: str = Field(
        ..., description="concise summary/caption of the table and a description of all rows"
    )
    columndescription: str = Field(
        ..., description="A comma seperated list of all columns in the following style columnname: description of what is displayed"
    )
    level_values: str = Field(
        ..., description="Give a comma seperated list of all unique values for each Level as a single String"
    )


#get the table_info from the CSR_Tableinfo dir
#adapted from https://docs.llamaindex.ai/en/stable/examples/pipeline/query_pipeline_sql/
def get_tableinfo_with_index(idx: int) -> str:
    search_pattern = f"{idx}_*"
    # Get the list of matching files
    results_list = list(Path(TABLEINFO_DIR).glob(search_pattern))
    if not results_list:
        return None
    elif len(results_list) == 1:
        return TableInfo.parse_file(results_list[0])
    else:
        file_names = [file.name for file in results_list]
        raise ValueError(f"More than one file matching index: {file_names}")

def get_table_names(engine):
    metadata = MetaData()
    metadata.reflect(bind=engine)
    table_names = metadata.tables.keys()
    return table_names

#iterate the tables and and create a table_info if not present
#adapted from https://docs.llamaindex.ai/en/stable/examples/pipeline/query_pipeline_sql/
def create_tableinfo(engine):
    table_names = set()
    table_infos = []
    table_names_db = get_table_names(engine)
    for idx, table in enumerate(table_names_db):
        table_info = get_tableinfo_with_index(idx)
        if table_info:
            table_infos.append(table_info)
        else:
            while True:
                df = pd.read_sql_table(table, engine)  
                df_str = df.head(10).to_csv() 
                table_info = program(
                    table_str=df_str,
                    exclude_table_name_list=str(list(table_names_db)),
                )
                table_info.tablename = table
                tablename = table_info.tablename
                print(f"Processed table: {tablename}")
                if tablename not in table_names:
                    table_names.add(tablename)
                    break
                else:
                    # try again
                    print(f"Table name {tablename} already exists, trying again.")
                    pass
            out_file = f"{TABLEINFO_DIR}/{idx}_{tablename}.json"
            json.dump(table_info.dict(), open(out_file, "w"))
            table_infos.append(table_info)
    return table_infos
    
    
        
#LLM function for creating the Table_info
#adapted from https://docs.llamaindex.ai/en/stable/examples/pipeline/query_pipeline_sql/
program = LLMTextCompletionProgram.from_defaults(
    output_cls=TableInfo,
    llm = LLM,
    prompt_template_str=TABLE_INFO_PROMPT,
)

