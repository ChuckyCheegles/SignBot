import streamlit as st
from openai import OpenAI
from openai.types.beta.assistant_stream_event import ThreadMessageDelta
from openai.types.beta.threads.text_delta_block import TextDeltaBlock
from openai import AssistantEventHandler
import googlemaps
import requests
import json
import pytz

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
ASSISTANT_ID = st.secrets["ASSISTANT_ID"]
GOOGLE_API = st.secrets["GOOGLE_API"]

allowed_files = {
    "pdf",
    "docx",
    "doc",
    "txt"
}


# Initialise the OpenAI client, and retrieve the assistant
client = OpenAI(api_key=OPENAI_API_KEY)
try: # Attempt to retrieve assistant
    assistant = client.beta.assistants.retrieve(assistant_id=ASSISTANT_ID)
except Exception as e: # Error handling for assistant retrieval
    st.error(f"Failed to retrieve OpenAI Assistant: {e}")
    print(f"Failed to retrieve OpenAI Assistant: {e}")
    st.stop()

if "uploader_key" not in st.session_state: # Save whether the uploader has a file in it or not
    st.session_state.uploader_key = 0

# Initialise session state to store conversation history locally to display on UI
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def update_key(): # Function for upload handling
    st.session_state.uploader_key += 1
    
def get_current_location(): # Gets the user's current location
    geolocation_result = gmaps.geolocate()
    if 'location' in geolocation_result and 'lat' in geolocation_result['location'] and 'lng' in geolocation_result['location']:
        lat = geolocation_result['location']['lat']
        long = geolocation_result['location']['lng']
    else:
        print("Could not determine the latitude and longitude.")
        return "Location could not be determined."
    
    reverse_geocode_result = gmaps.reverse_geocode((lat, long))
    
    if reverse_geocode_result and 'formatted_address' in reverse_geocode_result[0]:
        return reverse_geocode_result[0]['formatted_address']
    else:
        return "Address could not be determined."

def get_latitude(): # Gets the user's current latitude
    geolocation_result = gmaps.geolocate()
    if 'location' in geolocation_result and 'lat' in geolocation_result['location']:
        lat = geolocation_result['location']['lat']
        return lat
    else:
        print("Could not determine latitude.")
        return "Could not determine latitude."
    
def get_longitude(): # Gets the user's current longitude
    geolocation_result = gmaps.geolocate()
    if 'location' in geolocation_result and 'lng' in geolocation_result['location']:
        long = geolocation_result['location']['lng']
        return long
    else:
        print("Could not determine the longitude.")
        return "Could not determine the longitude."

def get_current_time(): # Gets the current time
    return datetime.now().isoformat()

def message_builder(user_query): # Builds a message from the user
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

#EventHandler class
class EventHandler(AssistantEventHandler):
  def on_text_delta(self, delta, snapshot):
    print(delta.value, end="", flush=True)
      
  def on_tool_call_created(self, tool_call):
    print(f"\nassistant > {tool_call.type}\n", flush=True)
  
  def on_event(self, event):
    # Retrieve events that are denoted with 'requires_action'
    # since these will have our tool_calls
    if event.event == 'thread.run.requires_action':
      run_id = event.data.id  # Retrieve the run ID from the event data
      self.handle_requires_action(event.data, run_id)
 
  def handle_requires_action(self, data, run_id):
    tool_outputs = []
     
    for tool in data.required_action.submit_tool_outputs.tool_calls:
      
      print(f"Tool Name: {json.dumps(tool.function.name)}")
      print(f"Tool Arguments:{json.dumps(tool.function.arguments)}")
      
      arguments = json.loads(tool.function.arguments) if isinstance(tool.function.arguments, str) else tool.function.arguments
      
      print(f"Parsed Arguments:{arguments}")
      
      # get_time function handler
      if tool.function.name == "get_time":
        timezone_str = arguments.get("time_zone", "UTC")
        try:
          timezone = pytz.timezone(timezone_str)
        except pytz.UnknownTimeZoneError:
          tool_outputs.append({"tool_call_id": tool.id, "output": "Timezone unrecognized. Please use a timezone in the pytz python library."})
          print("Timezone reported by assistant is not valid.")
        now = datetime.now(timezone)
        time_format = arguments.get("format", "12hr")
        if time_format == "12hr":
          current_time = now.strftime('%H:%M:%S')
        else:
          current_time = now.strftime('%H:%M:%S')
        tool_outputs.append({"tool_call_id": tool.id, "output": f"The current time in {timezone_str} is: {current_time}"})
        print(f"TOOL OUTPUT: The current time in {timezone_str} is: {current_time}\n")
        print(" ")
        print("-----------------------------------------------")
      
      # get_date function handler
      elif tool.function.name == "get_date":
        timezone_str = arguments.get("time_zone", "UTC")

        try:
          timezone = pytz.timezone(timezone_str)
        except pytz.UnknownTimeZoneError:
          tool_outputs.append({"tool_call_id": tool.id, "output": "Timezone unrecognized. Please use a timezone in the pytz python library."})
          print("Timezone reported by assistant is not valid.")
          
        now = datetime.now(timezone)
        current_date = now.strftime('%d:%m:%Y')
        tool_outputs.append({"tool_call_id": tool.id, "output": f"The current time in {timezone_str} is: {current_date}"})
        print(f"TOOL OUTPUT: The current date in {timezone_str} is: {current_date}\n")
        print(" ")
        print("-----------------------------------------------")
      
      # catch all for invalid tool calls. Sends the assistant a response saying the tool was invalid so it won't use it again during current thread.
      else:
        tool_outputs.append({"tool_call_id": tool.id, "output": "Function Invalid. Wrong Script?"})
        print("Tool Call Was Invalid")
        
    # Submit all tool_outputs at the same time
    self.submit_tool_outputs(tool_outputs, run_id)
 
  def submit_tool_outputs(self, tool_outputs, run_id):
    # Use the submit_tool_outputs_stream helper
    with client.beta.threads.runs.submit_tool_outputs_stream(
      thread_id=self.current_run.thread_id,
      run_id=self.current_run.id,
      tool_outputs=tool_outputs,
      event_handler=EventHandler(),
    ) as stream:
      for text in stream.text_deltas:
        pass



