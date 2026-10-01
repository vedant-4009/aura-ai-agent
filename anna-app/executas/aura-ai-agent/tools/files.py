from pathlib import Path

def list_files(folder: str = ".") -> str:
    path = Path(folder).resolve()
    if not path.exists():
        return f"Folder not found: {path}"

    items = []
    for item in sorted(path.iterdir()):
        kind = "DIR" if item.is_dir() else "FILE"
        items.append(f"{kind}: {item.name}")

    return "\n".join(items) if items else "Folder is empty."

def read_file(file_path: str) -> str:
    path = Path(file_path).resolve()

    if not path.exists():
        return f"File not found: {path}"

    if not path.is_file():
        return f"Not a file: {path}"

    try:
        return path.read_text(encoding="utf-8")[:20000]
    except Exception as exc:
        return f"Could not read file: {exc}"
