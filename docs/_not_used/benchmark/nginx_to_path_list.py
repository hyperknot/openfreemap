import json


# This script parses a nginx server log and creates a text file
# which can be used in the Lua script.
# The path file is not supplied in this repo.

with open('access.jsonl') as fp:
    json_lines = fp.readlines()

paths = []
for i, line in enumerate(json_lines):
    log_data = json.loads(line)
    if log_data['status'] != 200:
        continue

    if log_data['request_method'] != 'GET':
        continue

    uri = log_data['uri']

    if 'tiles/' not in uri or not uri.endswith('.pbf'):
        continue

    path = log_data['uri'].split('tiles/')[1]
    paths.append(path + '\n')

    print(f'{i / len(json_lines) * 100:.1f}%')

with open('path_list.txt', 'w') as fp:
    fp.writelines(paths)
