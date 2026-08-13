
edit_file_tool={
    "name":"edit_file",
    "description":"Replaces an exact snippet of a text in a file with new text.the old text must match (with whitespaces) exactly once in the file.",
    "input_schema":{
        "type":"object",
        "properties":{
            "path":{
                "type":"string",
                "description":"The file path to edit"
            },
            "old_text":{
                "type":"string",
                "description":"The exact text to find and replace"
            },
            "new_text":{
                "type":"string",
                "description":"The text to replace with"
            }
        },
        "required":["path","old_text","new_text"]
    }
}


def edit_file(path,old_content,new_content):
    try:
        with open(path,"r") as file:
            content=file.read()


        count=content.count(old_content)

        if (count==0):
            return f"Error: old text not found in the path {path}.No changes Made"
        elif (count>1):
            return f"Error: old text found {count} times in the {path}.It must match exactly once.Provide more  surrounding context to make it unique"


        new_content=content.replace(content,new_content)

        with open(path,"w") as file:
            file.write(new_content)

        return f"Successfully Edited {path}"

    except FileNotFoundError:
        return f"File Not Found In The Path {path}"

    except Exception as e:
        return f"Error Editing The path {path}."
    