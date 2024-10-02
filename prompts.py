from llama_index.core.prompts import PromptTemplate
from utils import create_level_values_string

#adapted from llama_index.core.prompts
RESPONSE_SYNTHESIS_PROMPT = (
    "Do not use escape characters or newline characters; write everything in one line. "
    "Synthesize a response based on the provided query results without repeating the query or SQL query in the response."
    "Query: {query_str}\n"
    "SQL: {sql_query}\n"
    "SQL Response: {context_str}\n"
    "Response: "
    "Only use these values to form the response: {result_str} . Do not use other values. "
    "Maintain the original number format from ({result_str})"
    "Do NOT use words like Million, billion or their translation. Only use the result"
    "Do NOT use Mio. mrd. or other abbreviations"
    "Do Not change units like kwh to mwh"
    "Example: value1 + value2 + value3 = result. "
    "If asked to sum numbers, add them exactly as they are presented, e.g., for the question 'How much petrol did x use in 2020?' the answer is '100+200+150=450'. "
    "When calculating sums, such as '594581 + 20021404 + 46580698 + 6982 + 5123421 + 426783', the result should be '72753869'. "
    "Only use the values provided in the response, and if specific values are requested, use only those. "
    "Ensure you use the correct unit, like liters or kWh, and do NOT round numbers; use exact values from the data. "
    "All responses should be in German. Verify the accuracy of your calculations."
    "Only use these values: {result_str}. in that format and after Antwort: Do Not add any comma, or points."
    "Do not add any commas, points, or any other symbols to the result. The number must be presented exactly as {result_str} without any modifications."
    
    "Here is the required format, each taking one line:\n\n"
    "Ergebnis: {result_str} \n"
    "Antwort: \n"
    


)

#adapted from llama_index.core.prompts
TEXT_TO_SQL_PROMPT = (
"Do NOT use capital letters for values taken from the question: use diesel instead of Diesel."
"Given an input question, first create a syntactically correct {dialect} SQL query to run."
"Then look at the results of the query and return the answer."
"Order the results by a relevant column to return the most interesting examples in the database."

"Never query for all the columns from a specific table; only ask for a few relevant columns given the question."

"Pay attention to use only the column names that you can see in the schema description {schema}."
"Be careful to not query for columns that do not exist."
"Pay attention to which column is in which table."
"Qualify column names with the table name when needed."
"Use explicit JOINs instead of implicit JOINs for clarity. "

"When asked questions like 'How much diesel did Skalamotors use in 2020?' use the SUM function, e.g., SUM(consumption)."
"Always try to use SUM when getting data for a year or for a country."

"Follow these guidelines when writing the SQL query:"

"Identify the tables and columns required for the query based on the schema."
"Determine the relationships between the tables and use explicit JOINs to connect them. "
"Use WHERE clauses to filter the data based on the question."
"Use aggregate functions like SUM, COUNT, AVG as needed to compute the required results. "
"Group the results appropriately to ensure accurate aggregation."

"Here is another example:\n "
"SELECT SUM(consumption) FROM  fuelConsumption WHERE level1 = 'SkalaMotors AG' AND level2 = 'China'; \n"
"SELECT SUM(consumption) FROM electricity WHERE level1 = 'SkalaMotors AG' AND level2 = 'Germany'\n\n"

"Handle multiple questions in a single query carefully by ensuring each part of the question is addressed separately."
"For questions with multiple conditions or asking for multiple values, use subqueries or CTEs (Common Table Expressions) to break down the problem into simpler parts."

"Example question with multiple conditions:\n"
"Question: Wie viel benzin und wie viel diesel wurde 2021 von SkalaEBikes verbraucht?\n"
"This is just an example use the Question: {query_str}. Generate a new SQL."
"SQLQuery:\n"
"DieselConsumption AS (\n"
" SELECT SUM(consumption) AS total_diesel\n"
" FROM fuelConsumption\n"
" WHERE level3 = 'SkalaEBikes' AND fuel_type = 'diesel' AND year = 2021\n"
"),\n"
"PetrolConsumption AS (\n"
" SELECT SUM(consumption) AS total_petroln\n"
" FROM fuelConsumption\n"
" WHERE level3 = 'SkalaEBikes' AND fuel_type = 'petrol' AND year = 2021\n"
")\n"
"SELECT total_diesel, total_benzin\n"
"FROM DieselConsumption, PetrolConsumption;\n\n"

"Use similar structure to handle complex questions and joins.\n"



"Check again to only use the column names from the {schema}"

"Here is the required format, each taking one line:\n\n"
"Question: {query_str}\n"
"SQLQuery: \n\n"


"Do not use any \ or / in the query."
"Do NOT use \\n in the SQL"
"Do not use an Other Format. "
"Do always put the SQLQuery or SQLStatement after SQLQuery: "
"Only use tables listed below.\n"
"{schema}\n\n"
)


#adapted and imporved from https://docs.llamaindex.ai/en/stable/examples/pipeline/query_pipeline_sql/
TABLE_INFO_PROMPT = """\
Give me a summary of the table with the following JSON format.
- Only use str and do NOT create any lists
- The table must be the same name as in the Data
- Do not display the Data
- Describe the levels like level1 according to their content and indicate which one, for example, represents a country, which one represents a company, and which one represents a subsidiary
- Check if a level represents company names (endings like AG,GmbH) then its a company
- Check if a level represents countrys (germany, usa ...) then its a country
- Check if a level represents variations of the same Name like (CarMotorAG,CarPetrolAG,CarMotorEGmbH) then it is a subsidiary
- Give a list of all unique values for each Level
- Make exact description of the levels and do not give two examples like company name or country
Do NOT make the table name one of the following: {exclude_table_name_list}

Table:
{table_str}

Summary: """



def create_text_to_sql_prompt(engine,table_infos):
    levels = create_level_values_string(table_infos)
    text_to_sql_prompt = str
    text_to_sql_prompt = """Look up what the main company is and what the subsidiary companys are to get the level right
    Make sure to identify subsidiary companys, if the name differs from the main Company its likely a subsidiary company
    Make sure to use the right values for the right level. """
    for level, value in levels.items():
            if value:  
                 text_to_sql_prompt+=(f"For {level} only use these values: {value}")
    else:
        text_to_sql_prompt+=(f"{level} is empty. ")
    text_to_sql_prompt+=(TEXT_TO_SQL_PROMPT)
    print(text_to_sql_prompt)
    return PromptTemplate(text_to_sql_prompt, prompt_type="text_to_sql").partial_format(dialect=engine.dialect.name)

def create_response_synthesis_prompt():
    return PromptTemplate(RESPONSE_SYNTHESIS_PROMPT)

def get_table_info_prompt():
    return TABLE_INFO_PROMPT