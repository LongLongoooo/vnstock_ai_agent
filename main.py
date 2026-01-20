from app.agent.command_router import handle_command

print("VN Stock HippoRAG Agent")
print('Commands: /newadvice "ABC" | /updateadvice "ABC" | quit')

while True:
    cmd = input("> ").strip()
    if cmd in ("quit", "exit"):
        break
    try:
        result = handle_command(cmd)
        print(result)
    except Exception as e:
        print({"error": str(e)})
