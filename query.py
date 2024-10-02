from llama_index.core.retrievers import SQLRetriever
from llama_index.core.query_pipeline import FnComponent
from llama_index.core.query_pipeline import FnComponent
from llama_index.core.query_pipeline import (
    QueryPipeline as QP,
    InputComponent,
)
from prompts import  create_text_to_sql_prompt, create_response_synthesis_prompt
from config import LLM, ENGINE, SQL_DATABASE
from tableinfo import create_tableinfo
from utils import  create_obj_retriever, get_table_context_and_rows_str, parse_response_to_sql, convert_result




def create_query_pipeline():

    table_infos = create_tableinfo(ENGINE)

    obj_retriever = create_obj_retriever(table_infos,SQL_DATABASE)

    sql_retriever = SQLRetriever(SQL_DATABASE)

    table_parser_component = FnComponent(fn=get_table_context_and_rows_str)    

    sql_parser_component = FnComponent(fn=parse_response_to_sql)

    text2sql_prompt = create_text_to_sql_prompt(ENGINE,table_infos)

    response_synthesis_prompt = create_response_synthesis_prompt()
    
    result_converter = FnComponent(fn=convert_result)

    #Creating the Querypipeline with all components
    #adapted from https://docs.llamaindex.ai/en/stable/examples/pipeline/query_pipeline_sql/
    qp = QP(
        modules={
            "input": InputComponent(),
            "table_retriever": obj_retriever,
            "table_output_parser": table_parser_component,
            "text2sql_prompt": text2sql_prompt,
            "text2sql_llm": LLM,
            "sql_output_parser": sql_parser_component,
            "sql_retriever": sql_retriever,
            "result_converter": result_converter,
            "response_synthesis_prompt": response_synthesis_prompt,
            "response_synthesis_llm": LLM,
        },
        verbose=True,
    )

    #Setting up the order in wich the components are linked
    #adapted from https://docs.llamaindex.ai/en/stable/examples/pipeline/query_pipeline_sql/
    qp.add_link("input", "table_retriever")
    qp.add_link("input", "table_output_parser", dest_key="query_str")
    qp.add_link(
        "table_retriever", "table_output_parser", dest_key="table_schema_objs"
    )
    qp.add_link("input", "text2sql_prompt", dest_key="query_str")
    qp.add_link("table_output_parser", "text2sql_prompt", dest_key="schema")
    qp.add_chain(
        ["text2sql_prompt", "text2sql_llm", "sql_output_parser", "sql_retriever"]
    )
    qp.add_link(
        "sql_output_parser", "response_synthesis_prompt", dest_key="sql_query"
    )
    qp.add_link(
        "sql_retriever", "result_converter", dest_key="context_str"
    )
    qp.add_link(
        "result_converter", "response_synthesis_prompt", dest_key="result_str"
    )
    qp.add_link(
        "sql_retriever", "response_synthesis_prompt", dest_key="context_str"
    )
    qp.add_link("input", "response_synthesis_prompt", dest_key="query_str")
    qp.add_link("response_synthesis_prompt", "response_synthesis_llm")
    
    
    
    
    

    return qp


    #qp.add_link("input", "table_retriever")
    #qp.add_link("input", "table_output_parser", dest_key="query_str")
    #qp.add_link(
    #    "table_retriever", "table_output_parser", dest_key="table_schema_objs"
    #)
    #qp.add_link("input", "text2sql_prompt", dest_key="query_str")
    #qp.add_link("table_output_parser", "text2sql_prompt", dest_key="schema")
    #qp.add_chain(
    #    ["text2sql_prompt", "text2sql_llm", "sql_output_parser", "sql_retriever"]
    #)
    #qp.add_link(
    #    "sql_output_parser", "response_synthesis_prompt", dest_key="sql_query"
    #)
    #
    #qp.add_link(
    #    "sql_retriever", "response_synthesis_prompt", dest_key="context_str"
    #)
    #qp.add_link("input", "response_synthesis_prompt", dest_key="query_str")
    #qp.add_link("response_synthesis_prompt", "response_synthesis_llm")