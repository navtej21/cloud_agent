import subprocess

bash_file_tool={
    "name":"bash_tool",
    "description":"Executes a shell command on Windows (cmd.exe syntax, e.g. 'dir' not 'ls', 'cd' not 'pwd') and returns its output.",
    "input_schema":{
        "type":"object",
        "properties":{
            "command":{
                "type":"string",
                "description":"the bash command to execute"
            }
        }
        ,
        "required":["command"]
    }
}

def bash_tool(command):
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        output = result.stdout
        if result.stderr:
            output += "\nSTDERR:\n" + result.stderr
        return output if output.strip() else "(command ran with no output)"
    except subprocess.TimeoutExpired:
        return "Error: command timed out after 30 seconds"
    except Exception as e:
        return f"Error running command: {e}"