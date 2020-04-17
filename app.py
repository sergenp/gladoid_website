import os
import random
import glob
import flask_discord
from pathlib import Path
from flask import Flask, request, render_template, url_for, redirect, send_file
from MongoDB.Connector import Connector
import markdown2

MongoDB = Connector()

app = Flask(__name__,
            static_folder='web/static',
            template_folder='web/templates')

try:
    from app_config import configurate
    configurate()
except ImportError as e:
    pass

app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config["DISCORD_CLIENT_ID"] = int(os.environ['DISCORD_CLIENT_ID'])
app.config["DISCORD_CLIENT_SECRET"] = os.environ['DISCORD_CLIENT_SECRET']
app.config["DISCORD_REDIRECT_URI"] = os.environ['DISCORD_REDIRECT_URI']

discord = flask_discord.DiscordOAuth2Session(app)

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


@app.route("/user/")
def user_page():
    try:
        user = discord.fetch_user()
        return render_template("user.html", user=user)
    except flask_discord.exceptions.Unauthorized:
        return redirect(url_for(".login"))
        
@app.route('/')
def index():
    user = None
    try:
        user = discord.fetch_user()
    except flask_discord.exceptions.Unauthorized:
        pass
    return render_template("index.html", user=user)

@app.route('/npcs')
def npcs():
    all_npcs = MongoDB.get_npcs()
    user = None
    try:
        user = discord.fetch_user()
    except flask_discord.exceptions.Unauthorized:
        pass
    return render_template("npcs.html", user=user, npcs=all_npcs)

@app.route('/equipments')
def equipments():
    user = None
    try:
        user = discord.fetch_user()
    except flask_discord.exceptions.Unauthorized:
        pass
    return render_template("equipments.html", user=user)

@app.route('/attacks')
def attacks():
    atk_name = request.args.get("attackname", "")
    user = None
    try:
        user = discord.fetch_user()
    except flask_discord.exceptions.Unauthorized:
        pass
    return render_template("attacks.html", user=user, atk_name=atk_name)

@app.route('/suggestions')
def suggestions():
    user = None
    try:
        user = discord.fetch_user()
    except flask_discord.exceptions.Unauthorized:
        pass
    
    return render_template("suggestions.html", user=user)

@app.route('/matchhistory')
def match_history():
    try:
        user = discord.fetch_user()
    except flask_discord.exceptions.Unauthorized:
        return redirect(url_for(".login"))

    matches = MongoDB.get_all_match_messages(user.id)
    for k in matches:
        for i, z in enumerate(k['Messages']):
            # replace user id with user name
            k['Messages'][i] = z.replace(f"<@{user.id}>", user.name).replace(f"<@!{user.id}>", user.name)
            # convert markdown to html
            k['Messages'][i] = markdown2.markdown(k['Messages'][i])

    return render_template("match_history.html", matches=matches, user=user)

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
