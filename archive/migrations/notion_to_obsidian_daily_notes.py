import os
import re

def modify_journal_entries_in_place(notion_folder_path, excluded_files):
    # Define patterns
    metadata_start_pattern = r'^---$'
    date_pattern = r'^Date:\s*(\d{4}-\d{2}-\d{2})$'
    title_pattern = r'^#\s*(.*)$'

    # Iterate through Notion files
    for filename in os.listdir(notion_folder_path):
        if filename in excluded_files:
            continue

        filepath = os.path.join(notion_folder_path, filename)
        with open(filepath, 'r') as file:
            content = file.readlines()

        inside_metadata = False
        date_str = None
        location = None
        modified_content = []
        for line in content:
            if re.match(metadata_start_pattern, line):
                inside_metadata = not inside_metadata
                modified_content.append(line)
                continue

            if inside_metadata:
                date_match = re.match(date_pattern, line)
                if date_match:
                    date_str = date_match.group(1)
                    modified_content.append(line)
                continue

            title_match = re.match(title_pattern, line)
            if title_match and not location:
                location = title_match.group(1)
            else:
                modified_content.append(line)

        # If no title (location) is found, fallback to the filename
        if not location:
            location = filename[:-3]

        # Modify the metadata to include location
        metadata_index = modified_content.index('---\n')
        modified_content.insert(metadata_index + 2, f'Location: {location}\n')

        # Write back the modified content
        with open(filepath, 'w') as file:
            file.writelines(modified_content)

        # Rename the file to the Obsidian daily notes format if date is found
        if date_str:
            new_filename = date_str + '.md'
            new_filepath = os.path.join(notion_folder_path, new_filename)
            os.rename(filepath, new_filepath)

modify_journal_entries_in_place('/mnt/d/personal cloud/external brain/Daily Journal', ["Seattle", "Daily Entry.md", "Gratuity Daily Entry.md", "TheMe System Daily Entry.md", "Untitled.md"])
