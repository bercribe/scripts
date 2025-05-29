import csv
import requests
import json

csv_file = "Raindrop.io-Export.csv"
api_key = ""
endpoint = "https://karakeep.judgement.mawz.dev"

bookmarks = 0
folders = dict()
with open(csv_file) as file:
    reader = csv.reader(file)
    for row in reader:
        if not row or row[0] == "id":
            continue

        bookmarks += 1

        title = row[1]
        note = row[2]
        excerpt = row[3]
        url = row[4]
        # max length = 40 char
        folder = row[5][-40:]
        tags = row[6]
        created = row[7]
        
        headers = {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Authorization': 'Bearer ' + api_key
        }

        payload = json.dumps({
          "title": title,
          "archived": False,
          "favourited": False,
          "note": note,
          "summary": excerpt,
          "createdAt": created,
          "type": "link",
          "url": url,
          # "precrawledArchiveId": "string"
        })

        response = requests.request("POST", f"{endpoint}/api/v1/bookmarks", headers=headers, data=payload)
        response.raise_for_status()

        bookmarkId = json.loads(response.text)["id"] 

        # folder
        if folder not in folders:
            print(f"adding folder: {folder}")

            payload = json.dumps({
              "name": folder,
              # "description": "string",
              "icon": "T",
              # "type": "manual",
              # "query": "string",
              # "parentId": "string"
            })

            response = requests.request("POST", f"{endpoint}/api/v1/lists", headers=headers, data=payload)
            response.raise_for_status()

            id = json.loads(response.text)["id"] 
            folders[folder] = id

        response = requests.request("PUT", f"{endpoint}/api/v1/lists/{folders[folder]}/bookmarks/{bookmarkId}", headers=headers, data=payload)
        response.raise_for_status()

        # tags
        if len(tags) > 0:
            payload = json.dumps({
              "tags": [
                {
                  # "tagId": "string",
                  "tagName": tag
                } for tag in tags.split(", ")
              ]
            })

            response = requests.request("POST", f"{endpoint}/api/v1/bookmarks/{bookmarkId}/tags", headers=headers, data=payload)
            response.raise_for_status()

        # break

print(bookmarks)
