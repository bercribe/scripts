import os
import requests
import json
import yaml
import re

DATABASE_DIRECTORY = "/mnt/d/personal cloud/external brain/Life Wiki/Reading List/Media"
GOOGLE_API_KEY = "AIzaSyDPkoCwl5M3Gp5xax67aFoWy0vcTXH3Ayw"
SEARCH_ENGINE_ID = "83e23b7080cf541e7"

def get_first_search_result(query, api_key, cx):
    # Call the Google Custom Search JSON API
    response = requests.get(f'https://www.googleapis.com/customsearch/v1?key={api_key}&cx={cx}&q={query}')

    data = json.loads(response.text)

    # Get the first search result
    if 'items' in data:
        return data['items'][0]['link']
    else:
        return None

def get_and_update_metadata(directory_path, api_key, cx):
    # Go through each .md file in the directory
    i = 0
    for filename in os.listdir(directory_path):
        if filename.endswith('.md'):
            filepath = os.path.join(directory_path, filename)

            with open(filepath, 'r+') as file:
                content = file.read()

                # Check if the file has metadata at the top
                if content.startswith('---'):
                    # Find the second occurrence of '---' which marks the end of metadata
                    end_metadata = [m.end() for m in re.finditer("---", content)]

                    if len(end_metadata) > 1:
                        end_metadata_index = end_metadata[1]

                        # Parse the metadata
                        metadata = yaml.load(content[3:end_metadata_index-3], Loader=yaml.FullLoader)

                        # If a 'Link' field doesn't exist, get the link and add it
                        if 'Link' not in metadata:
                            # Use the filename without the extension as the query
                            name = os.path.splitext(filename)[0]

                            # Perform the search
                            url = get_first_search_result(name, api_key, cx)

                            if url:
                                # Add the link to the metadata
                                metadata['Link'] = url

                                # Rewrite the metadata to the file
                                file.seek(0)
                                file.write('---\n')
                                yaml.dump(metadata, file)
                                file.write('---')

                                # Write the remaining content
                                file.write(content[end_metadata_index:])
                            
                            i += 1
                            if i >= 1000:
                                break
    print(f'{i} entries updated')

# Usage:
get_and_update_metadata(DATABASE_DIRECTORY, GOOGLE_API_KEY, SEARCH_ENGINE_ID)
