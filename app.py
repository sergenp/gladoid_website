import os
import json
import random
import glob
import flask_discord
from pathlib import Path
from flask import Flask, request, render_template, url_for, redirect, send_file, abort
from MongoDB.Connector import Connector
from app_config import configurate

MongoDB = Connector()

app = Flask(__name__,
            static_folder='web/static',
            template_folder='web/templates')

configurate(app)
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
    abort(404)

@app.route("/user")
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

@app.route('/addNPC', methods=['GET', 'POST'])
def add_npc():
    NPCS = MongoDB.get_npcs()
    attackTypes = MongoDB.get_attack_information()
    debuffTypes = MongoDB.get_turn_debuffs()
    damageTypes = [x['damage_type_name'] for x in attackTypes]

    default_npc_json = random.choice(NPCS)
    if request.method == 'POST':
        with open(f"{request.form['Name']}.json", "w") as f:
            atks = [x.split(" ")[0] for x in request.form.getlist('Attacks')]
            debuffs = [request.form.get('Debuffs')]
            stats = request.form.getlist('Stats')
            stat_keys = default_npc_json['Stats'].keys()
            for k in request.form:
                if k in default_npc_json and not k in ('Attacks', 'Debuffs', 'Stats'):
                    try:
                        default_npc_json[k] = int(request.form[k])
                    except ValueError:
                        default_npc_json[k] = request.form[k]

            default_npc_json["Stats"] = dict(zip(stat_keys, stats))
            default_npc_json["Attacks"] = atks
            default_npc_json["Debuffs"] = debuffs
            json.dump(default_npc_json, f, indent=4, sort_keys=True)
    return render_template("add_npc.html", default_npc_json=default_npc_json, attacks=attackTypes, damages=damageTypes, debuffs=debuffTypes)
