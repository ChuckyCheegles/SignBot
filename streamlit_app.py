import streamlit as st
import openai
from pathlib import Path

"""
# Welcome to SignBot!
SignBot is an AI tool designed to help sign manufacturers plan, design, and fabricate signage!
It can read architectural plans and relay information or just give general tips on any question you can ask!
"""


# Configuration
openai.api_key = st.secrets.api_key()
assistant_id = st.secrets.ass_id()
client = None

try:
    client = openai.Client()
except openai.APIError as e:
    st.error(f"OpenAI API Error: {e}")
except openai.APIConnectionError as e:
    st.error(f"Connection Error: {e}")
except openai.APIStatusError as e:
    st.error(f"Status Error: {e.status_code} - {e.response}")
except Exception as e:
    st.error(f"General Error: {e}")

# Function to interact with OpenAI Assistant and handle file uploads
def get_assistant_response(assistant_id, input_text, attached_files):
    if client is None:
        raise ValueError("OpenAI client is not initialized.")
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
            try:
                with st.spinner('Waiting for response from assistant...'):
                    response = get_assistant_response(assistant_id, user_input, uploaded_files)
                    st.success("Response received!")
                    st.write(response)
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.error("Please provide a query.")

if __name__ == "__main__":
    main()