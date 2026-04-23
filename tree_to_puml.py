import sys
import re


def is_file(name):
    return "." in name and not name.startswith(".")


def parse_tree(lines):
    stack = []
    root = {"name": None, "children": []}

    for line in lines:
        line = line.rstrip()

        # Skip empty lines and summary line
        if not line or re.match(r"\d+ directories?, \d+ files?", line):
            continue

        indent = len(re.match(r'^[\s│]*', line).group(0))
        name = re.sub(r'^[\s│├└─]+', '', line)

        if name == ".":
            continue  # skip root

        node = {"name": name, "children": []}

        while stack and stack[-1][0] >= indent:
            stack.pop()

        if stack:
            stack[-1][1]["children"].append(node)
        else:
            root["children"].append(node)

        stack.append((indent, node))

    return root


def emit(node, indent=1):
    space = "  " * indent

    # Node has children → package
    if node["children"]:
        s = f'{space}package "{node["name"]}"  {{\n'
        for child in node["children"]:
            s += emit(child, indent + 1)
        s += f"{space}}}\n"
        return s

    # Leaf node
    if is_file(node["name"]):
        return f'{space}file "{node["name"]}" \n'
    else:
        return f'{space}folder "{node["name"]}" \n'


if __name__ == "__main__":
    lines = sys.stdin.readlines()
    tree = parse_tree(lines)

    print("@startuml\n")
    print("skinparam folder {")
    print("    BackgroundColor #fcdca9")
    print("}")
    print("")
    print("skinparam file {")
    print("    BackgroundColor #dbdff5")
    print("}")
    print("")

    for child in tree["children"]:
        print(emit(child), end="")

    print("@enduml")