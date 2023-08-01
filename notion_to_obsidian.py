import time
import os
import re
from collections import defaultdict
from urllib.parse import unquote, quote
import zipfile

# Set the directory of your Notion markdown files
notion_dir = '/home/mawz/documents/external brain/export'
with zipfile.ZipFile('/home/mawz/documents/external brain/export.zip', 'r') as zip_ref:
    zip_ref.extractall(notion_dir)

# Store a map of old path to new path for files and directories separately
path_map_files = defaultdict(lambda: {'new_name': '', 'count': 0})
path_map_dirs = defaultdict(lambda: {'new_name': '', 'count': 0})

# Function to rename the file or directory, avoiding name collisions
def rename(old_name, path, path_map, is_file=False):
    base_name = old_name.rsplit(' ', 1)[0]
    new_name = base_name
    counter = path_map[old_name]['count']
    if is_file:
        while os.path.exists(os.path.join(path, new_name + '.md')):
            new_name = base_name + ' (' + str(counter) + ')'
            counter += 1
        path_map[old_name]['new_name'] = new_name + '.md'
    else:
        while os.path.exists(os.path.join(path, new_name)):
            new_name = base_name + ' (' + str(counter) + ')'
            counter += 1
        path_map[old_name]['new_name'] = new_name
    path_map[old_name]['count'] = counter
    return new_name

# Function to convert links from Notion to Obsidian
def convert_links():
    def replacer(match):
        link_text, link_url = match.groups()
        # Skip web links
        if link_url.startswith('http://') or link_url.startswith('https://'):
            return match.group(0)
        # Convert %20 back to space
        link_path_parts = unquote(link_url).split('/')
        new_link_path_parts = []
        for part in link_path_parts:
            if part in path_map_files:
                new_link_path_parts.append(path_map_files[part]['new_name'])
            elif part in path_map_dirs:
                new_link_path_parts.append(path_map_dirs[part]['new_name'])
            else:
                print(f'Unresolved link part: {part}')
                new_link_path_parts.append(part)  # leave unrecognized parts unchanged
        new_link_url = quote('/'.join(new_link_path_parts), safe='/&:,')
        return f'[{link_text}]({new_link_url})'
    return replacer

def convert_metadata(content):
    lines = content.split("\n")
    start_index = 2
    end_index = start_index
    for line in lines[start_index:]:
        if ":" in line:
            end_index += 1
        else:
            break
    converted_lines = ["---"] + lines[start_index:end_index] + ["---"] + lines[:start_index] + lines[end_index:]
    content = "\n".join(converted_lines)
    return content

# Process through the directory
for root, dirs, files in os.walk(notion_dir, topdown=False):
    # Renaming files
    for file in files:
        if file.endswith('.md'):
            new_file_name = rename(file, root, path_map_files, is_file=True)
            for i in range(3):  # Number of retries
                try:
                    os.rename(os.path.join(root, file), os.path.join(root, new_file_name + '.md'))
                    break
                except PermissionError as e:
                    print(f'PermissionError encountered for file {file}. Retry {i+1}/3')
                    time.sleep(1)  # Wait for 1 second before retrying

    # Renaming directories
    for name in dirs:
        new_name = rename(name, root, path_map_dirs)
        for i in range(3):  # Number of retries
            try:
                os.rename(os.path.join(root, name), os.path.join(root, new_name))
                break
            except PermissionError as e:
                print(f'PermissionError encountered for directory {name}. Retry {i+1}/3')
                time.sleep(1)  # Wait for 1 second before retrying

# Second pass: update file contents
for root, dirs, files in os.walk(notion_dir, topdown=False):
    # Update file contents
    for file in files:
        if file.endswith('.md'):
            with open(os.path.join(root, file), 'r') as f:
                content = f.read()
            content = convert_metadata(content)
            content = re.sub(r'\[([^\n]*)\]\((\S+)\)', convert_links(), content)
            with open(os.path.join(root, file), 'w') as f:
                f.write(content)
