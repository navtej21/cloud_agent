import anthropic

client=anthropic.Anthropic()

response=client.messages.create(
    model='claude-sonnet-4-5',
    max_tokens=1024,
    messages=[
        {"role":"user","content":"Say hello and tell what is 2+2 is"}
    ]
)


print(response.content[0].text)
print(response.stop_reason)
