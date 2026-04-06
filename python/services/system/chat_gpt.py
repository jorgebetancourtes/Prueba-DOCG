# python/services/system/query_service.py

import pandas as pd
import sqlparse
from openai import OpenAI
from sqlalchemy import text
from python.models.modelos import db
from config import *
import os
from flask import session

if os.getenv("OPENAI_API_KEY"):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class QueryService:

    def __init__(self):
        self.engine = db.engine
        self.schema_cache = None
        self.allowed_tables = None

    # ----------------------------------------------------------------------
    # Load DB schema & allowed tables (cached)
    # ----------------------------------------------------------------------
    def load_schema(self):
        if self.schema_cache:
            return self.schema_cache

        query = """
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position;
        """

        df = pd.read_sql(query, self.engine)

        # Filter out omitted tables
        df = df[~df["table_name"].isin(OMIT_TABLES)]
        self.allowed_tables = df["table_name"].unique().tolist()

        # Format schema text for LLM
        schema_text = ""
        for table in self.allowed_tables:
            schema_text += f"\nTable {table}:\n"
            sub = df[df["table_name"] == table]
            for _, row in sub.iterrows():
                schema_text += f" - {row['column_name']} ({row['data_type']})\n"

        self.schema_cache = schema_text
        return self.schema_cache

    # ----------------------------------------------------------------------
    # Convert natural language question → SQL
    # ----------------------------------------------------------------------
    def generate_sql(self, question: str) -> str:
        schema = self.load_schema()
        if GPT_PROMPT:
            prompt = GPT_PROMPT.format(schema=schema,question=question,id_usuario=session['id_usuario'])
        else:
            prompt = f"""
You are an expert PostgreSQL assistant.
Convert the user question into ONE safe read-only SQL query.

Hard Requirements (must ALWAYS be followed):

FOREIGN KEY JOIN RULES (STRICT — APPLY ONLY TO FOREIGN KEYS OF THE MAIN TABLE)

1. A 'foreign key column' is any column whose name starts with id_ in the MAIN TABLE ONLY.
   Do NOT apply this rule to other tables.

2. For EVERY foreign key column in the main table, you MUST:
   - Add a LEFT JOIN to the referenced table
   - Select ONE human-readable label from that table

3. INNER JOIN is FORBIDDEN ONLY for foreign keys of the MAIN TABLE.
   INNER JOIN IS ALLOWED for non-FK joins when appropriate.

4. Never show raw foreign key IDs in the SELECT.
   Replace them with a user-friendly label column.
   If no obvious label exists, select id_visualizacion.

5. The correct join pattern for MAIN-TABLE FKs is:
       LEFT JOIN <referenced_table> AS <alias>
              ON <main_table>.<fk_column> = <alias>.id

6. You MUST join and label ALL foreign keys of the main table, even if the user question does not mention them.


SELECT RULES:
- Include the main table's id_visualizacion as 'ID <table>'.
- Include one human-readable label column for each joined FK table.
- Include useful direct columns from the main table.
- Never SELECT *.
- Never return raw ID columns.

FILTERING RULES:
- Never filter using raw IDs unless the user explicitly provides one.
- When filtering by names or text fields, use LOWER(col) = LOWER('value') or ILIKE.
- Always qualify all columns with their table names.


VALIDATION:
If the question cannot be answered with a read-only SQL query using the provided schema, return EXACTLY:
INVALID_QUESTION

Database schema:
{schema}

User question: "{question}".

Return ONLY SQL OR `INVALID_QUESTION`. Nothing else.
"""

        res = client.responses.create(
            model="gpt-4.1-mini",
            input=[{"role": "user", "content": prompt}]
        )

        raw_sql = res.output[0].content[0].text.strip()
        sql = self.clean_llm_sql(raw_sql)
        return sql

    # ----------------------------------------------------------------------
    # Validate SQL (safety)
    # ----------------------------------------------------------------------
    def clean_llm_sql(self, sql: str):
        # Remove markdown backticks
        sql = sql.replace("```sql", "")
        sql = sql.replace("```", "")
        return sql.strip()    
    
    def validate_sql(self, sql: str):

        lower = sql.lower()

        forbidden = ["insert", "update", "delete", "drop", "alter", "truncate"]
        if any(word in lower for word in forbidden):
            raise ValueError("Se intento generar un querie no permitido. Favor de intentar nuevamente.")

        if self.allowed_tables:
            if not any(table.lower() in lower for table in self.allowed_tables):
                raise ValueError("Se intento generar un querie no permitido. Favor de intentar nuevamente.")

    # ----------------------------------------------------------------------
    # Execute SQL safely
    # ----------------------------------------------------------------------
    def execute_sql(self, sql: str) -> pd.DataFrame:
        try:
            with self.engine.connect() as conn:
                df = pd.read_sql(text(sql), conn)
            return df
        except Exception as e:
            raise ValueError(f"❌ Database error: {e}")

    # ----------------------------------------------------------------------
    # Optional: LLM Answer Summary
    # ----------------------------------------------------------------------
    def summarize(self, df: pd.DataFrame) -> str:

        table = df.head(20).to_markdown()

        prompt = f"""
Summarize this result in a business-friendly explanation. And make any recommendations you see fit.
Do NOT include SQL.

{table}
"""

        res = client.responses.create(
            model="gpt-4.1-mini",
            input=[{"role": "user", "content": prompt}]
        )

        return res.output[0].content[0].text.strip()

    # ----------------------------------------------------------------------
    # Full Query Pipeline
    # ----------------------------------------------------------------------
    def ask(self, question: str):

        sql = self.generate_sql(question)
        if sql == "INVALID_QUESTION":
            raise ValueError("La pregunta no es válida o no tiene sentido lógico. Por favor reformúlala.")
        self.validate_sql(sql)

        df = self.execute_sql(sql)
        df = df.fillna(0)

        if df.empty:
            answer = "No results found."
        elif df.shape == (1, 1):
            answer = f"Result: {df.iloc[0, 0]}"
        else:
            answer = self.summarize(df)

        return {
            "sql": sql,
            "data": df,
            "answer": answer,
        }