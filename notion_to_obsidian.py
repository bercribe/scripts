import time
import os
import re
from collections import defaultdict
from urllib.parse import unquote, quote
import zipfile
import csv

# Set the directory of your Notion markdown files
notion_dir = '/home/mawz/documents/external brain/export'
with zipfile.ZipFile('/home/mawz/documents/external brain/export.zip', 'r') as zip_ref:
    zip_ref.extractall(notion_dir)

# Store a map of old path to new path for files and directories separately
path_map_files = defaultdict(lambda: {'new_name': '', 'count': 0})
path_map_dirs = defaultdict(lambda: {'new_name': '', 'count': 0})

# Function to rename the file or directory, avoiding name collisions
def rename(old_name, path, path_map, extension=""):
    base_name = old_name.rsplit(' ', 1)[0]
    new_name = base_name
    counter = path_map[old_name]['count']
    while os.path.exists(os.path.join(path, new_name + extension)):
        new_name = base_name + ' (' + str(counter) + ')'
        counter += 1
    path_map[old_name]['new_name'] = new_name + extension
    path_map[old_name]['count'] = counter
    return new_name + extension

def convert_database(file, root):
    data_folder_name = file.removesuffix('.csv').removesuffix('_all')
    if data_folder_name in path_map_dirs:
        converted_data_folder_name = path_map_dirs[data_folder_name]["new_name"]
    else:
        print(f'Unresolved table data source: {data_folder_name}')
        converted_data_folder_name = data_folder_name.rsplit(' ', 1)[0]

    csv_file = os.path.join(root, file)
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        headers = next(reader)  # get the column headers
    # Process headers to match the dataview format
    def convert_header(h):
        if h == "Name":
            converted = "file.name"
        else:
            converted = h.lower().replace(" ", "-").replace("/", "")
        if converted == h:
            return h
        return f'{converted} as "{h}"'
    headers = [convert_header(h) for h in headers]

    # Build the dataview query
    relpath = os.path.relpath(root, notion_dir).replace("\\", "/")
    dataview_path = f'{relpath}/{converted_data_folder_name}'
    query = '```dataview\n'
    query += 'table ' + ', '.join(headers) + '\n'
    query += f'from "{dataview_path}"\n'
    query += f'where file.folder = "{dataview_path}"\n'
    query += '```\n'

    extension = file.removeprefix(data_folder_name).removesuffix('.csv') + '.md'
    new_file_name = rename(file, root, path_map_files, extension)
    output_file = os.path.join(root, new_file_name)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(query)
    os.remove(os.path.join(root, file))

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

def convert_metadata(content, file_name):
    if content[0] != '#':
        return content
    lines = content.split("\n")
    start_index = 2
    end_index = start_index
    for line in lines[start_index:]:
        if ":" in line:
            end_index += 1
        else:
            break
    converted_lines = []
    if start_index != end_index:
        converted_lines.append("---")
        converted_lines.extend(lines[start_index:end_index])
        converted_lines.append("---")
    if lines[0] != f'# {file_name.removesuffix(".md")}':
        converted_lines.extend(lines[:start_index])
    converted_lines.extend(lines[end_index:])
    return "\n".join(converted_lines)

def convert_asides(content):
    lines = content.split("\n")
    converted_lines = []
    in_aside = False
    for line in lines:
        if line == "<aside>":
            in_aside = True
            line = ">[!aside]"
        elif line == "</aside>":
            in_aside = False
            line = ""
        elif in_aside:
            line = f'>{line}'
        converted_lines.append(line)
    return "\n".join(converted_lines)

# Process through the directory
for root, dirs, files in os.walk(notion_dir, topdown=False):
    # Renaming files
    for file in files:
        if file.endswith('.md'):
            new_file_name = rename(file, root, path_map_files, '.md')
            for i in range(3):  # Number of retries
                try:
                    os.rename(os.path.join(root, file), os.path.join(root, new_file_name))
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

for root, dirs, files in os.walk(notion_dir):
    for file in files:
        if file.endswith('.csv'):
            convert_database(file, root)

# Second pass: update file contents
for root, dirs, files in os.walk(notion_dir):
    # Update file contents
    for file in files:
        if file.endswith('.md'):
            with open(os.path.join(root, file), 'r') as f:
                content = f.read()
            content = re.sub(r'\[([^\n]*)\]\((\S+)\)', convert_links(), content)
            content = convert_metadata(content, file)
            content = convert_asides(content)
            with open(os.path.join(root, file), 'w') as f:
                f.write(content)
