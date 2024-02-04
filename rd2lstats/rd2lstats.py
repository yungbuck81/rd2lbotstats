#!/usr/bin/env python3
import discord
import requests
import json
import csv
import sys
sys.path.append("..")

from constants.globalConstants import fantasy_kill_multiplier, fantasy_death_multiplier, fantasy_assist_multiplier, \
    fantasy_lasthit_multiplier, fantasy_gpm_multiplier, fantasy_ts_multiplier, fantasy_roshan_multiplier, \
    fantasy_wards_planted, fantasy_wards_dewarded, fantasy_camps_stacked, fantasy_first_blood, fantasy_stuns_multiplier, \
    pos1directory, pos1gpmfile, pos2directory, pos2gpmfile, pos3directory, pos3gpmfile, pos4directory, \
    pos4gpmfile, pos5directory, pos5gpmfile, pos1kdafile, pos2kdafile, pos4kdafile, pos3kdafile, pos5kdafile, \
    pos1fantasyfile, pos2fantasyfile, pos3fantasyfile, pos4fantasyfile, pos5fantasyfile, match_ids, \
    opendota_api_matches_url, dotabuff_url, opendota_api_players_url, steam_cdn, permissionkeyfile, \
    pos1currentdirectory, pos2currentdirectory, pos3currentdirectory, pos4currentdirectory, pos5currentdirectory, player_ranking_cutoff
from constants.hero_ids import get_hero_name
from constants.localconfig import ADMIN_IDS
import time
import ast
import copy

from utils import process_dict_values_into_list, list_difference, write_to_pos_based_csv_files, \
    find_player_in_dictionaries, empty_all_stat_files, write_to_pos_based_csv_files_current_week, \
    passes_role_threshold, update_current_week
intents = discord.Intents.default()
client = discord.Client(intents=intents)
permissionkey = open(permissionkeyfile).read()

