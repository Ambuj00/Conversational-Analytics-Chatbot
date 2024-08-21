import os
import openai
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine

def generate_schema(df):
    schema = ""
    for col in df.columns:
        dtype = str(df[col].dtype)
        schema += f"{col} ({dtype}), "
    return schema.rstrip(', ')

def construct_prompt(natural_language_query, schema):
    prompt = f"""
You are an AI assistant that converts natural language to SQL queries.

Here is the database schema:
Table: data
Columns:
{schema}

Generate a SQL query for the following request:
"{natural_language_query}"

Only provide the SQL query.
    """
    return prompt

def generate_sql_query(natural_language_query, schema):
    prompt = construct_prompt(natural_language_query, schema)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # Use 'gpt-4' if available
        messages=[
            {"role": "system", "content": "You are an AI assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150,
        temperature=0,
    )
    sql_query = response.choices[0].message["content"].strip()
    return sql_query

def execute_sql_query(df, sql_query):
    try:
        # Create in-memory SQLite database
        engine = create_engine('sqlite://', echo=False)
        df.to_sql('data', con=engine, index=False, if_exists='replace')

        # Print SQL query for debugging
        print(f"Executing SQL query: {sql_query}")

        # Execute query
        result_df = pd.read_sql_query(sql_query, con=engine)
        return result_df
    except Exception as e:
        return f"Error executing SQL query: {e}"

def main():
    # Custom CSS for advanced styling
    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(135deg, #1e1e1e 0%, #2c2c2c 100%);
            color: #e0e0e0;
            font-family: 'Arial', sans-serif;
        }
        .stTitle {
            font-size: 2.5em;
            font-weight: 700;
            color: #00bfff;
            text-align: center;
            padding: 20px 0;
        }
        .stTextInput, .stTextArea {
            border-radius: 10px;
            border: 1px solid #444;
            padding: 12px;
            background-color: #333;
            color: #e0e0e0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            transition: border-color 0.3s;
        }
        .stTextInput:focus, .stTextArea:focus {
            border-color: #00bfff;
            box-shadow: 0 0 0 0.2rem rgba(0,191,255,0.25);
        }
        .stButton {
            background-color: #00bfff;
            color: #fff;
            border: none;
            border-radius: 10px;
            padding: 12px 24px;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            transition: background-color 0.3s;
        }
        .stButton:hover {
            background-color: #0080ff;
        }
        .stSidebar {
            background: #2c2c2c;
            color: #e0e0e0;
            border-right: 1px solid #444;
        }
        .stWarning, .stError {
            color: #dc3545;
        }
        .stSuccess {
            color: #28a745;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("CSV Data Query Chatbot")

    # Sidebar for OpenAI API key
    st.sidebar.header("OpenAI API Key")
    openai_api_key = st.sidebar.text_input("Enter your OpenAI API key:", type="password", placeholder="Your OpenAI API Key")

    # File uploader
    uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file)

        # Correct column names if necessary
        df.columns = [
            "Page title and screen name", "Country", "Views", 
            "Users", "Views per user", "Average engagement time", 
            "Event count", "Key events"
        ]
        
        st.write("**Data Loaded:**")
        st.dataframe(df.head())  # Show first few rows of the uploaded CSV

        # Filter by country
        country_filter = st.selectbox("Select Country to Filter:", df["Country"].unique())
        filtered_df = df[df["Country"] == country_filter]
        st.write(f"**Filtered Data for {country_filter}:**")
        st.dataframe(filtered_df)

        # Main screen layout for query
        st.write("**Enter Your Query:**")
        user_query = st.text_area("Type your query here:", "What are the total views for the USA?")

        if openai_api_key:
            openai.api_key = openai_api_key  # Set the API key

            if st.button("Submit Query"):
                with st.spinner('Generating SQL query...'):
                    schema = generate_schema(filtered_df)  # Use filtered data
                    sql_query = generate_sql_query(user_query, schema)
                    st.write(f"**Generated SQL Query:**\n```sql\n{sql_query}\n```")

                with st.spinner('Executing SQL query...'):
                    result = execute_sql_query(filtered_df, sql_query)  # Use filtered data

                    if isinstance(result, pd.DataFrame) and not result.empty:
                        st.write("**Query Results:**")
                        st.dataframe(result)
                    elif isinstance(result, pd.DataFrame) and result.empty:
                        st.warning("The query executed successfully but returned no results.")
                    else:
                        st.error(result)
        else:
            st.warning("Please enter your OpenAI API key to proceed.")

if __name__ == "__main__":
    main()