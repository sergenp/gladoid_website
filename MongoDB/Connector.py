import sys
import pymongo
import os
import json
sys.path.append("..")

try:
    from MongoDB import mongo_settings
    CONNECTION_STRING = mongo_settings.CONNECTION_STRING
except (ModuleNotFoundError, ImportError):
    CONNECTION_STRING = os.environ["MongoDB_CONNECTION_STRING"]
    
class Connector():
    def __init__(self):
        self.client = pymongo.MongoClient(CONNECTION_STRING).HutAssistant

    def save_guild_settings(self, guild_settings_dict : dict):
        self.client.GuildSettings.find_one_and_replace({'_id' :'guild_settings'}, guild_settings_dict, upsert=True)

    def save_profile(self, profile_dict: dict):
        self.client.UserProfiles.find_one_and_replace({'_id' : profile_dict['_id']}, profile_dict, upsert=True)

    def get_all_profiles(self) -> list:
        return list(self.client.UserProfiles.find())

    def get_attack_information(self) -> list:
        return list(self.client.AttackInformation.find({}, {'_id': False}))

    def get_damage_types(self) -> list:
        return list(self.client.DamageTypes.find({}, {'_id': False}))

    def get_turn_debuffs(self) -> list:
        return list(self.client.TurnDebuffs.find({}, {'_id': False}))

    def get_npcs(self) -> list:
        return list(self.client.NPCs.find({}, {'_id': False}))

    def get_npcs_spawn_settings(self) -> list:
        return list(self.client.NPCSpawnSettings.find({}, {'_id': False}))

    def get_gladiator_game_settings(self) -> dict:
        game_settings = self.client.GladiatorGameSettings.find_one() 
        game_settings.pop("_id")
        return game_settings

    def get_events(self) -> list:
        return list(self.client.Events.find({}, {'_id': False}))

    def get_equipments(self) -> list:
        return list(self.client.Equipments.find({}, {'_id': False}))

    def get_equipment_slots(self) -> list:
        return list(self.client.EquipmentSlots.find({}, {'_id': False}))

    def get_guild_settings(self) -> dict:
        guild_settings = self.client.GuildSettings.find_one() 
        guild_settings.pop("_id")
        return guild_settings

    def download_all_collections_to_local(self):
        gladiator_path = os.path.abspath(os.path.join(os.path.dirname( __file__ ), "..", "Gladiator"))
        user_prof = os.path.join(gladiator_path, "UserProfileData")
        attack_inf = os.path.join(gladiator_path, "AttackInformation")
        events = os.path.join(gladiator_path, "Events")
        equipments = os.path.join(gladiator_path, "Equipments")
        npcs = os.path.join(gladiator_path, "NPCs")
        npc_setting = os.path.join(npcs, "Settings")
        game_setting = os.path.join(gladiator_path, "Settings")
        parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

        json.dump(self.get_attack_information(), open(os.path.join(attack_inf, "GladiatorAttackBuffs.json"), "w"), indent=4)
        json.dump(self.get_damage_types(), open(os.path.join(attack_inf, "GladiatorDamageTypes.json"),"w"), indent=4)
        json.dump(self.get_turn_debuffs(), open(os.path.join(attack_inf, "GladiatorTurnDebuffs.json"),"w"), indent=4)
        for npc in self.get_npcs():
            json.dump(npc, open(os.path.join(npcs, f"{npc['Name']}.json"), "w"), indent=4)
        json.dump(self.get_npcs_spawn_settings(), open(os.path.join(npc_setting, "Spawns.json"), "w"), indent=4)

        for pf in self.get_all_profiles():
            json.dump(pf, open(os.path.join(user_prof, f"{pf['_id']}.json"), "w"), indent=4)
        
        json.dump(self.get_events(), open(os.path.join(events, "Events.json"), "w"), indent=4)
        json.dump(self.get_equipments(), open(os.path.join(equipments, "GladiatorEquipments.json"), "w"), indent=4)
        json.dump(self.get_equipment_slots(), open(os.path.join(equipments, "GladiatorSlots.json"), "w"), indent=4)
        json.dump(self.get_gladiator_game_settings(), open(os.path.join(game_setting, "GladiatorGameSettings.json"), "w"), indent=4)
        json.dump(self.get_guild_settings(), open(os.path.join(parent_dir, "guild_settings.json"), "w"), indent=4)