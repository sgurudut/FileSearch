from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import time
import threading
import sys

app = FastAPI()

# Initialize OpenAI client
client = OpenAI(api_key="API_KEY")# chage API key)

assistant = client.beta.assistants.create(
    name="Event info assistant",
    instructions="You are a helpful assistant providing info to conference attendees. Use your knowledge base to answer questions about the conference.",
    model="gpt-4o",
    tools=[{"type": "file_search"}]
)

# Create a vector store called "Event Details"
vector_store = client.vector_stores.create(name="Event Details")

# Ready the files for upload to OpenAI
file_paths = ["ConferenceTestFile.pdf"]
file_streams = [open(path, "rb") for path in file_paths]

# Upload the files and add them to the vector store
file_batch = client.vector_stores.file_batches.upload_and_poll(
    vector_store_id=vector_store.id, files=file_streams
)

assistant = client.beta.assistants.update(
    assistant_id=assistant.id,
    tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
)


# Define a Pydantic model for the POST request body
class UserInput(BaseModel):
    user_input: str


@app.get("/")
async def root():
    return {"message": "Welcome to the Event Info Assistant API!"}


@app.post("/assistant")
async def assistant_logic(user_input: UserInput):
    """Handle user input and return assistant's response."""
    
    # Create a thread for the assistant to process the request
    thread = client.beta.threads.create(
        messages=[
            {"role": "user", "content": user_input.user_input}
        ]
    )

    # Use the create and poll SDK helper to create a run and poll the status of the run until it's in a terminal state.
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id, assistant_id=assistant.id
    )

    # Retrieve the messages from the assistant
    messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))

    # Get the content of the response and handle annotations
    message_content = messages[0].content[0].text
    annotations = message_content.annotations
    citations = []
    for index, annotation in enumerate(annotations):
        message_content.value = message_content.value.replace(annotation.text, f"[{index}]")
        if file_citation := getattr(annotation, "file_citation", None):
            cited_file = client.files.retrieve(file_citation.file_id)
            citations.append(f"[{index}] {cited_file.filename}")

    return {"response": message_content.value}


# Optional: Loading indicator simulation (if you want to simulate a long-running task)
def loading_indicator():
    while True:
        for dot_count in range(1, 4):
            sys.stdout.write("." * dot_count)
            sys.stdout.flush()
            time.sleep(0.5)  # Adjust time to control the speed of the dots
            sys.stdout.write("\r")  # Clear the line
            sys.stdout.flush()

def long_running_task():
    # Simulate a long task (replace with your actual task)
    time.sleep(10)  # Replace this with your task that takes time
    print("\nTask completed!")


# Start loading indicator in a separate thread if needed
loading_thread = threading.Thread(target=loading_indicator)
loading_thread.daemon = True  # Ensure the thread exits when the main program ends
loading_thread.start()


# To run FastAPI:
# Use `uvicorn` from the command line:
# uvicorn app:app --reload
# uvicorn fast_api_test:app --reload
