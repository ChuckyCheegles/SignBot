import streamlit as st
import openai
import os
from pathlib import Path

"""
# Welcome to SignBot!
SignBot is an AI tool designed to help sign manufacturers plan, design, and fabricate signage!
It can read architectural plans and relay information or just give general tips on any question you can ask!
"""


# Configuration
openai.api_key = os.getenv("OPENAI_API_KEY")
assistant_id = os.getenv("OPENAI_ASSISTANT_ID")
client = openai.OpenAI()

# Function to interact with OpenAI Assistant and handle file uploads
def get_assistant_response(assistant_id, input_text, attached_files):
    # Prepare file attachments
    files = []
    for uploaded_file in attached_files:
        files.append(uploaded_file)

    # Upload files if there are any
    if files:
        batch = openai.file.create(file=files)
        file_ids = [file['id'] for file in batch['data']]
    else:
        file_ids = None

    # Prepare messages
    messages = [
        {"role": "user", "content": input_text}
    ]

    # Create and poll run
    run = client.beta.threads.runs.create_and_poll(
        thread_id="thread_id_placeholder",
        assistant_id=assistant_id,
        messages=messages,
        files=file_ids
    )

    return run

def main():
    st.title("OpenAI Assistant")

    st.header("Upload Files")
    uploaded_files = st.file_uploader("Upload files for the assistant to analyze", accept_multiple_files=True)

    st.header("Enter Your Query")
    user_input = st.text_area("Type your query here")

    if st.button("Get Response"):
        if user_input:
            with st.spinner('Waiting for response from assistant...'):
                response = get_assistant_response(assistant_id, user_input, uploaded_files)
                st.success("Response received!")
                st.write(response)
        else:
            st.error("Please provide a query.")

if __name__ == "__main__":
    main()