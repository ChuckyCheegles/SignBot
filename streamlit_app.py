import streamlit as st
from openai import OpenAI
from openai.types.beta.assistant_stream_event import ThreadMessageDelta
from openai.types.beta.threads.text_delta_block import TextDeltaBlock

OPENAI_API_KEY = "sk-streamlitfrontend-OBWaH004XTdzoSuZtl6KT3BlbkFJ2ks5hAgn12iuLnUOgxBl"
ASSISTANT_ID = "asst_RNSt9CLC6nVtDmMa7iDbVKxf"

allowed_files = {
    "pdf",
    "docx",
    "doc",
    "txt"
}


# Initialise the OpenAI client, and retrieve the assistant
client = OpenAI(api_key=OPENAI_API_KEY)
try:
    assistant = client.beta.assistants.retrieve(assistant_id=ASSISTANT_ID)
except Exception as e:
    st.error(f"Failed to retrieve OpenAI Assistant: {e}")
    print(f"Failed to retrieve OpenAI Assistant: {e}")
    st.stop()

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# Initialise session state to store conversation history locally to display on UI
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def update_key():
    st.session_state.uploader_key += 1

# Title
st.title("SignBot - Testing Platform")
st.markdown(":red-background[SignBot is an experimental program. Responses may not be accurate. Try asking SignBot to verify it's results.]")

# Display messages in chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Textbox and streaming process
file_uploader = st.file_uploader("Upload a File!", type=allowed_files, accept_multiple_files=False, label_visibility="collapsed", key=f"uploader_{st.session_state.uploader_key}")

if user_query := st.chat_input("Ask SignBot A Question!"):
    if "thread_id" not in st.session_state:
        try:
            thread = client.beta.threads.create()
            st.session_state.thread_id = thread.id
            print(thread.id)
        except Exception as e:
            st.error(f"Failed to create thread: {e}")
            print(f"Failed to create thread: {e}")
            st.stop()

    with st.chat_message("user", avatar=":material/person:"):
        st.markdown(user_query)

    st.session_state.chat_history.append({"role": "user", "content": user_query})

    #Upload file to Assistant
    try:
        if file_uploader is not None:
            #Upload File
            file = client.files.create(
                file=file_uploader,
                purpose='assistants'
            )
            #Create array to store file IDs
            files_array = {
                f"{file.id}",
            }
            print(f"File Uploaded to OpenAI Assistant Succesfully with ID:{file.id}")            
            #Create Vector Store and attach File ID
            vector_store = client.beta.vector_stores.create(
                name=f"Vector Store for Thread ID: {st.session_state.thread_id}",
                file_ids=[files_array]
            )
            print(f"Vector Store Created Succesfully with ID:{vector_store.id}")

            #Get Vector Store ID and Attach it to current Thread ID
            client.beta.threads.update(
                st.session_state.thread_id,
                tool_resources={
                    "file_search": {
                        "vector_store_ids": vector_store.id,
                    }
                }
            )
            print(f"Vector Store Attached Succesfully to Thread ID:{st.session_state.thread_id}")
            update_key()
        else:
            print("No File Loaded")
    except Exception as e:
        st.error(f"Failed to attach file to thread: {e}")
        print(f"Failed to attach file to thread: {e}")



    try:
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=user_query
        )
        print(f"Message attached to thread ID: {st.session_state.thread_id}")
    except Exception as e:
        st.error(f"Failed to attach message to thread: {e}")
        print(f"Failed to attach message to thread: {e}")
        st.stop()

    with st.chat_message("SignBot", avatar=":material/terminal:"):
        try:
            stream = client.beta.threads.runs.create(
                thread_id=st.session_state.thread_id,
                assistant_id=ASSISTANT_ID,
                stream=True
            )
            print(f"Message received with thread ID: {st.session_state.thread_id}")
            
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


