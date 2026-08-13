import anthropic

client = anthropic.Anthropic()


from write_tool import write_file
from write_tool import write_file_tool
from bash_tool import bash_tool
from bash_tool import bash_file_tool
from edit_file_tool import *


from github_auth import clone_repo,get_installation_token,push_repo,pull_repo


# 1. Tell Claude what tool is available
read_file_tool = {
    "name": "read_file",
    "description": "Reads and returns the content of the file at the given path.",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The file path to read"
            }
        },
        "required": ["path"]
    }
}



# 2. The ACTUAL implementation of the tool
def read_file(path):

    try:
        with open(path, "r") as file:
            return file.read()
    except FileNotFoundError:
        return f"Error: file not found at path '{path}'"




token,expires_at=get_installation_token()
clone_result=clone_repo(token,"navtej21/QuickNotesAI","cloned_repo")


print("token",token)
print("expires_at",expires_at)
print("clone_result",clone_result)
# 3. Keep track of the conversation

task=input("Enter The Task:")
messages = [
    {
        "role": "user",
        "content": task
    }
]



# 4. Agent loop
while True:

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        tools=[read_file_tool,write_file_tool,bash_file_tool,edit_file_tool],
        messages=messages
    )

    print("stop_reason:", response.stop_reason)

    # Claude is finished
    if response.stop_reason == "end_turn":

        for block in response.content:
            if block.type == "text":
                print("Claude:", block.text)

        break


    # Claude wants to use a tool
    if response.stop_reason == "tool_use":

        # Add Claude's response to the conversation
        messages.append({
            "role": "assistant",
            "content": response.content
        })

        # Look through Claude's response for tool calls
        for block in response.content:

            if block.type == "tool_use":

                print("Claude wants to call:", block.name)
                print("Arguments:", block.input)
                print("Tool ID:", block.id)

                # Actually execute the Python function
                if block.name == "read_file":

                    result = read_file(block.input["path"])

                    print("Tool result:")
                    print(result)

                    # Send the result back to Claude
                    messages.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result
                            }
                        ]
                    })

                if block.name =="write_file":
                    result=write_file(block.input["path"],block.input["content"])

                    print("Tool result:")
                    print(result)

                    messages.append({
                        "role":"user",
                        "content":[
                            {
                                "type":"tool_result",
                                "tool_use_id":block.id,
                                "content":result
                            }
                        ]
                    })

                if block.name=="bash_tool":
                    result=bash_tool(block.input["command"])

                    print("Tool result:")
                    print(result)

                    messages.append(
                        {
                            "role":"user",
                            "content":[{
                                "type":"tool_result",
                                "tool_use_id":block.id,
                                "content":result
                            }
                            ]
                        }
                    )


                if block.name == "edit_file":
                    result = edit_file(block.input["path"], block.input["old_text"], block.input["new_text"])
                    print("Tool result:")
                    print(result)
                    messages.append({
                        "role": "user",
                        "content": [{"type": "tool_result","tool_use_id": block.id,"content": result}]})



# ## push the results
# push_result = push_repo(repo_path="cloned_repo",repo_full_name="navtej21/QuickNotesAI",token=token, branch="agent-changes")
# print("push_result:",push_result)

## pull the requests
pr_result = pull_repo(token=token, repo_full_name="navtej21/QuickNotesAI", branch="agent-changes", title="Automated agent change", body="Made via agent")
print("PR result:", pr_result)