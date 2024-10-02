import pandas as pd
from pathlib import Path
from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
   String,
    Integer,
)
import re
#The Import is adapted and imporved from https://docs.llamaindex.ai/en/stable/examples/pipeline/query_pipeline_sql/

data_dir = Path("./Data")
csv_files = sorted([f for f in data_dir.glob("*.csv")])
dfs = []
for csv_file in csv_files:
    print(f"processing file: {csv_file}")
    try:
        df = pd.read_csv(csv_file)
        # Entferne die Spalte 'timeRefTo'
        if 'timeRefTo' in df.columns:
            df.drop(columns=['timeRefTo'], inplace=True)
        
        # Umbenennen der Spalte 'timeRefFrom' in 'year' und Extrahieren des Jahres
        if 'timeRefFrom' in df.columns:
            df.rename(columns={'timeRefFrom': 'year'}, inplace=True)
            df['year'] = pd.to_datetime(df['year']).dt.year
            
        dfs.append(df)
    except Exception as e:
        print(f"Error parsing {csv_file}: {str(e)}")
        
        
def sanitize_column_name(input_string):
    
    # Remove special characters and spaces
    clean_string = re.sub('[^a-zA-Z0-9]', ' ', input_string)
    # Split the string into words
    words = clean_string.split()
    # Capitalize the first letter of each word except the first one
    camel_case_words = [words[0].lower()]
    camel_case_words.extend([word.capitalize() for word in words[1:]])
    # Join the words together to form the camel case string
    camel_case_string = ''.join(camel_case_words)

    return camel_case_string        
        
        
def create_table_from_dataframe(
    df: pd.DataFrame, table_name: str, engine, metadata_obj
):
    # Sanitize column names
    sanitized_columns = {col: sanitize_column_name(col) for col in df.columns}
    df = df.rename(columns=sanitized_columns)

    # Dynamically create columns based on DataFrame columns and data types
    columns = [
        Column(col, String if dtype == "object" else Integer)
        for col, dtype in zip(df.columns, df.dtypes)
    ]

    # Create a table with the defined columns
    table = Table(table_name, metadata_obj, *columns)

    # Create the table in the database
    metadata_obj.create_all(engine)

    # Insert data from DataFrame into the table
    with engine.connect() as conn:
        for _, row in df.iterrows():
            insert_stmt = table.insert().values(**row.to_dict())
            conn.execute(insert_stmt)
        conn.commit()        


engine = create_engine("sqlite:///chatDB.db")
metadata_obj = MetaData()
for idx, df in enumerate(dfs):
    tablename = sanitize_column_name(df.statementTitle[0])
    create_table_from_dataframe(df,tablename, engine, metadata_obj)