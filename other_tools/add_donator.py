import sys
import pickle
import json

username = sys.argv[1]
level = sys.argv[2]

api = pickle.load(open("donatorsession", "rb"))
user_id = api.get_id_from_username(username)

with open("donator.json", "r+") as file:
    content = json.load(file)
    content["donator"][user_id] = int(level)
    file.seek(0)
    json.dump(content, file)
    file.truncate()

