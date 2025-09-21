import os
import re


TARGET_EXTENSIONS = [".py", ".js", ".jsx", ".css"]


COMMENT_PATTERNS = {
    ".py": [r"
    ".js": [r"//.*", r"/\*[\s\S]*?\*/"],  
    ".jsx": [r"//.*", r"/\*[\s\S]*?\*/"], 
    ".css": [r"/\*[\s\S]*?\*/"]           
}

def remove_comments_from_text(text, extension):
    """Remove comments from text based on file extension."""
    patterns = COMMENT_PATTERNS.get(extension, [])
    for pattern in patterns:
        text = re.sub(pattern, "", text)
    return text

def process_file(filepath):
    """Read, strip comments, and overwrite file."""
    ext = os.path.splitext(filepath)[1]
    if ext not in TARGET_EXTENSIONS:
        return
    
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        original_text = f.read()
    
    cleaned_text = remove_comments_from_text(original_text, ext)
    
    if cleaned_text != original_text:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(cleaned_text)
        print(f"Cleaned comments in {filepath}")

def walk_project(root="."):
    """Walk through all files and clean comments."""
    for subdir, _, files in os.walk(root):
        for file in files:
            filepath = os.path.join(subdir, file)
            process_file(filepath)

if __name__ == "__main__":
    project_path = "."  
    walk_project(project_path)
    print("✅ All comments removed from project files.")
