import os
import requests

headers = {
    "Authorization":f"Bot {os.environ['DISCORD_BOT_TOKEN']}"
}

def get_user_from_id(user_id : int or str):
    return requests.get(f'http://discordapp.com/api/users/{user_id}', headers=headers).json()

def get_user_name_from_id(user_id : int or str):
    return get_user_from_id(user_id)['username']
