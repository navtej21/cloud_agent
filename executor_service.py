import redis
import json
import time

from write_tool import write_file
from bash_tool import bash_tool
from edit_file_tool import edit_file

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

STREAM_REQUESTS = "tool_requests"
STREAM_RESULTS = "tool_results"
GROUP_NAME = "executor_group"
CONSUMER_NAME = "executor_1"
PROCESSED_SET_KEY="processed_tool_calls"

def read_file(path):
    try:
        with open(path, "r") as file:
            return file.read()
    except FileNotFoundError:
        return f"Error: file not found at path '{path}'"


try:
    r.xgroup_create(STREAM_REQUESTS, GROUP_NAME, id="0", mkstream=True)
except redis.exceptions.ResponseError as e:
    if "BUSYGROUP" not in str(e):
        raise  

print("Executor service running, waiting for tool requests...")


def process_message(message_id,fields):
    tool_call_id = fields["tool_call_id"]
    
    
    if (r.sismember(PROCESSED_SET_KEY,tool_call_id)):
        print(f"Skipping already-processed tool_call_id: {tool_call_id}")
        r.xack(STREAM_REQUESTS,GROUP_NAME,message_id)
        return
       
            
    tool_name = fields["tool_name"]
    tool_input = json.loads(fields["tool_input"])
    
    
    print(f"Executing:{tool_name} with input:{tool_input}")
    
    
    
    print(f"Executing: {tool_name} with {tool_input}")
    
    if tool_name == "read_file":
        result = read_file(tool_input["path"])
    elif tool_name == "write_file":
        result = write_file(tool_input["path"], tool_input["content"])
    elif tool_name == "bash_tool":
        result = bash_tool(tool_input["command"])
    elif tool_name == "edit_file":
        result = edit_file(tool_input["path"], tool_input["old_text"], tool_input["new_text"])
    else:
        result = f"Unknown tool: {tool_name}"
    
                # Publish the result back
    r.xadd(STREAM_RESULTS, {
                    "tool_call_id": tool_call_id,
                    "result": result
                })


    ## add inside the set            
    r.sadd(PROCESSED_SET_KEY,tool_call_id)

    
    # Acknowledge this message as processed
    r.xack(STREAM_REQUESTS, GROUP_NAME, message_id)
    
    print(f"Result sent back for {tool_call_id}")




## checking for the pending task in the redis stream
pending_check=r.xreadgroup(GROUP_NAME,CONSUMER_NAME,{STREAM_REQUESTS:"0"},count=1,block=5000)
for stream_name, entries in pending_check:
    if entries:
        print(f"Found {len(entries)} unacknowledged message(s) from a previous crash:")
        for message_id, fields in entries:
            process_message(message_id=message_id,fields=fields)


while True:
    # Block and wait for new messages, up to 5 seconds at a time
    messages = r.xreadgroup(GROUP_NAME, CONSUMER_NAME, {STREAM_REQUESTS: ">"}, count=1, block=5000)

    if not messages:
        continue

    for stream_name, entries in messages:
        for message_id, fields in entries:
            tool_call_id = fields["tool_call_id"]
            process_message(message_id=message_id,fields=fields)