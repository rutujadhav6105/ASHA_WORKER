import os
import re

def replace_in_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = re.sub(r'\.withOpacity\(([^)]+)\)', r'.withValues(alpha: \1)', content)
    
    if content != new_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def main():
    root_dir = 'c:\\FlutterProject\\frontend\\lib'
    modified_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.dart'):
                file_path = os.path.join(root, file)
                if replace_in_file(file_path):
                    modified_files.append(file_path)
    
    print(f"Modified {len(modified_files)} files:")
    for f in modified_files:
        print(f)

if __name__ == '__main__':
    main()
