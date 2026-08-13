
## write the file function
def write_file(path,content):
    try:
        with open(path,"w") as file:
            file.write(content)
        return "Written the content successfully"
    except FileNotFoundError:
        return f"File Not Found in this path:${path}"


## tool description
write_file_tool={
    "name":"write_file",
    "description":"write content to the file in the given path.",
    "input_schema":{
        "type":"object",
        "properties":{
            "path":{
                "type":"string",
                "description":"the path to write the file"
            },
            "content":{
                "type":"string",
                "description":"the content to write in the file"
            }
        },
        "required":["path","content"]
    }
}