class Rd2lStats:

    def __init__(self):
        self.highest_gpm_value = 0
        self.highest_gpm_hero = 0
        self.highest_gpm_player = ""
        self.highest_gpm_match = ""

        self.highest_xpm_value = 0
        self.highest_xpm_player = ""
        self.highest_xpm_hero = 0
        self.highest_xpm_match = ""

        self.highest_kda_value = 0
        self.highest_kda_player = ""
        self.highest_kda_hero = 0
        self.highest_kda_match = ""

        self.highest_camps_value = 0
        self.highest_camps_player = ""
        self.highest_camps_hero = 0
        self.highest_camps_match = ""

        self.highest_herodamage_value = 0
        self.highest_herodamage_player = ""
        self.highest_herodamage_hero = 0
        self.highest_herodamage_match = ""

        self.highest_stuns_value = 0
        self.highest_stuns_player = ""
        self.highest_stuns_hero = 0
        self.highest_stuns_match = ""

        self.highest_towerdamage_value = 0
        self.highest_towerdamage_player = ""
        self.highest_towerdamage_hero = 0
        self.highest_towerdamage_match = ""

        self.highest_lane_value = 0
        self.highest_lane_hero = 0
        self.highest_lane_player = ""
        self.highest_lane_match = ""

        self.highest_deward_value = 0
        self.highest_deward_player = ""
        self.highest_deward_hero = 0
        self.highest_deward_match = ""

        self.highest_apm_value = 0
        self.highest_apm_player = ""
        self.highest_apm_hero = 0
        self.highest_apm_match = ""

        self.highest_courier_value = 0
        self.highest_courier_player = ""
        self.highest_courier_hero = 0
        self.highest_courier_match = ""

        self.highest_deaths_value = 0
        self.highest_deaths_player = ""
        self.highest_deaths_hero = 0
        self.highest_deaths_match = ""

        self.stats_leaders_dict = {}

        self.gpmcurrent_data = {}
        self.kdacurrent_data = {}
        self.fantasycurrent_data = {}
        self.gpm_data = {}
        self.kda_data = {}
        self.fantasy_data = {}

        self.consecutive_fails = 0

    # Function that calculates the fantasy score for a player object
    def get_fantasy_score(self, player):
        first_blood_claimed = 0 if player["firstblood_claimed"] is None else player["firstblood_claimed"]
        #roshans = (player["roshan_kills"]*1000/player["duration"] if "roshan_kills" in player else player["roshans_killed"]/player["duration"])
        # roshan_kills = 0 if roshans is None else roshans
        towers_killed = player["towers_killed"] if player["towers_killed"] is not None else 0
        obs_placed = player["obs_placed"]*1000/player["duration"] if player["obs_placed"] is not None else 0
        sentry_kills = player["sentry_kills"]*1000/player["duration"] if (
                "sentry_kills" in player and player["sentry_kills"] is not None) else 0
        obs_kills = player["observer_kills"]*1000/player["duration"] if (
                "observer_kills" in player and player["observer_kills"] is not None) else 0
        camps_stacked = player["camps_stacked"]*1000/player["duration"] if player["camps_stacked"] is not None else 0
        stuns = player["stuns"]/player["duration"] if player["stuns"] is not None else 0
        try:
            fantasy_score = round(
                ((player["kills"] * fantasy_kill_multiplier * 1000)/player["duration"]) + ((player["deaths"] * fantasy_death_multiplier * 1000)/player["duration"]) + (
                    (player["assists"] * fantasy_assist_multiplier * 1000)/player["duration"]) + (
                    (player["last_hits"] * fantasy_lasthit_multiplier * 10)/player["duration"]) + (
                    (player["gold_per_min"] * 10 * fantasy_gpm_multiplier)/player["duration"]) + (
                        towers_killed * fantasy_ts_multiplier) + (
                        # roshan_kills * fantasy_roshan_multiplier) + (
                        obs_placed * fantasy_wards_planted) + (
                        (sentry_kills + obs_kills) * fantasy_wards_dewarded) + (
                        camps_stacked * fantasy_camps_stacked) + (
                        first_blood_claimed * fantasy_first_blood) + (
                        stuns * fantasy_stuns_multiplier), 2)
        except:  # Todo add specific exception and add details in print for debugging
            print("Error in get fantasy score")
            return
        return fantasy_score*100

    # Returns the player name in text given the player ID
    def get_player_name_for_account_id(self, playerId):
        json_data = self.request_opendota(opendota_api_players_url + playerId)
        return json_data['profile']['name'] if json_data['profile'].get('name') is not None else json_data['profile']['personaname']

    def request_opendota(self, url):
        response = requests.get(url)
        json_data = json.loads(response.text)
        if 'rate limit' in json_data.get('error', ''):
            self.consecutive_fails += 1
            time.sleep(61)
            if (self.consecutive_fails < 4):
                return self.request_opendota(url)
            else:
                return 'Unable to make request'
        else:
            self.consecutive_fails = 0
            return json_data

    # Function to process csv files and check duplicates for a single player across multiple pos. User can select
    # manually which role they should belong to
    def find_duplicates(self):

        self.gpmcurrent_data = {
          'gpm1' : process_dict_values_into_list(
              dict(csv.reader(open(pos1currentdirectory + pos1gpmfile, 'r', encoding="utf-8", newline='')))),
          'gpm2' : process_dict_values_into_list(
              dict(csv.reader(open(pos2currentdirectory + pos2gpmfile, 'r', encoding="utf-8", newline='')))),
          'gpm3' : process_dict_values_into_list(
              dict(csv.reader(open(pos3currentdirectory + pos3gpmfile, 'r', encoding="utf-8", newline='')))),
          'gpm4' : process_dict_values_into_list(
              dict(csv.reader(open(pos4currentdirectory + pos4gpmfile, 'r', encoding="utf-8", newline='')))),
          'gpm5' : process_dict_values_into_list(
              dict(csv.reader(open(pos5currentdirectory + pos5gpmfile, 'r', encoding="utf-8", newline=''))))
        }

        self.kdacurrent_data = {
          'kda1' : process_dict_values_into_list(
              dict(csv.reader(open(pos1currentdirectory + pos1kdafile, 'r', encoding="utf-8", newline='')))),
          'kda2' : process_dict_values_into_list(
              dict(csv.reader(open(pos2currentdirectory + pos2kdafile, 'r', encoding="utf-8", newline='')))),
          'kda3' : process_dict_values_into_list(
              dict(csv.reader(open(pos3currentdirectory + pos3kdafile, 'r', encoding="utf-8", newline='')))),
          'kda4' : process_dict_values_into_list(
              dict(csv.reader(open(pos4currentdirectory + pos4kdafile, 'r', encoding="utf-8", newline='')))),
          'kda5' : process_dict_values_into_list(
              dict(csv.reader(open(pos5currentdirectory + pos5kdafile, 'r', encoding="utf-8", newline=''))))
        }

        self.fantasycurrent_data = {
          'fantasy1' : process_dict_values_into_list(
              dict(csv.reader(open(pos1currentdirectory + pos1fantasyfile, 'r', encoding="utf-8", newline='')))),
          'fantasy2' : process_dict_values_into_list(
              dict(csv.reader(open(pos2currentdirectory + pos2fantasyfile, 'r', encoding="utf-8", newline='')))),
          'fantasy3' : process_dict_values_into_list(
              dict(csv.reader(open(pos3currentdirectory + pos3fantasyfile, 'r', encoding="utf-8", newline='')))),
          'fantasy4' : process_dict_values_into_list(
              dict(csv.reader(open(pos4currentdirectory + pos4fantasyfile, 'r', encoding="utf-8", newline='')))),
          'fantasy5' : process_dict_values_into_list(
              dict(csv.reader(open(pos5currentdirectory + pos5fantasyfile, 'r', encoding="utf-8", newline=''))))
        }

        self.gpm_data = {
          'gpm1' : process_dict_values_into_list(
              dict(csv.reader(open(pos1directory + pos1gpmfile, 'r', encoding="utf-8", newline='')))),
          'gpm2' : process_dict_values_into_list(
              dict(csv.reader(open(pos2directory + pos2gpmfile, 'r', encoding="utf-8", newline='')))),
          'gpm3' : process_dict_values_into_list(
              dict(csv.reader(open(pos3directory + pos3gpmfile, 'r', encoding="utf-8", newline='')))),
          'gpm4' : process_dict_values_into_list(
              dict(csv.reader(open(pos4directory + pos4gpmfile, 'r', encoding="utf-8", newline='')))),
          'gpm5' : process_dict_values_into_list(
              dict(csv.reader(open(pos5directory + pos5gpmfile, 'r', encoding="utf-8", newline=''))))
        }

        self.kda_data = {     
          'kda1' : process_dict_values_into_list(
              dict(csv.reader(open(pos1directory + pos1kdafile, 'r', encoding="utf-8", newline='')))),
          'kda2' : process_dict_values_into_list(
              dict(csv.reader(open(pos2directory + pos2kdafile, 'r', encoding="utf-8", newline='')))),
          'kda3' : process_dict_values_into_list(
              dict(csv.reader(open(pos3directory + pos3kdafile, 'r', encoding="utf-8", newline='')))),
          'kda4' : process_dict_values_into_list(
              dict(csv.reader(open(pos4directory + pos4kdafile, 'r', encoding="utf-8", newline='')))),
          'kda5' : process_dict_values_into_list(
              dict(csv.reader(open(pos5directory + pos5kdafile, 'r', encoding="utf-8", newline=''))))
        }

        self.fantasy_data = {
          'fantasy1' : process_dict_values_into_list(
              dict(csv.reader(open(pos1directory + pos1fantasyfile, 'r', encoding="utf-8", newline='')))),
          'fantasy2' : process_dict_values_into_list(
              dict(csv.reader(open(pos2directory + pos2fantasyfile, 'r', encoding="utf-8", newline='')))),
          'fantasy3' : process_dict_values_into_list(
              dict(csv.reader(open(pos3directory + pos3fantasyfile, 'r', encoding="utf-8", newline='')))),
          'fantasy4' : process_dict_values_into_list(
              dict(csv.reader(open(pos4directory + pos4fantasyfile, 'r', encoding="utf-8", newline='')))),
          'fantasy5' : process_dict_values_into_list(
              dict(csv.reader(open(pos5directory + pos5fantasyfile, 'r', encoding="utf-8", newline=''))))
        }

        # Iterate through each stat and for each pos to find duplicates
        # If the role is changed from what was originally parsed, add them to the new roles dictionary and delete old
        gpm_value_set = {}
        gpm_player_set = {}
        user_choices = []
        for index, gpmdict in enumerate(
                [copy.deepcopy(self.gpmcurrent_data['gpm1']), copy.deepcopy(self.gpmcurrent_data['gpm2']), copy.deepcopy(self.gpmcurrent_data['gpm3']), copy.deepcopy(self.gpmcurrent_data['gpm4']),
                 copy.deepcopy(self.gpmcurrent_data['gpm5'])]):
            for player, gpm in copy.deepcopy(gpmdict).items():
                if player in gpm_player_set:
                    print("-- Player GPM: {} found in {} and {} -- ".format(player, gpm_player_set[player], index + 1))
                    foundInput = False
                    while(not foundInput):
                        try:
                            uinput = int(input("Which position should be selected? 1,2,3,4,5 for roles or 0 to keep separate"))
                            user_choices.append(uinput)
                            foundInput = True # Assume true and set back to false if needed
                            if uinput == 1:
                                cumulative = gpm_value_set[player][0] * gpm_value_set[player][1]
                                matches = gpm_value_set[player][1] + gpm[1]
                                evalList = [(cumulative + (gpm[0] * gpm[1])) / matches, matches]
                                self.gpm_data['gpm1'][player] = evalList
                                if index + 1 == 1:
                                    if gpm_player_set[player] == 2:
                                        self.gpm_data['gpm2'].pop(player)
                                    if gpm_player_set[player] == 3:
                                        self.gpm_data['gpm3'].pop(player)
                                    if gpm_player_set[player] == 4:
                                        self.gpm_data['gpm4'].pop(player)
                                    if gpm_player_set[player] == 5:
                                        self.gpm_data['gpm5'].pop(player)
                                elif gpm_player_set[player] == 1:
                                    if index + 1 == 2:
                                        self.gpm_data['gpm2'].pop(player)
                                    if index + 1 == 3:
                                        self.gpm_data['gpm3'].pop(player)
                                    if index + 1 == 4:
                                        self.gpm_data['gpm4'].pop(player)
                                    if index + 1 == 5:
                                        self.gpm_data['gpm5'].pop(player)
                            elif uinput == 2:
                                cumulative = gpm_value_set[player][0] * gpm_value_set[player][1]
                                matches = gpm_value_set[player][1] + gpm[1]
                                evalList = [(cumulative + (gpm[0] * gpm[1])) / matches, matches]
                                self.gpm_data['gpm2'][player] = evalList
                                if index + 1 == 2:
                                    if gpm_player_set[player] == 1:
                                        self.gpm_data['gpm1'].pop(player)
                                    if gpm_player_set[player] == 3:
                                        self.gpm_data['gpm3'].pop(player)
                                    if gpm_player_set[player] == 4:
                                        self.gpm_data['gpm4'].pop(player)
                                    if gpm_player_set[player] == 5:
                                        self.gpm_data['gpm5'].pop(player)
                                elif gpm_player_set[player] == 2:
                                    if index + 1 == 1:
                                        self.gpm_data['gpm1'].pop(player)
                                    if index + 1 == 3:
                                        self.gpm_data['gpm3'].pop(player)
                                    if index + 1 == 4:
                                        self.gpm_data['gpm4'].pop(player)
                                    if index + 1 == 5:
                                        self.gpm_data['gpm5'].pop(player)
                            elif uinput == 3:
                                cumulative = gpm_value_set[player][0] * gpm_value_set[player][1]
                                matches = gpm_value_set[player][1] + gpm[1]
                                evalList = [(cumulative + (gpm[0] * gpm[1])) / matches, matches]
                                self.gpm_data['gpm3'][player] = evalList
                                if index + 1 == 3:
                                    if gpm_player_set[player] == 2:
                                        self.gpm_data['gpm2'].pop(player)
                                    if gpm_player_set[player] == 1:
                                        self.gpm_data['gpm1'].pop(player)
                                    if gpm_player_set[player] == 4:
                                        self.gpm_data['gpm4'].pop(player)
                                    if gpm_player_set[player] == 5:
                                        self.gpm_data['gpm5'].pop(player)
                                elif gpm_player_set[player] == 3:
                                    if index + 1 == 2:
                                        self.gpm_data['gpm2'].pop(player)
                                    if index + 1 == 1:
                                        self.gpm_data['gpm1'].pop(player)
                                    if index + 1 == 4:
                                        self.gpm_data['gpm4'].pop(player)
                                    if index + 1 == 5:
                                        self.gpm_data['gpm5'].pop(player)
                            elif uinput == 4:
                                cumulative = gpm_value_set[player][0] * gpm_value_set[player][1]
                                matches = gpm_value_set[player][1] + gpm[1]
                                evalList = [(cumulative + (gpm[0] * gpm[1])) / matches, matches]
                                self.gpm_data['gpm4'][player] = evalList
                                if index + 1 == 4:
                                    if gpm_player_set[player] == 2:
                                        self.gpm_data['gpm2'].pop(player)
                                    if gpm_player_set[player] == 3:
                                        self.gpm_data['gpm3'].pop(player)
                                    if gpm_player_set[player] == 1:
                                        self.gpm_data['gpm1'].pop(player)
                                    if gpm_player_set[player] == 5:
                                        self.gpm_data['gpm5'].pop(player)
                                elif gpm_player_set[player] == 4:
                                    if index + 1 == 2:
                                        self.gpm_data['gpm2'].pop(player)
                                    if index + 1 == 3:
                                        self.gpm_data['gpm3'].pop(player)
                                    if index + 1 == 1:
                                        self.gpm_data['gpm1'].pop(player)
                                    if index + 1 == 5:
                                        self.gpm_data['gpm5'].pop(player)
                            elif uinput == 5:
                                cumulative = gpm_value_set[player][0] * gpm_value_set[player][1]
                                matches = gpm_value_set[player][1] + gpm[1]
                                evalList = [(cumulative + (gpm[0] * gpm[1])) / matches, matches]
                                self.gpm_data['gpm5'][player] = evalList
                                if index + 1 == 5:
                                    if gpm_player_set[player] == 2:
                                        self.gpm_data['gpm2'].pop(player)
                                    if gpm_player_set[player] == 3:
                                        self.gpm_data['gpm3'].pop(player)
                                    if gpm_player_set[player] == 4:
                                        self.gpm_data['gpm4'].pop(player)
                                    if gpm_player_set[player] == 1:
                                        self.gpm_data['gpm1'].pop(player)
                                elif gpm_player_set[player] == 5:
                                    if index + 1 == 2:
                                        self.gpm_data['gpm2'].pop(player)
                                    if index + 1 == 3:
                                        self.gpm_data['gpm3'].pop(player)
                                    if index + 1 == 4:
                                        self.gpm_data['gpm4'].pop(player)
                                    if index + 1 == 1:
                                        self.gpm_data['gpm1'].pop(player)
                            elif uinput == 0:
                                print("Keeping both roles' stats")
                            else:
                                raise ValueError()
                        except ValueError:
                            print("Option not recognized.")
                            foundInput = False
                else:
                    gpm_player_set[player] = index + 1
                    gpm_value_set[player] = gpm

        # Iterate through each stat and for each pos to find duplicates
        # If the role is changed from what was originally parsed, add them to the new roles dictionary and delete old
        kda_value_set = {}
        kda_player_set = {}
        counter = -1
        for index, kdadict in enumerate(
                [copy.deepcopy(self.kdacurrent_data['kda1']), copy.deepcopy(self.kdacurrent_data['kda2']), copy.deepcopy(self.kdacurrent_data['kda3']), copy.deepcopy(self.kdacurrent_data['kda4']),
                 copy.deepcopy(self.kdacurrent_data['kda5'])]):

            for player, kda in copy.deepcopy(kdadict).items():
                if player in kda_player_set:
                    counter += 1
                    try:
                        if user_choices[counter] == 1:
                            cumulative = kda_value_set[player][0] * kda_value_set[player][1]
                            matches = kda_value_set[player][1] + kda[1]
                            evalList = [(cumulative + (kda[0] * kda[1])) / matches, matches]
                            self.kda_data['kda1'][player] = evalList
                            if index + 1 == 1:
                                if kda_player_set[player] == 2:
                                    self.kda_data['kda2'].pop(player)
                                if kda_player_set[player] == 3:
                                    self.kda_data['kda3'].pop(player)
                                if kda_player_set[player] == 4:
                                    self.kda_data['kda4'].pop(player)
                                if kda_player_set[player] == 5:
                                    self.kda_data['kda5'].pop(player)
                            elif kda_player_set[player] == 1:
                                if index + 1 == 2:
                                    self.kda_data['kda2'].pop(player)
                                if index + 1 == 3:
                                    self.kda_data['kda3'].pop(player)
                                if index + 1 == 4:
                                    self.kda_data['kda4'].pop(player)
                                if index + 1 == 5:
                                    self.kda_data['kda5'].pop(player)
                        elif user_choices[counter] == 2:
                            cumulative = kda_value_set[player][0] * kda_value_set[player][1]
                            matches = kda_value_set[player][1] + kda[1]
                            evalList = [(cumulative + (kda[0] * kda[1])) / matches, matches]
                            self.kda_data['kda2'][player] = evalList
                            if index + 1 == 2:
                                if kda_player_set[player] == 1:
                                    self.kda_data['kda1'].pop(player)
                                if kda_player_set[player] == 3:
                                    self.kda_data['kda3'].pop(player)
                                if kda_player_set[player] == 4:
                                    self.kda_data['kda4'].pop(player)
                                if kda_player_set[player] == 5:
                                    self.kda_data['kda5'].pop(player)
                            elif kda_player_set[player] == 2:
                                if index + 1 == 1:
                                    self.kda_data['kda1'].pop(player)
                                if index + 1 == 3:
                                    self.kda_data['kda3'].pop(player)
                                if index + 1 == 4:
                                    self.kda_data['kda4'].pop(player)
                                if index + 1 == 5:
                                    self.kda_data['kda5'].pop(player)
                        elif user_choices[counter] == 3:
                            cumulative = kda_value_set[player][0] * kda_value_set[player][1]
                            matches = kda_value_set[player][1] + kda[1]
                            evalList = [(cumulative + (kda[0] * kda[1])) / matches, matches]
                            self.kda_data['kda3'][player] = evalList
                            if index + 1 == 3:
                                if kda_player_set[player] == 2:
                                    self.kda_data['kda2'].pop(player)
                                if kda_player_set[player] == 1:
                                    self.kda_data['kda1'].pop(player)
                                if kda_player_set[player] == 4:
                                    self.kda_data['kda4'].pop(player)
                                if kda_player_set[player] == 5:
                                    self.kda_data['kda5'].pop(player)
                            elif kda_player_set[player] == 3:
                                if index + 1 == 2:
                                    self.kda_data['kda2'].pop(player)
                                if index + 1 == 1:
                                    self.kda_data['kda1'].pop(player)
                                if index + 1 == 4:
                                    self.kda_data['kda4'].pop(player)
                                if index + 1 == 5:
                                    self.kda_data['kda5'].pop(player)
                        elif user_choices[counter] == 4:
                            cumulative = kda_value_set[player][0] * kda_value_set[player][1]
                            matches = kda_value_set[player][1] + kda[1]
                            evalList = [(cumulative + (kda[0] * kda[1])) / matches, matches]
                            self.kda_data['kda4'][player] = evalList
                            if index + 1 == 4:
                                if kda_player_set[player] == 2:
                                    self.kda_data['kda2'].pop(player)
                                if kda_player_set[player] == 3:
                                    self.kda_data['kda3'].pop(player)
                                if kda_player_set[player] == 1:
                                    self.kda_data['kda1'].pop(player)
                                if kda_player_set[player] == 5:
                                    self.kda_data['kda5'].pop(player)
                            elif kda_player_set[player] == 4:
                                if index + 1 == 2:
                                    self.kda_data['kda2'].pop(player)
                                if index + 1 == 3:
                                    self.kda_data['kda3'].pop(player)
                                if index + 1 == 1:
                                    self.kda_data['kda1'].pop(player)
                                if index + 1 == 5:
                                    self.kda_data['kda5'].pop(player)
                        elif user_choices[counter] == 5:
                            cumulative = kda_value_set[player][0] * kda_value_set[player][1]
                            matches = kda_value_set[player][1] + kda[1]
                            evalList = [(cumulative + (kda[0] * kda[1])) / matches, matches]
                            self.kda_data['kda5'][player] = evalList
                            if index + 1 == 5:
                                if kda_player_set[player] == 2:
                                    self.kda_data['kda2'].pop(player)
                                if kda_player_set[player] == 3:
                                    self.kda_data['kda3'].pop(player)
                                if kda_player_set[player] == 4:
                                    self.kda_data['kda4'].pop(player)
                                if kda_player_set[player] == 1:
                                    self.kda_data['kda1'].pop(player)
                            elif kda_player_set[player] == 5:
                                if index + 1 == 2:
                                    self.kda_data['kda2'].pop(player)
                                if index + 1 == 3:
                                    self.kda_data['kda3'].pop(player)
                                if index + 1 == 4:
                                    self.kda_data['kda4'].pop(player)
                                if index + 1 == 5:
                                    self.kda_data['kda1'].pop(player)
                        elif user_choices[counter] == 0:
                            print("Keeping both roles' stats")
                        else:
                            raise ValueError()
                    except ValueError:
                        print("Option not recognized.")

                else:
                    kda_player_set[player] = index + 1
                    kda_value_set[player] = kda

        # Iterate through each stat and for each pos to find duplicates
        # If the role is changed from what was originally parsed, add them to the new roles dictionary and delete old
        fantasy_value_set = {}
        fantasy_player_set = {}
        counter = -1
        for index, fantasydict in enumerate(
                [copy.deepcopy(self.fantasycurrent_data['fantasy1']), copy.deepcopy(self.fantasycurrent_data['fantasy2']), copy.deepcopy(self.fantasycurrent_data['fantasy3']), 
                 copy.deepcopy(self.fantasycurrent_data['fantasy4']), copy.deepcopy(self.fantasycurrent_data['fantasy5'])]):

            for player, fantasy in copy.deepcopy(fantasydict).items():
                if player in fantasy_player_set:
                    counter += 1
                    if user_choices[counter] == 1:
                        cumulative = fantasy_value_set[player][0] * fantasy_value_set[player][1]
                        matches = fantasy_value_set[player][1] + fantasy[1]
                        evalList = [(cumulative + (fantasy[0] * fantasy[1])) / matches, matches]
                        self.fantasy_data['fantasy1'][player] = evalList
                        if index + 1 == 1:
                            if fantasy_player_set[player] == 2:
                                self.fantasy_data['fantasy2'].pop(player)
                            if fantasy_player_set[player] == 3:
                                self.fantasy_data['fantasy3'].pop(player)
                            if fantasy_player_set[player] == 4:
                                self.fantasy_data['fantasy4'].pop(player)
                            if fantasy_player_set[player] == 5:
                                self.fantasy_data['fantasy5'].pop(player)
                        elif fantasy_player_set[player] == 1:
                            if index + 1 == 2:
                                self.fantasy_data['fantasy2'].pop(player)
                            if index + 1 == 3:
                                self.fantasy_data['fantasy3'].pop(player)
                            if index + 1 == 4:
                                self.fantasy_data['fantasy4'].pop(player)
                            if index + 1 == 5:
                                self.fantasy_data['fantasy5'].pop(player)
                    elif user_choices[counter] == 2:
                        cumulative = fantasy_value_set[player][0] * fantasy_value_set[player][1]
                        matches = fantasy_value_set[player][1] + fantasy[1]
                        evalList = [(cumulative + (fantasy[0] * fantasy[1])) / matches, matches]
                        self.fantasy_data['fantasy2'][player] = evalList
                        if index + 1 == 2:
                            if fantasy_player_set[player] == 1:
                                self.fantasy_data['fantasy1'].pop(player)
                            if fantasy_player_set[player] == 3:
                                self.fantasy_data['fantasy3'].pop(player)
                            if fantasy_player_set[player] == 4:
                                self.fantasy_data['fantasy4'].pop(player)
                            if fantasy_player_set[player] == 5:
                                self.fantasy_data['fantasy5'].pop(player)
                        elif fantasy_player_set[player] == 2:
                            if index + 1 == 1:
                                self.fantasy_data['fantasy1'].pop(player)
                            if index + 1 == 3:
                                self.fantasy_data['fantasy3'].pop(player)
                            if index + 1 == 4:
                                self.fantasy_data['fantasy4'].pop(player)
                            if index + 1 == 5:
                                self.fantasy_data['fantasy5'].pop(player)
                    elif user_choices[counter] == 3:
                        cumulative = fantasy_value_set[player][0] * fantasy_value_set[player][1]
                        matches = fantasy_value_set[player][1] + fantasy[1]
                        evalList = [(cumulative + (fantasy[0] * fantasy[1])) / matches, matches]
                        self.fantasy_data['fantasy3'][player] = evalList
                        if index + 1 == 3:
                            if fantasy_player_set[player] == 2:
                                self.fantasy_data['fantasy2'].pop(player)
                            if fantasy_player_set[player] == 1:
                                self.fantasy_data['fantasy1'].pop(player)
                            if fantasy_player_set[player] == 4:
                                self.fantasy_data['fantasy4'].pop(player)
                            if fantasy_player_set[player] == 5:
                                self.fantasy_data['fantasy5'].pop(player)
                        elif fantasy_player_set[player] == 3:
                            if index + 1 == 2:
                                self.fantasy_data['fantasy2'].pop(player)
                            if index + 1 == 1:
                                self.fantasy_data['fantasy1'].pop(player)
                            if index + 1 == 4:
                                self.fantasy_data['fantasy4'].pop(player)
                            if index + 1 == 5:
                                self.fantasy_data['fantasy5'].pop(player)
                    elif user_choices[counter] == 4:
                        cumulative = fantasy_value_set[player][0] * fantasy_value_set[player][1]
                        matches = fantasy_value_set[player][1] + fantasy[1]
                        evalList = [(cumulative + (fantasy[0] * fantasy[1])) / matches, matches]
                        self.fantasy_data['fantasy4'][player] = evalList
                        if index + 1 == 4:
                            if fantasy_player_set[player] == 2:
                                self.fantasy_data['fantasy2'].pop(player)
                            if fantasy_player_set[player] == 3:
                                self.fantasy_data['fantasy3'].pop(player)
                            if fantasy_player_set[player] == 1:
                                self.fantasy_data['fantasy1'].pop(player)
                            if fantasy_player_set[player] == 5:
                                self.fantasy_data['fantasy5'].pop(player)
                        elif fantasy_player_set[player] == 4:
                            if index + 1 == 2:
                                self.fantasy_data['fantasy2'].pop(player)
                            if index + 1 == 3:
                                self.fantasy_data['fantasy3'].pop(player)
                            if index + 1 == 1:
                                self.fantasy_data['fantasy1'].pop(player)
                            if index + 1 == 5:
                                self.fantasy_data['fantasy5'].pop(player)
                    elif user_choices[counter] == 5:
                        cumulative = fantasy_value_set[player][0] * fantasy_value_set[player][1]
                        matches = fantasy_value_set[player][1] + fantasy[1]
                        evalList = [(cumulative + (fantasy[0] * fantasy[1])) / matches, matches]
                        self.fantasy_data['fantasy5'][player] = evalList
                        if index + 1 == 5:
                            if fantasy_player_set[player] == 2:
                                self.fantasy_data['fantasy2'].pop(player)
                            if fantasy_player_set[player] == 3:
                                self.fantasy_data['fantasy3'].pop(player)
                            if fantasy_player_set[player] == 4:
                                self.fantasy_data['fantasy4'].pop(player)
                            if fantasy_player_set[player] == 1:
                                self.fantasy_data['fantasy1'].pop(player)
                        elif fantasy_player_set[player] == 5:
                            if index + 1 == 2:
                                self.fantasy_data['fantasy2'].pop(player)
                            if index + 1 == 3:
                                self.fantasy_data['fantasy3'].pop(player)
                            if index + 1 == 4:
                                self.fantasy_data['fantasy4'].pop(player)
                            if index + 1 == 1:
                                self.fantasy_data['fantasy1'].pop(player)
                    elif user_choices[counter]  == 0:
                        print("Keeping both roles stats")
                    else:
                        print("Option not recognized. Please enter one among 1/2/3/4/5")

                else:
                    fantasy_player_set[player] = index + 1
                    fantasy_value_set[player] = fantasy

        write_to_pos_based_csv_files(self.gpm_data['gpm1'], self.kda_data['kda1'], self.fantasy_data['fantasy1'],
                                     self.gpm_data['gpm2'], self.kda_data['kda2'], self.fantasy_data['fantasy2'],
                                     self.gpm_data['gpm3'], self.kda_data['kda3'], self.fantasy_data['fantasy3'],
                                     self.gpm_data['gpm4'], self.kda_data['kda4'], self.fantasy_data['fantasy4'],
                                     self.gpm_data['gpm5'], self.kda_data['kda5'], self.fantasy_data['fantasy5'])

        print("No more duplicates found. Exiting...")
        return

    # Function to swap two players roles
    def swap_players(self):

        # TODO: Improve data structure used to be a single object
        self.gpm_data['gpm1'] = process_dict_values_into_list(
            dict(csv.reader(open(pos1directory + pos1gpmfile, 'r', encoding="utf-8", newline=''))))
        self.gpm_data['gpm2'] = process_dict_values_into_list(
            dict(csv.reader(open(pos2directory + pos2gpmfile, 'r', encoding="utf-8", newline=''))))
        self.gpm_data['gpm3'] = process_dict_values_into_list(
            dict(csv.reader(open(pos3directory + pos3gpmfile, 'r', encoding="utf-8", newline=''))))
        self.gpm_data['gpm4'] = process_dict_values_into_list(
            dict(csv.reader(open(pos4directory + pos4gpmfile, 'r', encoding="utf-8", newline=''))))
        self.gpm_data['gpm5'] = process_dict_values_into_list(
            dict(csv.reader(open(pos5directory + pos5gpmfile, 'r', encoding="utf-8", newline=''))))

        self.kda_data['kda1'] = process_dict_values_into_list(
            dict(csv.reader(open(pos1directory + pos1kdafile, 'r', encoding="utf-8", newline=''))))
        self.kda_data['kda2'] = process_dict_values_into_list(
            dict(csv.reader(open(pos2directory + pos2kdafile, 'r', encoding="utf-8", newline=''))))
        self.kda_data['kda3'] = process_dict_values_into_list(
            dict(csv.reader(open(pos3directory + pos3kdafile, 'r', encoding="utf-8", newline=''))))
        self.kda_data['kda4'] = process_dict_values_into_list(
            dict(csv.reader(open(pos4directory + pos4kdafile, 'r', encoding="utf-8", newline=''))))
        self.kda_data['kda5'] = process_dict_values_into_list(
            dict(csv.reader(open(pos5directory + pos5kdafile, 'r', encoding="utf-8", newline=''))))

        self.fantasy_data['fantasy1'] = process_dict_values_into_list(
            dict(csv.reader(open(pos1directory + pos1fantasyfile, 'r', encoding="utf-8", newline=''))))
        self.fantasy_data['fantasy2'] = process_dict_values_into_list(
            dict(csv.reader(open(pos2directory + pos2fantasyfile, 'r', encoding="utf-8", newline=''))))
        self.fantasy_data['fantasy3'] = process_dict_values_into_list(
            dict(csv.reader(open(pos3directory + pos3fantasyfile, 'r', encoding="utf-8", newline=''))))
        self.fantasy_data['fantasy4'] = process_dict_values_into_list(
            dict(csv.reader(open(pos4directory + pos4fantasyfile, 'r', encoding="utf-8", newline=''))))
        self.fantasy_data['fantasy5'] = process_dict_values_into_list(
            dict(csv.reader(open(pos5directory + pos5fantasyfile, 'r', encoding="utf-8", newline=''))))

        player1, player2 = input("Enter two players ID's to swap roles").split()

        dict1 = find_player_in_dictionaries(player1, self.gpm_data)
        dict2 = find_player_in_dictionaries(player2, self.gpm_data)
        temp = dict1.pop(player1)
        dict2[player1] = temp
        temp = dict2.pop(player2)
        dict1[player2] = temp

        dict1 = find_player_in_dictionaries(player1, self.kda_data)
        dict2 = find_player_in_dictionaries(player2, self.kda_data)
        temp = dict1.pop(player1)
        dict2[player1] = temp
        temp = dict2.pop(player2)
        dict1[player2] = temp

        dict1 = find_player_in_dictionaries(player1, self.fantasy_data)
        dict2 = find_player_in_dictionaries(player2, self.fantasy_data)
        temp = dict1.pop(player1)
        dict2[player1] = temp
        temp = dict2.pop(player2)
        dict1[player2] = temp


        write_to_pos_based_csv_files(self.gpm_data['gpm1'], self.kda_data['kda1'], self.fantasy_data['fantasy1'],
                                     self.gpm_data['gpm2'], self.kda_data['kda2'], self.fantasy_data['fantasy2'],
                                     self.gpm_data['gpm3'], self.kda_data['kda3'], self.fantasy_data['fantasy3'],
                                     self.gpm_data['gpm4'], self.kda_data['kda4'], self.fantasy_data['fantasy4'],
                                     self.gpm_data['gpm5'], self.kda_data['kda5'], self.fantasy_data['fantasy5'])

        print("Swapped both players successfully")
        return

    # Function that calculates stats for current week, adds them to the cumulative stats for the season
    def generate_stats(self):
        # TODO: Create function that can be reused
        self.gpm_data['gpm1'] = process_dict_values_into_list(
            dict(csv.reader(open(pos1directory + pos1gpmfile, 'r+', encoding="utf-8", newline=''))))
        self.gpm_data['gpm2'] = process_dict_values_into_list(
            dict(csv.reader(open(pos2directory + pos2gpmfile, 'r+', encoding="utf-8", newline=''))))
        self.gpm_data['gpm3'] = process_dict_values_into_list(
            dict(csv.reader(open(pos3directory + pos3gpmfile, 'r+', encoding="utf-8", newline=''))))
        self.gpm_data['gpm4'] = process_dict_values_into_list(
            dict(csv.reader(open(pos4directory + pos4gpmfile, 'r+', encoding="utf-8", newline=''))))
        self.gpm_data['gpm5'] = process_dict_values_into_list(
            dict(csv.reader(open(pos5directory + pos5gpmfile, 'r+', encoding="utf-8", newline=''))))

        self.kda_data['kda1'] = process_dict_values_into_list(
            dict(csv.reader(open(pos1directory + pos1kdafile, 'r+', encoding="utf-8", newline=''))))
        self.kda_data['kda2'] = process_dict_values_into_list(
            dict(csv.reader(open(pos2directory + pos2kdafile, 'r+', encoding="utf-8", newline=''))))
        self.kda_data['kda3'] = process_dict_values_into_list(
            dict(csv.reader(open(pos3directory + pos3kdafile, 'r+', encoding="utf-8", newline=''))))
        self.kda_data['kda4'] = process_dict_values_into_list(
            dict(csv.reader(open(pos4directory + pos4kdafile, 'r+', encoding="utf-8", newline=''))))
        self.kda_data['kda5'] = process_dict_values_into_list(
            dict(csv.reader(open(pos5directory + pos5kdafile, 'r+', encoding="utf-8", newline=''))))

        self.fantasy_data['fantasy1'] = process_dict_values_into_list(
            dict(csv.reader(open(pos1directory + pos1fantasyfile, 'r+', encoding="utf-8", newline=''))))
        self.fantasy_data['fantasy2'] = process_dict_values_into_list(
            dict(csv.reader(open(pos2directory + pos2fantasyfile, 'r+', encoding="utf-8", newline=''))))
        self.fantasy_data['fantasy3'] = process_dict_values_into_list(
            dict(csv.reader(open(pos3directory + pos3fantasyfile, 'r+', encoding="utf-8", newline=''))))
        self.fantasy_data['fantasy4'] = process_dict_values_into_list(
            dict(csv.reader(open(pos4directory + pos4fantasyfile, 'r+', encoding="utf-8", newline=''))))
        self.fantasy_data['fantasy5'] = process_dict_values_into_list(
            dict(csv.reader(open(pos5directory + pos5fantasyfile, 'r+', encoding="utf-8", newline=''))))

        # Current week stats

        self.gpmcurrent_data['gpm1'] = process_dict_values_into_list(
            dict(csv.reader(open(pos1currentdirectory + pos1gpmfile, 'w+', encoding="utf-8", newline=''))))
        self.gpmcurrent_data['gpm2'] = process_dict_values_into_list(
            dict(csv.reader(open(pos2currentdirectory + pos2gpmfile, 'w+', encoding="utf-8", newline=''))))
        self.gpmcurrent_data['gpm3'] = process_dict_values_into_list(
            dict(csv.reader(open(pos3currentdirectory + pos3gpmfile, 'w+', encoding="utf-8", newline=''))))
        self.gpmcurrent_data['gpm4'] = process_dict_values_into_list(
            dict(csv.reader(open(pos4currentdirectory + pos4gpmfile, 'w+', encoding="utf-8", newline=''))))
        self.gpmcurrent_data['gpm5'] = process_dict_values_into_list(
            dict(csv.reader(open(pos5currentdirectory + pos5gpmfile, 'w+', encoding="utf-8", newline=''))))

        self.kdacurrent_data['kda1'] = process_dict_values_into_list(
            dict(csv.reader(open(pos1currentdirectory + pos1kdafile, 'w+', encoding="utf-8", newline=''))))
        self.kdacurrent_data['kda2'] = process_dict_values_into_list(
            dict(csv.reader(open(pos2currentdirectory + pos2kdafile, 'w+', encoding="utf-8", newline=''))))
        self.kdacurrent_data['kda3'] = process_dict_values_into_list(
            dict(csv.reader(open(pos3currentdirectory + pos3kdafile, 'w+', encoding="utf-8", newline=''))))
        self.kdacurrent_data['kda4'] = process_dict_values_into_list(
            dict(csv.reader(open(pos4currentdirectory + pos4kdafile, 'w+', encoding="utf-8", newline=''))))
        self.kdacurrent_data['kda5'] = process_dict_values_into_list(
            dict(csv.reader(open(pos5currentdirectory + pos5kdafile, 'w+', encoding="utf-8", newline=''))))

        self.fantasycurrent_data['fantasy1'] = process_dict_values_into_list(
            dict(csv.reader(open(pos1currentdirectory + pos1fantasyfile, 'w+', encoding="utf-8", newline=''))))
        self.fantasycurrent_data['fantasy2'] = process_dict_values_into_list(
            dict(csv.reader(open(pos2currentdirectory + pos2fantasyfile, 'w+', encoding="utf-8", newline=''))))
        self.fantasycurrent_data['fantasy3'] = process_dict_values_into_list(
            dict(csv.reader(open(pos3currentdirectory + pos3fantasyfile, 'w+', encoding="utf-8", newline=''))))
        self.fantasycurrent_data['fantasy4'] = process_dict_values_into_list(
            dict(csv.reader(open(pos4currentdirectory + pos4fantasyfile, 'w+', encoding="utf-8", newline=''))))
        self.fantasycurrent_data['fantasy5'] = process_dict_values_into_list(
            dict(csv.reader(open(pos5currentdirectory + pos5fantasyfile, 'w+', encoding="utf-8", newline=''))))

        matches_size = len(match_ids)
        for match_index, matchid in enumerate(match_ids):
            json_data = self.request_opendota(opendota_api_matches_url + matchid)

            radiant_players = {
              'pos1' : None,
              'pos2' : None,
              'pos3' : None,
              'pos4' : None,
              'pos5' : None
            }

            dire_players = {
              'pos1' : None,
              'pos2' : None,
              'pos3' : None,
              'pos4' : None,
              'pos5' : None
            }

            # Sometimes Open dota API can have 500 status, in that case break out
            try:
                json_data['players']
            except KeyError:
                print("Internal server error for match ID: " + matchid)
                return

            # TODO: Refactor so that code is not repeated
            for player in json_data['players']:
                # if player == 80718533
                    # print 'Shit'
                if player['isRadiant']:
                    # Happens sometimes, player cannot be parsed. Just skip
                    if "lane" not in player:
                        continue
                    if player['lane'] == 1:
                        if radiant_players['pos1'] is None:
                            radiant_players['pos1'] = player
                        else:
                            if radiant_players['pos1']['lh_t'][11] < player["lh_t"][11]:
                                radiant_players['pos5'] = radiant_players['pos1']
                                radiant_players['pos1'] = player
                            else:
                                radiant_players['pos5'] = player
                    elif player['lane'] == 2:
                        if radiant_players['pos2'] is None:
                            radiant_players['pos2'] = player
                        elif radiant_players['pos2']['lh_t'][11] < player['lh_t'][11]:
                            if radiant_players['pos4'] is None:
                                radiant_players['pos4'] = radiant_players['pos2']
                                radiant_players['pos2'] = player
                            elif radiant_players['pos4'] is not None:
                                if radiant_players['pos4']['lh_t'][11] < radiant_players['pos2']['lh_t'][11]:
                                    radiant_players['pos5'] = radiant_players['pos4']
                                    radiant_players['pos4'] = radiant_players['pos2']
                                    radiant_players['pos2'] = player
                                else:
                                    radiant_players['pos5'] = radiant_players['pos2']
                                    radiant_players['pos2'] = player
                            elif radiant_players['pos5'] is not None:
                                if radiant_players['pos5']['lh_t'][11] > radiant_players['pos2']['lh_t'][11]:
                                    radiant_players['pos4'] = radiant_players['pos5']
                                    radiant_players['pos5'] = radiant_players['pos2']
                            else:
                                radiant_players['pos4'] = radiant_players['pos2']
                                radiant_players['pos2'] = player
                        else:
                            radiant_players['pos4'] = player
                    elif player['lane'] == 3:
                        if radiant_players['pos3'] is None:
                            radiant_players['pos3'] = player
                        else:
                            if radiant_players['pos3']['lh_t'][11] < player['lh_t'][11]:
                                radiant_players['pos4'] = radiant_players['pos3']
                                radiant_players['pos3'] = player
                            else:
                                radiant_players['pos4'] = player
                else:
                    if "lane" not in player:
                        continue
                    if player['lane'] == 1:
                        if dire_players['pos3'] is None:
                            dire_players['pos3'] = player
                        else:
                            if dire_players['pos3']['lh_t'][11] < player['lh_t'][11]:
                                dire_players['pos4'] = dire_players['pos3']
                                dire_players['pos3'] = player
                            else:
                                dire_players['pos4'] = player
                    elif player['lane'] == 2:
                        if dire_players['pos2'] is None:
                            dire_players['pos2'] = player
                        elif dire_players['pos2']['lh_t'][11] < player['lh_t'][11]:
                            if dire_players['pos4'] is None:
                                dire_players['pos4'] = dire_players['pos2']
                                dire_players['pos2'] = player
                            elif dire_players['pos4'] is not None:
                                if dire_players['pos4']['lh_t'][11] < dire_players['pos2']['lh_t'][11]:
                                    dire_players['pos5'] = dire_players['pos4']
                                    dire_players['pos4'] = dire_players['pos2']
                                    dire_players['pos2'] = player
                                else:
                                    dire_players['pos5'] = dire_players['pos2']
                                    dire_players['pos2'] = player
                            elif dire_players['pos5'] is not None:
                                if dire_players['pos5']['lh_t'][11] > dire_players['pos2']['lh_t'][11]:
                                    dire_players['pos4'] = dire_players['pos5']
                                    dire_players['pos5'] = dire_players['pos2']
                            else:
                                dire_players['pos4'] = dire_players['pos2']
                                dire_players['pos2'] = player
                        else:
                            dire_players['pos4'] = player
                    elif player['lane'] == 3:
                        if dire_players['pos1'] is None:
                            dire_players['pos1'] = player
                        else:
                            if dire_players['pos1']['lh_t'][11] < player['lh_t'][11]:
                                dire_players['pos5'] = dire_players['pos1']
                                dire_players['pos1'] = player
                            else:
                                dire_players['pos5'] = player

            # For any unfilled pos (Maybe because they jungled???) Fill them in to remaining slot
            for index, each in enumerate(
                    [radiant_players['pos1'], dire_players['pos1'], radiant_players['pos2'], dire_players['pos2'], radiant_players['pos3'], dire_players['pos3'], radiant_players['pos4'],
                     dire_players['pos4'], radiant_players['pos5'], dire_players['pos5']]):
                if each is None:
                    diff = list_difference(json_data['players'],
                                           [radiant_players['pos1'], dire_players['pos1'], radiant_players['pos2'], dire_players['pos2'], radiant_players['pos3'],
                                            dire_players['pos3'],
                                            radiant_players['pos4'], dire_players['pos4'], radiant_players['pos5'], dire_players['pos5']])
                    if index == 0:
                        radiant_players['pos1'] = diff[0]
                    elif index == 1:
                        dire_players['pos1'] = diff[0]
                    elif index == 2:
                        radiant_players['pos2'] = diff[0]
                    elif index == 3:
                        dire_players['pos2'] = diff[0]
                    elif index == 4:
                        radiant_players['pos3'] = diff[0]
                    elif index == 5:
                        dire_players['pos3'] = diff[0]
                    elif index == 6:
                        radiant_players['pos4'] = diff[0]
                    elif index == 7:
                        dire_players['pos4'] = diff[0]
                    elif index == 8:
                        radiant_players['pos5'] = diff[0]
                    elif index == 9:
                        dire_players['pos5'] = diff[0]

            # Parse response to add stat to each relevant dictionary based on role
            # TODO: Refactor to avoid code duplication
            for i in range(1, 6): 
                for player in [radiant_players['pos' + str(i)], dire_players['pos' + str(i)]]:
                    if str(player["account_id"]) in self.gpmcurrent_data['gpm' + str(i)]:
                        if isinstance(self.gpmcurrent_data['gpm' + str(i)][str(player["account_id"])], str):
                            evalList = ast.literal_eval(self.gpmcurrent_data['gpm' + str(i)][str(player["account_id"])])
                        else:
                            evalList = self.gpmcurrent_data['gpm' + str(i)][str(player["account_id"])]
                        self.gpmcurrent_data['gpm' + str(i)][str(player["account_id"])] = [
                            ((evalList[0] * evalList[1]) + player["gold_per_min"]) / (evalList[1] + 1), evalList[1] + 1]
                    else:
                        self.gpmcurrent_data['gpm' + str(i)][str(player["account_id"])] = [player["gold_per_min"], 1]

                    if str(player["account_id"]) in self.gpm_data['gpm' + str(i)]:
                        if isinstance(self.gpm_data['gpm' + str(i)][str(player["account_id"])], str):
                            evalList = ast.literal_eval(self.gpm_data['gpm' + str(i)][str(player["account_id"])])
                        else:
                            evalList = self.gpm_data['gpm' + str(i)][str(player["account_id"])]
                        self.gpm_data['gpm' + str(i)][str(player["account_id"])] = [
                            ((evalList[0] * evalList[1]) + player["gold_per_min"]) / (evalList[1] + 1), evalList[1] + 1]
                    else:
                        self.gpm_data['gpm' + str(i)][str(player["account_id"])] = [player["gold_per_min"], 1]

                    if str(player["account_id"]) in self.kdacurrent_data['kda' + str(i)]:
                        if isinstance(self.kdacurrent_data['kda' + str(i)][str(player["account_id"])], str):
                            evalList = ast.literal_eval(self.kdacurrent_data['kda' + str(i)][str(player["account_id"])])
                        else:
                            evalList = self.kdacurrent_data['kda' + str(i)][str(player["account_id"])]
                        self.kdacurrent_data['kda' + str(i)][str(player["account_id"])] = [
                            ((evalList[0] * evalList[1]) + player["kda"]) / (evalList[1] + 1), evalList[1] + 1]
                    else:
                        self.kdacurrent_data['kda' + str(i)][str(player["account_id"])] = [player["kda"], 1]

                    if str(player["account_id"]) in self.kda_data['kda' + str(i)]:
                        if isinstance(self.kda_data['kda' + str(i)][str(player["account_id"])], str):
                            evalList = ast.literal_eval(self.kda_data['kda' + str(i)][str(player["account_id"])])
                        else:
                            evalList = self.kda_data['kda' + str(i)][str(player["account_id"])]
                        self.kda_data['kda' + str(i)][str(player["account_id"])] = [
                            ((evalList[0] * evalList[1]) + player["kda"]) / (evalList[1] + 1),
                            evalList[1] + 1]
                    else:
                        self.kda_data['kda' + str(i)][str(player["account_id"])] = [player["kda"], 1]

                    if str(player["account_id"]) in self.fantasycurrent_data['fantasy' + str(i)]:
                        if isinstance(self.fantasycurrent_data['fantasy' + str(i)][str(player["account_id"])], str):
                            evalList = ast.literal_eval(self.fantasycurrent_data['fantasy' + str(i)][str(player["account_id"])])
                        else:
                            evalList = self.fantasycurrent_data['fantasy' + str(i)][str(player["account_id"])]
                        self.fantasycurrent_data['fantasy' + str(i)][str(player["account_id"])] = [
                            ((evalList[0] * evalList[1]) + self.get_fantasy_score(player)) / (evalList[1] + 1), evalList[1] + 1]
                    else:
                        self.fantasycurrent_data['fantasy' + str(i)][str(player["account_id"])] = [self.get_fantasy_score(player), 1]

                    if str(player["account_id"]) in self.fantasy_data['fantasy' + str(i)]:
                        if isinstance(self.fantasy_data['fantasy' + str(i)][str(player["account_id"])], str):
                            evalList = ast.literal_eval(self.fantasy_data['fantasy' + str(i)][str(player["account_id"])])
                        else:
                            evalList = self.fantasy_data['fantasy' + str(i)][str(player["account_id"])]
                        self.fantasy_data['fantasy' + str(i)][str(player["account_id"])] = [
                            ((evalList[0] * evalList[1]) + self.get_fantasy_score(player)) / (evalList[1] + 1),
                            evalList[1] + 1]
                    else:
                        try:
                            self.fantasy_data['fantasy' + str(i)][str(player["account_id"])] = [self.get_fantasy_score(player), 1]
                        except:
                            print("Failed in getting fantasy score")

            for player in json_data['players']:
                if player['gold_per_min'] > self.highest_gpm_value:
                    self.highest_gpm_value = player['gold_per_min']
                    self.highest_gpm_player = player['account_id']
                    self.highest_gpm_hero = player['hero_id']
                    self.highest_gpm_match = dotabuff_url + str(json_data['match_id'])
                if player['xp_per_min'] > self.highest_xpm_value:
                    self.highest_xpm_value = player['xp_per_min']
                    self.highest_xpm_player = player['account_id']
                    self.highest_xpm_hero = player['hero_id']
                    self.highest_xpm_match = dotabuff_url + str(json_data['match_id'])
                if player['kda'] > self.highest_kda_value:
                    self.highest_kda_value = player['kda']
                    self.highest_kda_player = player['account_id']
                    self.highest_kda_hero = player['hero_id']
                    self.highest_kda_match = dotabuff_url + str(json_data['match_id'])
                if player['camps_stacked'] is not None and player['camps_stacked'] > self.highest_camps_value:
                    self.highest_camps_value = player['camps_stacked']
                    self.highest_camps_player = player['account_id']
                    self.highest_camps_hero = player['hero_id']
                    self.highest_camps_match = dotabuff_url + str(json_data['match_id'])
                if player['hero_damage'] > self.highest_herodamage_value:
                    self.highest_herodamage_value = player['hero_damage']
                    self.highest_herodamage_player = player['account_id']
                    self.highest_herodamage_hero = player['hero_id']
                    self.highest_herodamage_match = dotabuff_url + str(json_data['match_id'])
                if player['stuns'] is not None and player['stuns'] > self.highest_stuns_value:
                    self.highest_stuns_value = player['stuns']
                    self.highest_stuns_player = player['account_id']
                    self.highest_stuns_hero = player['hero_id']
                    self.highest_stuns_match = dotabuff_url + str(json_data['match_id'])
                if player['tower_damage'] is not None and player['tower_damage'] > self.highest_towerdamage_value:
                    self.highest_towerdamage_value = player['tower_damage']
                    self.highest_towerdamage_player = player['account_id']
                    self.highest_towerdamage_hero = player['hero_id']
                    self.highest_towerdamage_match = dotabuff_url + str(json_data['match_id'])
                if 'lane_efficiency' in player and player['lane_efficiency'] > self.highest_lane_value:
                    self.highest_lane_value = player['lane_efficiency']
                    self.highest_lane_player = player['account_id']
                    self.highest_lane_hero = player['hero_id']
                    self.highest_lane_match = dotabuff_url + str(json_data['match_id'])
                if 'observer_kills' in player and 'sentry_kills' in player and player['observer_kills'] is not None and \
                        player['sentry_kills'] is not None and (
                        player['observer_kills'] + player['sentry_kills']) > self.highest_deward_value:
                    self.highest_deward_value = (player['observer_kills'] + player['sentry_kills'])
                    self.highest_deward_player = player['account_id']
                    self.highest_deward_hero = player['hero_id']
                    self.highest_deward_match = dotabuff_url + str(json_data['match_id'])
                if 'courier_kills' in player and player['courier_kills'] > self.highest_courier_value:
                    self.highest_courier_value = player['courier_kills']
                    self.highest_courier_player = player['account_id']
                    self.highest_courier_hero = player['hero_id']
                    self.highest_courier_match = dotabuff_url + str(json_data['match_id'])
                if 'deaths' in player and player['deaths'] > self.highest_deaths_value:
                    self.highest_deaths_value = player['deaths']
                    self.highest_deaths_player = player['account_id']
                    self.highest_deaths_hero = player['hero_id']
                    self.highest_deaths_match = dotabuff_url + str(json_data['match_id'])
                # if 'actions_per_min' in player and player['actions_per_min'] > self.highest_apm_value:
                #     self.highest_apm_value = player['actions_per_min']
                #     self.highest_apm_player = player['account_id']
                #     self.highest_apm_hero = player['hero_id']
                #     self.highest_apm_match = dotabuff_url + str(json_data['match_id'])
            print("Processed match {} of {} with ID: {}".format(match_index + 1, matches_size, matchid))

        json_data = self.request_opendota(opendota_api_players_url + str(self.highest_gpm_player))

        self.stats_leaders_dict["gpm"] = {"name": (json_data['profile']['name'] if json_data['profile']['name'] != None
                                                   else json_data['profile']['personaname']),
                                          "avatar": json_data['profile']['avatarmedium'],
                                          "hero": self.highest_gpm_hero,
                                          "match": self.highest_gpm_match,
                                          "value": self.highest_gpm_value}

        json_data = self.request_opendota(opendota_api_players_url + str(self.highest_xpm_player))
        self.stats_leaders_dict["xpm"] = {"name": (json_data['profile']['name'] if json_data['profile']['name'] != None
                                                   else json_data['profile']['personaname']),
                                          "avatar": json_data['profile']['avatarmedium'],
                                          "hero": self.highest_xpm_hero,
                                          "match": self.highest_xpm_match,
                                          "value": self.highest_xpm_value}

        json_data = self.request_opendota(opendota_api_players_url + str(self.highest_kda_player))
        self.stats_leaders_dict["kda"] = {"name": (json_data['profile']['name'] if json_data['profile']['name'] != None
                                                   else json_data['profile']['personaname']),
                                          "avatar": json_data['profile']['avatarmedium'],
                                          "hero": self.highest_kda_hero,
                                          "match": self.highest_kda_match,
                                          "value": self.highest_kda_value}

        jdson_data = self.request_opendota(opendota_api_players_url + str(self.highest_camps_player))
        self.stats_leaders_dict["camps"] = {
            "name": (json_data['profile']['name'] if json_data['profile']['name'] != None
                     else json_data['profile']['personaname']),
            "avatar": json_data['profile']['avatarmedium'],
            "hero": self.highest_camps_hero,
            "match": self.highest_camps_match,
            "value": self.highest_camps_value}

        json_data = self.request_opendota(opendota_api_players_url + str(self.highest_herodamage_player))
        self.stats_leaders_dict["herodamage"] = {
            "name": (json_data['profile']['name'] if json_data['profile']['name'] != None
                     else json_data['profile']['personaname']),
            "avatar": json_data['profile']['avatarmedium'],
            "hero": self.highest_herodamage_hero,
            "match": self.highest_herodamage_match,
            "value": self.highest_herodamage_value}

        json_data = self.request_opendota(opendota_api_players_url + str(self.highest_stuns_player))
        self.stats_leaders_dict["stuns"] = {
            "name": (json_data['profile']['name'] if json_data['profile']['name'] != None
                     else json_data['profile']['personaname']),
            "avatar": json_data['profile']['avatarmedium'],
            "hero": self.highest_stuns_hero,
            "match": self.highest_stuns_match,
            "value": self.highest_stuns_value}

        json_data = self.request_opendota(opendota_api_players_url + str(self.highest_towerdamage_player))
        self.stats_leaders_dict["towerdamage"] = {
            "name": (json_data['profile']['name'] if json_data['profile']['name'] != None
                     else json_data['profile']['personaname']),
            "avatar": json_data['profile']['avatarmedium'],
            "hero": self.highest_towerdamage_hero,
            "match": self.highest_towerdamage_match,
            "value": self.highest_towerdamage_value}

        json_data = self.request_opendota(opendota_api_players_url + str(self.highest_lane_player))
        self.stats_leaders_dict["lane"] = {"name": (json_data['profile']['name'] if json_data['profile']['name'] != None
                                                    else json_data['profile']['personaname']),
                                           "avatar": json_data['profile']['avatarmedium'],
                                           "hero": self.highest_lane_hero,
                                           "match": self.highest_lane_match,
                                           "value": self.highest_lane_value}

        json_data = self.request_opendota(opendota_api_players_url + str(self.highest_deward_player))
        self.stats_leaders_dict["deward"] = {
            "name": (json_data['profile']['name'] if json_data['profile']['name'] != None
                     else json_data['profile']['personaname']),
            "avatar": json_data['profile']['avatarmedium'],
            "hero": self.highest_deward_hero,
            "match": self.highest_deward_match,
            "value": self.highest_deward_value}

        json_data = self.request_opendota(opendota_api_players_url + str(self.highest_deaths_player))
        self.stats_leaders_dict["deaths"] = {
            "name": (json_data['profile']['name'] if json_data['profile']['name'] != None
                     else json_data['profile']['personaname']),
            "avatar": json_data['profile']['avatarmedium'],
            "hero": self.highest_deaths_hero,
            "match": self.highest_deaths_match,
            "value": self.highest_deaths_value}

        # json_data = self.request_opendota(opendota_api_players_url + str(self.highest_apm_player))
        # self.stats_leaders_dict["apm"] = {"name": (json_data['profile']['name'] if json_data['profile']['name'] != None
        #                                            else json_data['profile']['personaname']),
        #                                   "avatar": json_data['profile']['avatarmedium'],
        #                                   "hero": self.highest_apm_hero,
        #                                   "match": self.highest_apm_match,
        #                                   "value": self.highest_apm_value}

        json_data = self.request_opendota(opendota_api_players_url + str(self.highest_courier_player))
        self.stats_leaders_dict["courier"] = {
            "name": (json_data['profile']['name'] if json_data['profile']['name'] != None
                     else json_data['profile']['personaname']),
            "avatar": json_data['profile']['avatarmedium'],
            "hero": self.highest_courier_hero,
            "match": self.highest_courier_match,
            "value": self.highest_courier_value}

        json_data = self.request_opendota(opendota_api_players_url + str(self.highest_deaths_player))
        self.stats_leaders_dict["deaths"] = {
            "name": (json_data['profile']['name'] if json_data['profile']['name'] != None
                     else json_data['profile']['personaname']), 
            "avatar": json_data['profile']['avatarmedium'],
            "hero": self.highest_deaths_hero,
            "match": self.highest_deaths_match,
            "value": self.highest_deaths_value}

        stats_leaders_file = open('stats_leaders.csv', 'r+', encoding="utf-8", newline='')
        stats_leaders_file_writer = csv.writer(stats_leaders_file)
        for k, v in self.stats_leaders_dict.items():
            stats_leaders_file_writer.writerow([k, v])
        stats_leaders_file.close()

        print("Generated stats leaders file.")
        print("Creating position based stat files...")

        write_to_pos_based_csv_files_current_week(self.gpmcurrent_data['gpm1'], self.kdacurrent_data['kda1'], self.fantasycurrent_data['fantasy1'],
                                     self.gpmcurrent_data['gpm2'], self.kdacurrent_data['kda2'], self.fantasycurrent_data['fantasy2'],
                                     self.gpmcurrent_data['gpm3'], self.kdacurrent_data['kda3'], self.fantasycurrent_data['fantasy3'],
                                     self.gpmcurrent_data['gpm4'], self.kdacurrent_data['kda4'], self.fantasycurrent_data['fantasy4'],
                                     self.gpmcurrent_data['gpm5'], self.kdacurrent_data['kda5'], self.fantasycurrent_data['fantasy5'])

        write_to_pos_based_csv_files(self.gpm_data['gpm1'], self.kda_data['kda1'], self.fantasy_data['fantasy1'],
                                     self.gpm_data['gpm2'], self.kda_data['kda2'], self.fantasy_data['fantasy2'],
                                     self.gpm_data['gpm3'], self.kda_data['kda3'], self.fantasy_data['fantasy3'],
                                     self.gpm_data['gpm4'], self.kda_data['kda4'], self.fantasy_data['fantasy4'],
                                     self.gpm_data['gpm5'], self.kda_data['kda5'], self.fantasy_data['fantasy5'])

