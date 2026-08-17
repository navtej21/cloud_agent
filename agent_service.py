import anthropic
import redis
import json
import uuid
import time

from write_tool import write_file_tool
from edit_file_tool import edit_file_tool
from bash_tool import bash_file_tool
from dotenv import load_dotenv

client = anthropic.Anthropic()
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

STREAM_REQUESTS = "tool_requests"
STREAM_RESULTS = "tool_results"
STREAM_TASKS = "agent_tasks"
TASK_GROUP_NAME = "agent_group"
TASK_CONSUMER_NAME = "agent_1"

last_result_id = "0"

read_file_tool = {
    "name": "read_file",
    "description": "Reads and returns the content of the file at the given path.",
    "input_schema": {
        "type": "object",
        "properties": {"path": {"type": "string", "description": "The file path to read"}},
        "required": ["path"]
    }
}


def send_tool_request(tool_call_id, tool_name, tool_input):
    r.xadd(STREAM_REQUESTS, {
        "tool_call_id": tool_call_id,
        "tool_name": tool_name,
        "tool_input": json.dumps(tool_input)
    })


def wait_for_result(tool_call_id, timeout_seconds=30):
    global last_result_id
    start = time.time()
    while time.time() - start < timeout_seconds:
        messages = r.xread({STREAM_RESULTS: last_result_id}, count=10, block=1000)
        for stream_name, entries in messages:
            for message_id, fields in entries:
                last_result_id = message_id
                if fields["tool_call_id"] == tool_call_id:
                    return fields["result"]
    return "Error: tool result timed out"


# --- Consumer group setup for agent_tasks, same pattern as executor_service.py ---
try:
    r.xgroup_create(STREAM_TASKS, TASK_GROUP_NAME, id="0", mkstream=True)
except redis.exceptions.ResponseError as e:
    if "BUSYGROUP" not in str(e):
        raise


def wait_for_task():
    # 1. First check for anything left pending from a previous crash
    pending = r.xreadgroup(TASK_GROUP_NAME, TASK_CONSUMER_NAME, {STREAM_TASKS: "0"}, count=1)
    for stream_name, entries in pending:
        if entries:
            message_id, fields = entries[0]
            print(f"Reclaiming unacknowledged task from a previous crash: {message_id}")
            return message_id, fields["sessionId"], fields["tasks"]

    # 2. Otherwise, block and wait for a genuinely new task
    while True:
        messages = r.xreadgroup(TASK_GROUP_NAME, TASK_CONSUMER_NAME, {STREAM_TASKS: ">"}, count=1, block=5000)
        for stream_name, entries in messages:
            for message_id, fields in entries:
                return message_id, fields["sessionId"], fields["tasks"]


while True:
    print("waiting for tasks")
    task_message_id, sessionId, task = wait_for_task()
    print(f"Received task for session {sessionId}: {task}")

    messages = [{"role": "user", "content": task}]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            tools=[read_file_tool, write_file_tool, bash_file_tool, edit_file_tool],
            messages=messages
        )

        if response.stop_reason == "end_turn":
            for block in response.content:
                if block.type == "text":
                    print("Claude:", block.text)
            break

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            for block in response.content:
                if block.type == "tool_use":
                    print(f"Requesting: {block.name} with {block.input}")

                    send_tool_request(block.id, block.name, block.input)
                    result = wait_for_result(block.id)

                    print("Got result:", result)

                    messages.append({
                        "role": "user",
                        "content": [{"type": "tool_result", "tool_use_id": block.id, "content": result}]
                    })

    # Task fully complete — now safe to acknowledge
    r.xack(STREAM_TASKS, TASK_GROUP_NAME, task_message_id)
    print(f"Task for session {sessionId} complete. Waiting for next task...")