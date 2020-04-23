import os
import random
import glob
import flask_discord
try:
    from app_config import configurate 
    configurate()
except ImportError as e:
    pass
from pathlib import Path
from flask import Flask, request, render_template, url_for, redirect, send_file, jsonify
from flask_caching import Cache
from MongoDB.Connector import Connector
from Discord import DiscordAPI
import markdown2


MongoDB = Connector()

app = Flask(__name__,
            static_folder='web/static',
            template_folder='web/templates')
config = {
    "SECRET_KEY" : os.environ['SECRET_KEY'],
    "DISCORD_CLIENT_ID" : int(os.environ['DISCORD_CLIENT_ID']),
    "DISCORD_CLIENT_SECRET" : os.environ['DISCORD_CLIENT_SECRET'],
    "DISCORD_REDIRECT_URI" : os.environ['DISCORD_REDIRECT_URI'],
    "CACHE_TYPE": "simple",
    "CACHE_DEFAULT_TIMEOUT": 300
}

app.config.from_mapping(config)
discord = flask_discord.DiscordOAuth2Session(app)
cache = Cache(app)

def get_user_and_profile():
    user, profile = None, None
    try:
        user = discord.fetch_user()
        profile = MongoDB.get_profile(user.id)
    except flask_discord.exceptions.Unauthorized:
        pass
    return user, profile

@app.route("/login/")
def login():
    discord.revoke()
    return discord.create_session(scope=["identify", "email"])

@app.route("/logout/")
def logout():
    discord.revoke()
    return redirect(url_for(".index"))

@app.route("/callback/")
def callback():
    discord.callback()
    return redirect(url_for(".user_page"))


@app.route('/npcimage', methods=['GET'])
def npc_image():
    images_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "NPCImages")
    npc_name = request.args.get("name", "").lower()
    images = []
    for k in glob.glob(os.path.join(images_path, "*.*")):
        if npc_name in Path(k).stem.lower():
            images.append(k)
    if images:
        filename = os.path.join(images_path, random.choice(images))
        return send_file(filename, mimetype='image/png')


@app.route("/policy", methods=['GET'])
def policy():
    return render_template("policy.html")

@app.route('/get_leaderboard', methods=['GET'])
@cache.cached(timeout=300)
def get_leaderboard():
    leaderboard_profiles = MongoDB.get_leaderboard()
    #switch user_id with user_name
    for prof in leaderboard_profiles:
        prof["_id"] = DiscordAPI.get_user_name_from_id(prof["_id"])
    return jsonify(leaderboard_profiles)

@app.route("/leaderboard/")
def leader_board():
    user, profile = get_user_and_profile()
    if user:
        return render_template("leaderboard.html", user=user, profile=profile)
    return render_template("leaderboard.html")

@app.route("/user/")
def user_page():
    user, profile = get_user_and_profile()
    if user:
        return render_template("user.html", user=user, profile=profile)
    return redirect(url_for(".login"))
        
@app.route('/',methods=['GET'])
def index():
    profile_count = MongoDB.get_profile_count()
    match_count = MongoDB.get_all_matches_count()
    user, profile = get_user_and_profile()
    return render_template("index.html", user=user, profile=profile, pc=profile_count, mc=match_count)

@app.route('/npcs',methods=['GET'])
@cache.cached(timeout=600)
def npcs():
    all_npcs = MongoDB.get_npcs()
    spawn_settings = MongoDB.get_npcs_spawn_settings()
    user, profile = get_user_and_profile()
    return render_template("npcs.html", user=user,  profile=profile, npcs=all_npcs, spawns=spawn_settings)

@app.route('/equipments',methods=['GET'])
@cache.cached(timeout=600)
def equipments():
    all_equipments = MongoDB.get_equipments()
    equipment_slots = MongoDB.get_equipment_slots()
    user, profile = get_user_and_profile()
    return render_template("equipments.html", user=user, profile=profile, equipments=all_equipments, slots=equipment_slots)

@app.route('/attacks',methods=['GET'])
def attacks():
    atk_name = str(request.args.get("attackname", "")).replace(" ", "")
    debuff_name = str(request.args.get("debuffname", "")).replace(" ", "")
    atks = MongoDB.get_attack_information()
    damage_types = MongoDB.get_damage_types()
    debuffs = MongoDB.get_turn_debuffs()
    user, profile = get_user_and_profile()
    return render_template("attacks.html", user=user, profile=profile, debuff_name=debuff_name, atk_name=atk_name, attacks=atks, damage_types=damage_types, debuffs=debuffs)

@app.route('/suggestions',methods=['GET', 'POST'])
def suggestions():
    suggestion_tags = ["Feature", "Improvement", "Idea", "Bug Fix"]
    user, profile = get_user_and_profile()
    if request.method == 'POST':
        form_success = False
        if user:
            data = {"From" : user.name}
            data['Tags'] = request.form.getlist('Tags')
            data['Title'] = request.form.get('Title')
            data['Suggestion Text'] = request.form.get('Suggestion Text')
            MongoDB.insert_suggestion(data)
            form_success = True

        return render_template("suggestions.html", user=user, profile=profile, suggestion_tags=suggestion_tags, form_success=form_success)

    return render_template("suggestions.html", user=user, profile=profile, suggestion_tags=suggestion_tags)

@app.route('/matchhistory',methods=['GET'])
def match_history():
    user, profile = get_user_and_profile()
    if not user:
        return redirect(url_for(".login"))

    matches = MongoDB.get_all_match_messages(user.id)
    for k in matches:
        for i, z in enumerate(k['Messages']):
            # replace user id with user name
            k['Messages'][i] = z.replace(f"<@{user.id}>", user.name).replace(f"<@!{user.id}>", user.name)
            # convert markdown to html
            k['Messages'][i] = markdown2.markdown(k['Messages'][i])

    return render_template("match_history.html", matches=matches, user=user, profile=profile)

if __name__ == '__main__':
    app.run()
    
# @app.route('/addNPC', methods=['GET', 'POST'])
# def add_npc():
#     NPCS = MongoDB.get_npcs()
#     attackTypes = MongoDB.get_attack_information()
#     debuffTypes = MongoDB.get_turn_debuffs()
#     damageTypes = [x['damage_type_name'] for x in attackTypes]

#     default_npc_json = random.choice(NPCS)
#     if request.method == 'POST':
#         with open(f"{request.form['Name']}.json", "w") as f:
#             atks = [x.split(" ")[0] for x in request.form.getlist('Attacks')]
#             debuffs = [request.form.get('Debuffs')]
#             stats = request.form.getlist('Stats')
#             stat_keys = default_npc_json['Stats'].keys()
#             for k in request.form:
#                 if k in default_npc_json and not k in ('Attacks', 'Debuffs', 'Stats'):
#                     try:
#                         default_npc_json[k] = int(request.form[k])
#                     except ValueError:
#                         default_npc_json[k] = request.form[k]

#             default_npc_json["Stats"] = dict(zip(stat_keys, stats))
#             default_npc_json["Attacks"] = atks
#             default_npc_json["Debuffs"] = debuffs
#             json.dump(default_npc_json, f, indent=4, sort_keys=True)
#     return render_template("add_npc.html", default_npc_json=default_npc_json, attacks=attackTypes, damages=damageTypes, debuffs=debuffTypes)
