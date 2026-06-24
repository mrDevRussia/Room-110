import os

EXCLUDE_DIRS = {'.git', '.github', '__pycache__', 'node_modules', 'build', 'target', 'dist'}
EXCLUDE_FILES = {'package-lock.json', 'yarn.lock', 'project_context.md'}
ALLOWED_EXTENSIONS = {'.rs', '.py', '.js', '.ts', '.c', '.cpp', '.h', '.go', '.json', '.md', '.br'}

def build_repository_context(root_dir="."):
    context_output = "# REPOSITORY CONTEXT AND ARCHITECTURE\n\n"
    
    # 1. Map the directory tree
    context_output += "## Directory Structure\n```text\n"
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        level = root.replace(root_dir, '').count(os.sep)
        indent = ' ' * 4 * (level)
        context_output += f"{indent}{os.path.basename(root)}/\n"
        sub_indent = ' ' * 4 * (level + 1)
        for f in files:
            if f not in EXCLUDE_FILES and os.path.splitext(f)[1] in ALLOWED_EXTENSIONS:
                context_output += f"{sub_indent}{f}\n"
    context_output += "
```\n\n"

    # 2. Append file contents
    context_output += "## Source Code Files\n\n"
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            if file in EXCLUDE_FILES or os.path.splitext(file)[1] not in ALLOWED_EXTENSIONS:
                continue
                
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, root_dir)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                context_output += f"### File: {relative_path}\n"
                context_output += f"```{os.path.splitext(file)[1][1:]}\n"
                context_output += f"{content}\n"
                context_output += "
```\n\n"
            except Exception as e:
                print(f"Skipping {relative_path} due to error: {e}")
                
    return context_output

if __name__ == "__main__":
    context = build_repository_context()
    with open("project_context.md", "w", encoding="utf-8") as out:
        out.write(context)
    print("Project context aggregated successfully in project_context.md")
