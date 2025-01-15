import xml.etree.ElementTree as ET
from collections import defaultdict

file_path = 'inoreader.xml'
out_path = 'deduped.xml'

tree = ET.parse(file_path)
root = tree.getroot()
body = root.find('body')

feeds = defaultdict(list)

for i, category in enumerate(body):
    for j, feed in enumerate(category):
        feeds[feed.attrib['xmlUrl']].append(i)
print('Total feeds:', len(feeds))

dupes = sorted([pair for pair in feeds.items() if len(pair[1]) > 1], key=lambda x: x[1])

print('Deduping...')
for dupe in dupes:
    for i, cat_ind in enumerate(dupe[1]):
        xml_url = dupe[0]
        category = body[cat_ind]
        feed = None
        for f in category:
            if f.attrib['xmlUrl'] == xml_url:
                feed = f
                break
        if feed == None:
            print("Error! Feed not found for", xml_url)
            exit(1)
        if i == 0:
            print(feed.attrib['title'], dupe[1])
            print('    +', category.attrib['title'])
        else:
            print('    -', category.attrib['title'])
            category.remove(feed)

tree.write(out_path)
