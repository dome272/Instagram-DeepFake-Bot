import sys
import pickle
import json

username = sys.argv[1]

api = pickle.load(open("donatorsession", "rb"))
user_id = api.get_id_from_username(username)

print(user_id)

