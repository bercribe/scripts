import os
import csv
import yaml
import re

def get_metadata_and_write_to_csv(directory_path):
    # Initialize the list to hold all CSV data
    csv_data = []

    # Go through each .md file in the directory
    for filename in os.listdir(directory_path):
        if filename.endswith('.md'):
            filepath = os.path.join(directory_path, filename)

            with open(filepath, 'r') as file:
                content = file.read()

                # Check if the file has metadata at the top
                if content.startswith('---'):
                    # Find the second occurrence of '---' which marks the end of metadata
                    end_metadata = [m.end() for m in re.finditer("---", content)]

                    if len(end_metadata) > 1:
                        end_metadata_index = end_metadata[1]

                        # Parse the metadata
                        metadata = yaml.load(content[3:end_metadata_index-3], Loader=yaml.FullLoader)

                        # If a 'Link' field exists, add it to the CSV data
                        if 'Link' in metadata:
                            tags = []
                            for key, val in metadata.items():
                                if key not in ['Type', 'Status', 'Link', 'Has cover art']:
                                    tags.append(val)
                            csv_data.append({
                                'folder': f'{metadata["Type"]}/{metadata["Status"]}',
                                'url': metadata['Link'],
                                'title': os.path.splitext(filename)[0],
                                'note': content[end_metadata_index:],
                                'tags': ', '.join(tags),
                                'created': '',
                            })

    # Write the CSV data to a file
    with open('raindrop_import.csv', 'w', newline='') as csvfile:
        fieldnames = ['folder', 'url', 'title', 'note', 'tags', 'created']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(csv_data)

# Usage:
get_metadata_and_write_to_csv('/mnt/d/personal cloud/external brain/Life Wiki/Reading List/Media')
