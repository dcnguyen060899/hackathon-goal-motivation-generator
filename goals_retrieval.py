# -*- coding: utf-8 -*-
"""goals_retrieval.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/12e-zRC2DibIF2zBNTtODjt5M4kCkBdti

# dependencies
"""


import streamlit as st
import os
import sys
import openai

# initialize open ai agent model
openai.api_key = st.secrets["openai_api_key"]
# os.environ["ACTIVELOOP_TOKEN"] = ''

# Fetching secrets
os.environ['ACTIVELOOP_TOKEN'] = st.secrets["active_loop_token"]

# %%
# Imports
#
from typing import List

from llama_hub.tools.weather import OpenWeatherMapToolSpec
from llama_index import (
    Document,
    ServiceContext,
    SimpleDirectoryReader,
    VectorStoreIndex,
)
from llama_index.agent import OpenAIAgent
from llama_index.llms import OpenAI
from llama_index.multi_modal_llms import OpenAIMultiModal
from llama_index.output_parsers import PydanticOutputParser
from llama_index.program import MultiModalLLMCompletionProgram
from llama_index.tools import FunctionTool, QueryEngineTool, ToolMetadata
from llama_index.vector_stores import DeepLakeVectorStore
from pydantic import BaseModel

from llama_index.readers.deeplake import DeepLakeReader
import random
from llama_index.storage.storage_context import StorageContext

from typing import List, Tuple
import deeplake
from PIL import Image
from io import BytesIO
import re
import numpy as np
from IPython.display import display
import matplotlib.pyplot as plt
# from google.colab.patches import cv2_imshow
# import cv2
import pandas as pd
import ipywidgets as widgets
from llama_index import set_global_service_context
from llama_index import ServiceContext, VectorStoreIndex, SimpleDirectoryReader
from llama_index.embeddings import OpenAIEmbedding
from llama_index import set_global_service_context

# """# create database"""

import json
from llama_index import Document


# """# retrieve to-do list vector database"""

# """# load vector database"""

class Quotes(BaseModel):
    """Data model for Quote related to user's To-do List"""
    Quote: str
    Author: str


class QuoteList(BaseModel):
    """A list of Quotes Tarlor to User's To-do List for the model to use"""
    TodoList: List[Quotes]

reader = DeepLakeReader()
query_vector = [random.random() for _ in range(1536)]
documents = reader.load_data(
    query_vector=query_vector,
    dataset_path="hub://dcnguyen060899/quote_of_the_day",
    limit=5,
)

dataset_path = 'quote_of_the_day'
vector_store = DeepLakeVectorStore(dataset_path=dataset_path, overwrite=True)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

embed_model = OpenAIEmbedding()
service_context = ServiceContext.from_defaults(embed_model=embed_model)

set_global_service_context(service_context)

# %%
# Inventory query engine tool
#
inventory_index = VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context,
    service_context=service_context
)

todolist_query_engine = inventory_index.as_query_engine(output_cls=QuoteList)

todolist_query_engine_tool = QueryEngineTool(
    query_engine=todolist_query_engine,
    metadata=ToolMetadata(
        name="todolist_query_engine",
        description=(
            "Useful for finding quote of the day in our vector database"
            "Usage: input: Give me a motivational quote base on my to-do list of the day"
            "Output: quote of the day tailor to the user to-do list"
            "Always ask the user to-do list as input when using this tool"
        ),
    ),
)

# """# ask the user input and input quote of the day"""

# Define a Pydantic model for the immigration response
class MotivationResponse(BaseModel):
    quote_of_the_day: str = ""
    user_tasks: str = ""
    motivation: str = ""
    important_date: str = ""

def response_to_user_input(nationality: str, todolist_query_engine_tool: str, user_todo_list: str):
    """
    Combining everything ranging from combing quote of the day to
    """

    # Define the GPT-4 model
    gpt4_language_model = OpenAI(language_model="gpt-4")

    # Define prompt template based on nationality and user query
    prompt_template_str = f"""
    You are an expert in motivational mentoring and fluent in multiple languages, including the language preferred by someone from {nationality}.
    The quote from {todolist_query_engine_tool} will provide you some context on the quote choice tailor to the user to-do list.
    Provide detailed information in a clear and user-friendly manner about the following query:

    "{user_todo_list}"

    The response should be tailored to the nationality and language preferences of the user.
    Note: If user ask in other languages other than English, response in their languages
    Example:
    >>> User's Input:
        "To-do-list": "Codio Activity 1.1: pandas Dataframes",
        "time": "2:30 PM",
        "date": "Monday, Feb 1, 2024"

    >>> Response:
    Quote:...
    Author:...
    Motivation:...
    Important Date:...

    """

    # Create a function to generate response based on the user's query and nationality
    motivation_completion_program = MultiModalLLMCompletionProgram.from_defaults(
        output_parser=PydanticOutputParser(MotivationResponse),
        prompt_template_str=prompt_template_str,
        llm=gpt4_language_model,
        verbose=True,
    )
    response = motivation_completion_program()

    return response

# Tool for immigration assistance based on nationality and user query
response_to_user_input = FunctionTool.from_defaults(fn=response_to_user_input)

# """# initiate the agents"""

llm = OpenAI(model="gpt-4", temperature=0.7)

agent = OpenAIAgent.from_tools(
  system_prompt = """You are a mentor. Your role is to motivate the user basedase on their to-do list. Your response has to be specific,
   motivate them not only with quotes but include with a personal detail touch like what time they shoukld do their work, etc.

  First ask what their to-do list first for some context. There here are the function logic you should access:

  >>> Ask the user for to-do list input. Once you get the context of what the user task for the day:
        >>> Motivate user with one of our quotes of the day from our vector database (todolist_query_engine_tool)

  >>> Once you retrieve user input, pass the user input and quote retrieve from the database directly to response_to_user_input and generate the final response.
  """,
  tools=[
      todolist_query_engine_tool,
      response_to_user_input,
    ],
    llm=llm,
  verbose=True)

# Create the Streamlit UI components
st.title('👔 InspireMe: Goals & Quotes Generator" 🧩')

# Session state for holding messages
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Display past messages
for message in st.session_state.messages:
    st.chat_message(message['role']).markdown(message['content'])

# Custom CSS to inject for styling
st.markdown("""
<style>
.big-font {
    font-size:30px !important;
}
.small-font {
    font-size:12px !important;
}
.streamlit-file-uploader {
    max-width: 200px;
    max-height: 200px;
}
</style>
""", unsafe_allow_html=True)

# Use columns to create a layout
col1, col2 = st.columns([1, 4])

with col1:
    # File uploader in a smaller column
    uploaded_file = st.file_uploader("", type=['csv', 'txt', 'jpg', 'jpeg', 'png'])

with col2:
    # Main input and application interface
    prompt = st.text_input('', 'Input your prompt here')


if prompt:
   # Directly query the OpenAI Agent
   st.chat_message('user').markdown(prompt)
   st.session_state.messages.append({'role': 'user', 'content': prompt})

   response = agent.chat(prompt)
   final_response = response.response

   st.chat_message('assistant').markdown(final_response)
   st.session_state.messages.append({'role': 'assistant', 'content': final_response})
