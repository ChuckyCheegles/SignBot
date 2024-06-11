import streamlit as st
from openai import OpenAI
from openai.types.beta.assistant_stream_event import ThreadMessageDelta
from openai.types.beta.threads.text_delta_block import TextDeltaBlock

OPENAI_API_KEY = "sk-streamlitfrontend-OBWaH004XTdzoSuZtl6KT3BlbkFJ2ks5hAgn12iuLnUOgxBl"
ASSISTANT_ID = "asst_RNSt9CLC6nVtDmMa7iDbVKxf"

# Initialise the OpenAI client, and retrieve the assistant
client = OpenAI(api_key=OPENAI_API_KEY)
try:
    assistant = client.beta.assistants.retrieve(assistant_id=ASSISTANT_ID)
except Exception as e:
    st.error(f"Failed to retrieve OpenAI Assistant: {e}")
    print(f"Failed to retrieve OpenAI Assistant: {e}")
    st.stop()

# Initialise session state to store conversation history locally to display on UI
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Title
st.title("SignBot - Testing Platform")

# Display messages in chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Textbox and streaming process
if user_query := st.chat_input("Ask SignBot A Question!"):
    if "thread_id" not in st.session_state:
        try:
            thread = client.beta.threads.create()
            st.session_state.thread_id = thread.id
        except Exception as e:
            st.error(f"Failed to create thread: {e}")
            print(f"Failed to create thread: {e}")
            st.stop()

    with st.chat_message("user"):
        st.markdown(user_query)

    st.session_state.chat_history.append({"role": "user", "content": user_query})
    
    try:
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=user_query
        )
    except Exception as e:
        st.error(f"Failed to attach message to thread: {e}")
        print(f"Failed to attach message to thread: {e}")
        st.stop()

    with st.chat_message("assistant"):
        try:
            stream = client.beta.threads.runs.create(
                thread_id=st.session_state.thread_id,
                assistant_id=ASSISTANT_ID,
                stream=True
            )
        except Exception as e:
            st.error(f"Failed to create stream: {e}")
            print(f"Failed to create stream: {e}")
            st.stop()
        
        assistant_reply_box = st.empty()
        
        assistant_reply = ""

        try:
            for event in stream:
                if isinstance(event, ThreadMessageDelta):
                    if isinstance(event.data.delta.content[0], TextDeltaBlock):
                        assistant_reply_box.empty()
                        assistant_reply += event.data.delta.content[0].text.value
                        assistant_reply_box.markdown(assistant_reply)
        except Exception as e:
            st.error(f"Error during streaming: {e}")
            print(f"Error during streaming: {e}")

        st.session_state.chat_history.append({"role": "assistant", "content": assistant_reply})