rd2lstats = Rd2lStats()

# Function invoked when bot is live
@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


# Function invoked when user sends message
@client.event
async def on_message(message):
    if message.author.id not in ADMIN_IDS:
        return

    # Find duplicates for a single player across multiple roles
    if message.content.startswith('$bot_find_duplicates'):
        rd2lstats.find_duplicates()

    # Find duplicates for a single player across multiple roles
    if message.content.startswith('$bot_clear_files'):
        empty_all_stat_files()

    # Swap two players roles in data
    if message.content.startswith('$bot_swap_players'):
        rd2lstats.swap_players()

    # Generate stats will generate stats without printing them out, used for debugging
    if message.content.startswith('$bot_generate_stats'):
        print('Generating stats...')
        rd2lstats.generate_stats()

    # Prints out stats in discord embeds
    if message.content.startswith('$bot_get_stats'):
        gpm1 = process_dict_values_into_list(
            dict(csv.reader(open(pos1directory + pos1gpmfile, 'r', encoding="utf-8", newline=''))))
        gpm2 = process_dict_values_into_list(
            dict(csv.reader(open(pos2directory + pos2gpmfile, 'r', encoding="utf-8", newline=''))))
        gpm3 = process_dict_values_into_list(
            dict(csv.reader(open(pos3directory + pos3gpmfile, 'r', encoding="utf-8", newline=''))))
        gpm4 = process_dict_values_into_list(
            dict(csv.reader(open(pos4directory + pos4gpmfile, 'r', encoding="utf-8", newline=''))))
        gpm5 = process_dict_values_into_list(
            dict(csv.reader(open(pos5directory + pos5gpmfile, 'r', encoding="utf-8", newline=''))))

        kda1 = process_dict_values_into_list(
            dict(csv.reader(open(pos1directory + pos1kdafile, 'r', encoding="utf-8", newline=''))))
        kda2 = process_dict_values_into_list(
            dict(csv.reader(open(pos2directory + pos2kdafile, 'r', encoding="utf-8", newline=''))))
        kda3 = process_dict_values_into_list(
            dict(csv.reader(open(pos3directory + pos3kdafile, 'r', encoding="utf-8", newline=''))))
        kda4 = process_dict_values_into_list(
            dict(csv.reader(open(pos4directory + pos4kdafile, 'r', encoding="utf-8", newline=''))))
        kda5 = process_dict_values_into_list(
            dict(csv.reader(open(pos5directory + pos5kdafile, 'r', encoding="utf-8", newline=''))))

        fantasy1 = process_dict_values_into_list(
            dict(csv.reader(open(pos1directory + pos1fantasyfile, 'r', encoding="utf-8", newline=''))))
        fantasy2 = process_dict_values_into_list(
            dict(csv.reader(open(pos2directory + pos2fantasyfile, 'r', encoding="utf-8", newline=''))))
        fantasy3 = process_dict_values_into_list(
            dict(csv.reader(open(pos3directory + pos3fantasyfile, 'r', encoding="utf-8", newline=''))))
        fantasy4 = process_dict_values_into_list(
            dict(csv.reader(open(pos4directory + pos4fantasyfile, 'r', encoding="utf-8", newline=''))))
        fantasy5 = process_dict_values_into_list(
            dict(csv.reader(open(pos5directory + pos5fantasyfile, 'r', encoding="utf-8", newline=''))))

        stats_leaders_dict = process_dict_values_into_list(
            dict(csv.reader(open('stats_leaders.csv', 'r', encoding="utf-8", newline=''))))

        print('Finished processing stats files')

        # Find number of games played in season this far
        games_played = update_current_week(gpm2)
        threshold_wrapper = lambda item: passes_role_threshold(item, games_played)

        # TODO: Add better names for embeds
        embeds = {}
        embeds[1] = discord.Embed(title="Highest GPM", colour=discord.Colour(0x1),
                              description=stats_leaders_dict['gpm']['name'])
        embeds[1].set_image(url="{}{}.png".format(steam_cdn, get_hero_name(stats_leaders_dict['gpm']['hero'])))
        embeds[1].set_thumbnail(url=stats_leaders_dict['gpm']['avatar'])
        embeds[1].add_field(name="GPM", value=stats_leaders_dict['gpm']['value'])
        embeds[1].add_field(name="MatchID", value="{}".format(stats_leaders_dict["gpm"]["match"],
                                                                stats_leaders_dict["gpm"]["match"]))

        print('Processed Highest GPM')

        embeds[2] = discord.Embed(title="Highest XPM", colour=discord.Colour(0x1),
                               description=stats_leaders_dict['xpm']['name'])
        embeds[2].set_image(url="{}{}.png".format(steam_cdn, get_hero_name(stats_leaders_dict['xpm']['hero'])))
        embeds[2].set_thumbnail(url=stats_leaders_dict['xpm']['avatar'])
        embeds[2].add_field(name="XPM", value=stats_leaders_dict['xpm']['value'])
        embeds[2].add_field(name="MatchID", value="{}".format(stats_leaders_dict["xpm"]["match"]))

        print('Processed Highest XPM')

        embeds[3] = discord.Embed(title="Highest KDA", colour=discord.Colour(0x1),
                               description=stats_leaders_dict['kda']['name'])
        embeds[3].set_image(url="{}{}.png".format(steam_cdn, get_hero_name(stats_leaders_dict['kda']['hero'])))
        embeds[3].set_thumbnail(url=stats_leaders_dict['kda']['avatar'])
        embeds[3].add_field(name="KDA", value=stats_leaders_dict['kda']['value'])
        embeds[3].add_field(name="MatchID", value="{}".format(stats_leaders_dict["kda"]["match"]))

        print('Processed Highest KDA')

        embeds[4] = discord.Embed(title="Highest Hero damage", colour=discord.Colour(0x1),
                               description=stats_leaders_dict['herodamage']['name'])
        embeds[4].set_image(url="{}{}.png".format(steam_cdn, get_hero_name(stats_leaders_dict['herodamage']['hero'])))
        embeds[4].set_thumbnail(url=stats_leaders_dict['herodamage']['avatar'])
        embeds[4].add_field(name="Damage", value=stats_leaders_dict['herodamage']['value'])
        embeds[4].add_field(name="MatchID", value="{}".format(stats_leaders_dict["herodamage"]["match"]))

        print('Processed Highest Hero Damage')

        embeds[5] = discord.Embed(title="Highest Stun time", colour=discord.Colour(0x1),
                               description=stats_leaders_dict['stuns']['name'])
        embeds[5].set_image(url="{}{}.png".format(steam_cdn, get_hero_name(stats_leaders_dict['stuns']['hero'])))
        embeds[5].set_thumbnail(url=stats_leaders_dict['stuns']['avatar'])
        embeds[5].add_field(name="Stun time", value=round(stats_leaders_dict['stuns']['value'], 2))
        embeds[5].add_field(name="MatchID", value="{}".format(stats_leaders_dict["stuns"]["match"]))

        print('Processed Highest Stun Time')

        embeds[6] = discord.Embed(title="Most camps stacked", colour=discord.Colour(0x1),
                               description=stats_leaders_dict['camps']['name'])
        embeds[6].set_image(url="{}{}.png".format(steam_cdn, get_hero_name(stats_leaders_dict['camps']['hero'])))
        embeds[6].set_thumbnail(url=stats_leaders_dict['camps']['avatar'])
        embeds[6].add_field(name="Camps stacked", value=stats_leaders_dict['camps']['value'])
        embeds[6].add_field(name="MatchID", value="{}".format(stats_leaders_dict["camps"]["match"]))

        print('Processed Most Camps Stacked')

        embeds[7] = discord.Embed(title="Highest Tower damage", colour=discord.Colour(0x1),
                               description=stats_leaders_dict['towerdamage']['name'])
        embeds[7].set_image(url="{}{}.png".format(steam_cdn, get_hero_name(stats_leaders_dict['towerdamage']['hero'])))
        embeds[7].set_thumbnail(url=stats_leaders_dict['towerdamage']['avatar'])
        embeds[7].add_field(name="Damage", value=stats_leaders_dict['towerdamage']['value'])
        embeds[7].add_field(name="MatchID", value="{}".format(stats_leaders_dict["towerdamage"]["match"]))

        print('Processed Highest Tower Damage')

        embeds[8] = discord.Embed(title="Best lane efficiency", colour=discord.Colour(0x1),
                               description=stats_leaders_dict['lane']['name'])
        embeds[8].set_image(url="{}{}.png".format(steam_cdn, get_hero_name(stats_leaders_dict['lane']['hero'])))
        embeds[8].set_thumbnail(url=stats_leaders_dict['lane']['avatar'])
        embeds[8].add_field(name="Efficiency", value=round(stats_leaders_dict['lane']['value'], 2))
        embeds[8].add_field(name="MatchID", value="{}".format(stats_leaders_dict["lane"]["match"]))

        print('Processed Best Lane Efficiency')

        embeds[9] = discord.Embed(title="Highest dewards", colour=discord.Colour(0x1),
                               description=stats_leaders_dict['deward']['name'])
        embeds[9].set_image(url="{}{}.png".format(steam_cdn, get_hero_name(stats_leaders_dict['deward']['hero'])))
        embeds[9].set_thumbnail(url=stats_leaders_dict['deward']['avatar'])
        embeds[9].add_field(name="Dewards", value=stats_leaders_dict['deward']['value'])
        embeds[9].add_field(name="MatchID", value="{}".format(stats_leaders_dict["deward"]["match"]))

        print('Processed Highest Dewards')

        # embeds[10] = discord.Embed(title="Highest APM", colour=discord.Colour(0x1),
        #                         description=stats_leaders_dict['apm']['name'])
        # embeds[10].set_image(url="{}{}.png".format(steam_cdn, get_hero_name(stats_leaders_dict['apm']['hero'])))
        # embeds[10].set_thumbnail(url=stats_leaders_dict['apm']['avatar'])
        # embeds[10].add_field(name="APM", value=stats_leaders_dict['apm']['value'])
        # embeds[10].add_field(name="MatchID", value="[{}]({})".format(stats_leaders_dict["apm"]["match"],
        #                                                           stats_leaders_dict["apm"]["match"]))

        # print('Processed Highest APM')

        embeds[16] = discord.Embed(title="Highest Courier kills", colour=discord.Colour(0x1),
                                description=stats_leaders_dict['courier']['name'])
        embeds[16].set_image(url="{}{}.png".format(steam_cdn, get_hero_name(stats_leaders_dict['courier']['hero'])))
        embeds[16].set_thumbnail(url=stats_leaders_dict['courier']['avatar'])
        embeds[16].add_field(name="Couriers", value=stats_leaders_dict['courier']['value'])
        embeds[16].add_field(name="MatchID", value="{}".format(stats_leaders_dict["courier"]["match"]))

        embeds[17] = discord.Embed(title="Most Deaths", colour=discord.Colour(0x1),
                                description=stats_leaders_dict['deaths']['name'])
        embeds[17].set_image(url="{}{}.png".format(steam_cdn, get_hero_name(stats_leaders_dict['deaths']['hero'])))
        embeds[17].set_thumbnail(url=stats_leaders_dict['deaths']['avatar'])
        embeds[17].add_field(name="Deaths", value=stats_leaders_dict['deaths']['value'])
        embeds[17].add_field(name="MatchID", value='{}'.format(stats_leaders_dict["deaths"]["match"]))

        print('Processed Highest Courier Kills')

        for i in range(1, 6):
            filtered_gpm = copy.deepcopy({key: value for key, value in rd2lstats.gpm_data['gpm' + str(i)].items()})
            rounded_dict_gpm = {k: [round(v[0], 2), v[1]] for k, v in filtered_gpm.items()}
            sorted_dict_gpm = sorted(rounded_dict_gpm.items(), key=threshold_wrapper, reverse=True)[:player_ranking_cutoff]

            filtered_kda = copy.deepcopy({key: value for key, value in rd2lstats.kda_data['kda' + str(i)].items()})
            rounded_dict_kda = {k: [round(v[0], 2), v[1]] for k, v in filtered_kda.items()}
            sorted_dict_kda = sorted(rounded_dict_kda.items(), key=threshold_wrapper, reverse=True)[:player_ranking_cutoff]

            filtered_fantasy = copy.deepcopy({key: value for key, value in rd2lstats.fantasy_data['fantasy' + str(i)].items()})
            rounded_dict_fantasy = {k: [round(v[0], 2), v[1]] for k, v in filtered_fantasy.items()}
            sorted_dict_fantasy = sorted(rounded_dict_fantasy.items(), key=threshold_wrapper, reverse=True)[:player_ranking_cutoff]

            embeds[10 + i] = discord.Embed(title=f"Pos {i} Leaderboard", colour=discord.Colour(0x1))

            ranking = '\n'.join(f"{i + 1}." for i in range(player_ranking_cutoff))
            embeds[10 + i].add_field(name="Ranking", value=ranking, inline=True)

            player_names = '\n'.join(rd2lstats.get_player_name_for_account_id(player_id) for player_id, _ in sorted_dict_gpm)
            embeds[10 + i].add_field(name="Player", value=player_names, inline=True)

            gpm_values = '\n'.join(str(gpm[0]) for _, gpm in sorted_dict_gpm[:8])
            embeds[10 + i].add_field(name="GPM", value=gpm_values, inline=True)

            ranking = '\n'.join(f"{i + 1}." for i in range(player_ranking_cutoff))
            embeds[10 + i].add_field(name="Ranking", value=ranking, inline=True)

            player_names = '\n'.join(rd2lstats.get_player_name_for_account_id(player_id) for player_id, _ in sorted_dict_kda)
            embeds[10 + i].add_field(name="Player", value=player_names, inline=True)

            kda_values = '\n'.join(str(kda[0]) for _, kda in sorted_dict_kda[:8])
            embeds[10 + i].add_field(name="KDA", value=kda_values, inline=True)
     
            ranking = '\n'.join(f"{i + 1}." for i in range(player_ranking_cutoff))
            embeds[10 + i].add_field(name="Ranking", value=ranking, inline=True)

            player_names = '\n'.join(rd2lstats.get_player_name_for_account_id(player_id) for player_id, _ in sorted_dict_fantasy)
            embeds[10 + i].add_field(name="Player", value=player_names, inline=True)

            overall_performance_values = '\n'.join(str(round(performance_data[0], 2)) for _, performance_data in sorted_dict_fantasy[:8])
            embeds[10 + i].add_field(name="Overall performance", value=overall_performance_values, inline=True)

            print('Processed embed ' + str(10 + i))

        await message.channel.send(embed=embeds[1])
        await message.channel.send(embed=embeds[2])
        await message.channel.send(embed=embeds[3])
        await message.channel.send(embed=embeds[4])
        await message.channel.send(embed=embeds[5])
        await message.channel.send(embed=embeds[6])
        await message.channel.send(embed=embeds[7])
        await message.channel.send(embed=embeds[8])
        await message.channel.send(embed=embeds[9])
        # await message.channel.send(embed=embeds[10])
        await message.channel.send(embed=embeds[16])
        await message.channel.send(embed=embeds[17])

        await message.channel.send(embed=embeds[11])
        await message.channel.send(embed=embeds[12])
        await message.channel.send(embed=embeds[13])
        await message.channel.send(embed=embeds[14])
        await message.channel.send(embed=embeds[15])
        print("Sent stats successfully")

client.run(permissionkey)
