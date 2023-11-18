import base64
import os
import re
from io import BytesIO
from dotenv import load_dotenv
import openai
import streamlit as st
from langchain.callbacks import get_openai_callback
from streamlit_chat import message
from lida import Manager, TextGenerationConfig, llm 
from PIL import Image
import pandas as pd

class LidaAgent:

    @staticmethod
    def count_tokens_agent(agent, query):
        with get_openai_callback() as cb:
            result = agent(query)
            st.write(f'Spent a total of {cb.total_tokens} tokens')

        return result
    
    def __init__(self):
        pass

    def visualize_response(self, uploaded_file_content, query):
        load_dotenv()
        openai.api_key = os.getenv('OPENAI_API_KEY')
        lidaai = Manager(text_gen=llm("openai"))
        textgen_config = TextGenerationConfig(n=1, temperature=0.5, model="gpt-3.5-turbo-0301", use_cache=True)

        path_to_save = "filename.csv"
        uploaded_file_content.to_csv(path_to_save, index=False)

        summary = lidaai.summarize("filename.csv", summary_method="default", textgen_config=textgen_config)
        textgen_config = TextGenerationConfig(n=1, temperature=0.2, use_cache=True)
        charts = lidaai.visualize(summary=summary, goal=query, textgen_config=textgen_config, library="seaborn")  

        if charts:
            img_base64_string = charts[0].raster
            img = base64_to_image(img_base64_string)
            return img
        else:
            st.warning("No charts found.")
            return None


    def summarize_response(self, uploaded_file_content):
        load_dotenv()
        openai.api_key = os.getenv('OPENAI_API_KEY')
        lidaai = Manager(text_gen=llm("openai"))
        textgen_config = TextGenerationConfig(n=1, temperature=0.5, model="gpt-3.5-turbo-0301", use_cache=True)

        # Save DataFrame to CSV file
        path_to_save = "filename.csv"
        uploaded_file_content.to_csv(path_to_save, index=False)

        summary = lidaai.summarize("filename.csv", summary_method="default", textgen_config=textgen_config)

        goals = lidaai.goals(summary, n=2, textgen_config=textgen_config)

        imgs = []
        for goal in goals:
            library = "seaborn"
            textgen_config = TextGenerationConfig(n=1, temperature=0.2, use_cache=True)
            charts = lidaai.visualize(summary=summary, goal=goal, textgen_config=textgen_config, library=library)  
            img_base64_string = charts[0].raster
            img = base64_to_image(img_base64_string)
            imgs.append(img)

        return summary, goals, imgs

    def process_agent_thoughts(self, captured_output):
        thoughts = captured_output.getvalue()
        cleaned_thoughts = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', thoughts)
        cleaned_thoughts = re.sub(r'\[1m>', '', cleaned_thoughts)
        return cleaned_thoughts

    def display_agent_thoughts(self, cleaned_thoughts):
        with st.expander("Display the agent's thoughts"):
            st.write(cleaned_thoughts)

    def update_chat_history(self, query, result):
        st.session_state.chat_history.append(("user", query))
        st.session_state.chat_history.append(("agent", result))

    def display_chat_history(self):
        for i, (sender, message_text) in enumerate(st.session_state.chat_history):
            if sender == "user":
                message(message_text, is_user=True, key=f"{i}_user")
            else:
                message(message_text, key=f"{i}")

def base64_to_image(base64_string):
    # Decode the base64 string
    byte_data = base64.b64decode(base64_string)
    
    # Use BytesIO to convert the byte data to an image
    return Image.open(BytesIO(byte_data))
