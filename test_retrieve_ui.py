from tools.retrieve_ui_reference import RetrieveUIReference

tool = RetrieveUIReference()

tests = [
    "vscode search icon",
    "brave back button",
    "youtube logo",
    "chatgpt add files button",
    "mail compose area",
    "mail compose button",
    "where is the window close icon",
    "unknown item"
]

for q in tests:
    print("\n=== QUERY:", q, "===")
    print(tool.run(q))