# Title
st.title("SignBot")
st.markdown(":purple-background[SignBot is an experimental program. Responses may not be accurate. Try asking SignBot to verify it's results.]")
file_uploader = st.file_uploader("Upload a File!", type=allowed_files, accept_multiple_files=False, label_visibility="collapsed", key=f"uploader_{st.session_state.uploader_key}")
st.divider()
# Display messages in chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])



def run_assistant():
    user_data = f"<Location: {get_current_location()} Latitude:{get_latitude()} Longitude:{get_longitude()}><Query Time:{get_current_time()}>" # User data part of query
    
    event_handler = EventHandler()
    
    if "thread_id" not in st.session_state:
        try:
            thread = client.beta.threads.create()
            st.session_state.thread_id = thread.id
            print(f"Created New Thread with ID: {thread.id}")
        except Exception as e:
            st.error(f"Failed to create thread: {e}")
            print(f"Failed to create thread: {e}")
            st.stop()
    
    try:
        if file_uploader is not None:
            # Upload File
            file = client.files.create(
                file=file_uploader,
                purpose='assistants'
            )
            # Create array to store file IDs
            files_array = [f"{file.id}"]  # This should be a simple list of strings
            print(f"File Uploaded to OpenAI Assistant Successfully with ID: {file.id}")            

            # Create Vector Store and attach File ID
            vector_store = client.beta.vector_stores.create(
                name=f"Vector Store for Thread ID: {st.session_state.thread_id}",
                file_ids=files_array,  # Passing simple list
                expires_after={
                    "anchor": "last_active_at",
                    "days": 1
                },
            )

            if "vector_store_id" not in st.session_state:
               st.session_state.vector_store_id = [vector_store.id]

            print(f"Vector Store Created Successfully with ID: {st.session_state.vector_store_id}")

            # Get Vector Store ID and Attach it to current Thread ID
            try:
                client.beta.threads.update(
                    st.session_state.thread_id,
                    tool_resources={
                        "file_search": {
                            "vector_store_ids": [vector_store.id], 
                        }
                  }
                )
            except Exception as e:
                print(f"Vector Store Failed to Attach to Thread ID: {st.session_state.thread_id} for reason: {e}")
                st.error(f"Vector Store Failed to Attach to Thread ID: {st.session_state.thread_id} for reason: {e}")
                st.error("SignBot will continue to answer queries but it's responses may be unreliable. Try starting a new thread!")

            print(f"Vector Store Attached Successfully to Thread ID: {st.session_state.thread_id}")
            update_key()
        else:
            print("No File Loaded")
    except Exception as e:
        st.error(f"Failed to attach file to thread: {e}")
        print(f"Failed to attach file to thread: {e}")
        
    



if user_query := st.chat_input("Ask SignBot A Question!"):
    
    with st.chat_message("user", avatar=":material/person:"):
        st.markdown(user_query)

    st.session_state.chat_history.append({"role": "user", "content": user_query})

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
            with client.beta.threads.runs.stream(
                    thread_id=thread.id,
                    assistant_id=assistant.id,
                    event_handler=event_handler
            ) as stream:
                stream.until_done()
                print("")
                
        except Exception as e:
            st.error(f"Error during streaming: {e}")
            print(f"Error during streaming: {e}")
        
        st.session_state.chat_history.append({"role": "SignBot", "content": assistant_reply})



if __name__ == "__main__":
    run_assistant()