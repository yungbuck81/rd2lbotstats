import ast

# Function to calculate difference between two lists
import csv

from constants.globalConstants import pos1directory, pos1gpmfile, pos1kdafile, pos1fantasyfile, pos2gpmfile, \
    pos2directory, pos2kdafile, pos2fantasyfile, pos3directory, pos3gpmfile, pos3kdafile, pos3fantasyfile, \
    pos4directory, pos4gpmfile, pos4kdafile, pos4fantasyfile, pos5directory, pos5gpmfile, pos5kdafile, pos5fantasyfile, \
    pos1currentdirectory, pos2currentdirectory, pos3currentdirectory, pos4currentdirectory, pos5currentdirectory


def update_current_week(dict):
    games_played = 0
    filtered_dict = {key: value for key, value in dict.items()}
    for player in filtered_dict.items():
        games_played = max(games_played, player[1][1])
    return games_played

def list_difference(li1, li2):
    li_dif = [i for i in li1 if i not in li2]
    return li_dif


# Function to process a dictionary values into a list
def process_dict_values_into_list(dict1):
    new_dict = {}
    for key, value in dict1.items():
        try:
            new_dict[key] = ast.literal_eval(value)
        except IndentationError:
            print("test")
    return new_dict


# Function to find player in dictionaries
def find_player_in_dictionaries(player, dict1, dict2, dict3, dict4, dict5):
    if player in dict1:
        return dict1
    if player in dict2:
        return dict2
    if player in dict3:
        return dict3
    if player in dict4:
        return dict4
    if player in dict5:
        return dict5
    else:
        print("Player: {} was not found in any dictionary provided".format(player))
        return

# Calculate weighted average given a stat
def passes_role_threshold(stat, games_played):

    # Weight off-role players based on the number of games played
    if(stat[1][1] < 0.5 * games_played):
        games_played = stat[1][1]

    return stat[1][0] * games_played

# Function that takes in position based stats dictionaries and writes them to csv files for current week stats only
def write_to_pos_based_csv_files_current_week(gpm1, kda1, fantasy1,
                                 gpm2, kda2, fantasy2,
                                 gpm3, kda3, fantasy3,
                                 gpm4, kda4, fantasy4,
                                 gpm5, kda5, fantasy5):
    # TODO: Refactor this to be a function that can be reused
    gpm1_file = open(pos1currentdirectory + pos1gpmfile, 'w', encoding="utf-8", newline='')
    gpm1_writer = csv.writer(gpm1_file)
    for k, v in gpm1.items():
        gpm1_writer.writerow([k, v])
    gpm1_file.close()
    kda1_file = open(pos1currentdirectory + pos1kdafile, 'w', encoding="utf-8", newline='')
    kda1_writer = csv.writer(kda1_file)
    for k, v in kda1.items():
        kda1_writer.writerow([k, v])
    kda1_file.close()
    fantasy1_file = open(pos1currentdirectory + pos1fantasyfile, 'w', encoding="utf-8", newline='')
    fantasy1_writer = csv.writer(fantasy1_file)
    for k, v in fantasy1.items():
        fantasy1_writer.writerow([k, v])
    fantasy1_file.close()

    gpm2_file = open(pos2currentdirectory + pos2gpmfile, 'w', encoding="utf-8", newline='')
    gpm2_writer = csv.writer(gpm2_file)
    for k, v in gpm2.items():
        gpm2_writer.writerow([k, v])
    gpm2_file.close()
    kda2_file = open(pos2currentdirectory + pos2kdafile, 'w', encoding="utf-8", newline='')
    kda2_writer = csv.writer(kda2_file)
    for k, v in kda2.items():
        kda2_writer.writerow([k, v])
    kda2_file.close()
    fantasy2_file = open(pos2currentdirectory + pos2fantasyfile, 'w', encoding="utf-8", newline='')
    fantasy2_writer = csv.writer(fantasy2_file)
    for k, v in fantasy2.items():
        fantasy2_writer.writerow([k, v])
    fantasy2_file.close()

    gpm3_file = open(pos3currentdirectory + pos3gpmfile, 'w', encoding="utf-8", newline='')
    gpm3_writer = csv.writer(gpm3_file)
    for k, v in gpm3.items():
        gpm3_writer.writerow([k, v])
    gpm3_file.close()
    kda3_file = open(pos3currentdirectory + pos3kdafile, 'w', encoding="utf-8", newline='')
    kda3_writer = csv.writer(kda3_file)
    for k, v in kda3.items():
        kda3_writer.writerow([k, v])
    kda3_file.close()
    fantasy3_file = open(pos3currentdirectory + pos3fantasyfile, 'w', encoding="utf-8", newline='')
    fantasy3_writer = csv.writer(fantasy3_file)
    for k, v in fantasy3.items():
        fantasy3_writer.writerow([k, v])
    fantasy3_file.close()

    gpm4_file = open(pos4currentdirectory + pos4gpmfile, 'w', encoding="utf-8", newline='')
    gpm4_writer = csv.writer(gpm4_file)
    for k, v in gpm4.items():
        gpm4_writer.writerow([k, v])
    gpm4_file.close()
    kda4_file = open(pos4currentdirectory + pos4kdafile, 'w', encoding="utf-8", newline='')
    kda4_writer = csv.writer(kda4_file)
    for k, v in kda4.items():
        kda4_writer.writerow([k, v])
    kda4_file.close()
    fantasy4_file = open(pos4currentdirectory + pos4fantasyfile, 'w', encoding="utf-8", newline='')
    fantasy4_writer = csv.writer(fantasy4_file)
    for k, v in fantasy4.items():
        fantasy4_writer.writerow([k, v])
    fantasy4_file.close()

    gpm5_file = open(pos5currentdirectory + pos5gpmfile, 'w', encoding="utf-8", newline='')
    gpm5_writer = csv.writer(gpm5_file)
    for k, v in gpm5.items():
        gpm5_writer.writerow([k, v])
    gpm5_file.close()
    kda5_file = open(pos5currentdirectory + pos5kdafile, 'w', encoding="utf-8", newline='')
    kda5_writer = csv.writer(kda5_file)
    for k, v in kda5.items():
        kda5_writer.writerow([k, v])
    kda5_file.close()
    fantasy5_file = open(pos5currentdirectory + pos5fantasyfile, 'w', encoding="utf-8", newline='')
    fantasy5_writer = csv.writer(fantasy5_file)
    for k, v in fantasy5.items():
        fantasy5_writer.writerow([k, v])
    fantasy5_file.close()

    print("Writing to all files for current week finished.")

# Function that takes in position based stats dictionaries and writes them to csv files
def write_to_pos_based_csv_files(gpm1, kda1, fantasy1,
                                 gpm2, kda2, fantasy2,
                                 gpm3, kda3, fantasy3,
                                 gpm4, kda4, fantasy4,
                                 gpm5, kda5, fantasy5):
    # TODO: Refactor this to be a function that can be reused
    gpm1_file = open(pos1directory + pos1gpmfile, 'w', encoding="utf-8", newline='')
    gpm1_writer = csv.writer(gpm1_file)
    for k, v in gpm1.items():
        gpm1_writer.writerow([k, v])
    gpm1_file.close()
    kda1_file = open(pos1directory + pos1kdafile, 'w', encoding="utf-8", newline='')
    kda1_writer = csv.writer(kda1_file)
    for k, v in kda1.items():
        kda1_writer.writerow([k, v])
    kda1_file.close()
    fantasy1_file = open(pos1directory + pos1fantasyfile, 'w', encoding="utf-8", newline='')
    fantasy1_writer = csv.writer(fantasy1_file)
    for k, v in fantasy1.items():
        fantasy1_writer.writerow([k, v])
    fantasy1_file.close()

    gpm2_file = open(pos2directory + pos2gpmfile, 'w', encoding="utf-8", newline='')
    gpm2_writer = csv.writer(gpm2_file)
    for k, v in gpm2.items():
        gpm2_writer.writerow([k, v])
    gpm2_file.close()
    kda2_file = open(pos2directory + pos2kdafile, 'w', encoding="utf-8", newline='')
    kda2_writer = csv.writer(kda2_file)
    for k, v in kda2.items():
        kda2_writer.writerow([k, v])
    kda2_file.close()
    fantasy2_file = open(pos2directory + pos2fantasyfile, 'w', encoding="utf-8", newline='')
    fantasy2_writer = csv.writer(fantasy2_file)
    for k, v in fantasy2.items():
        fantasy2_writer.writerow([k, v])
    fantasy2_file.close()

    gpm3_file = open(pos3directory + pos3gpmfile, 'w', encoding="utf-8", newline='')
    gpm3_writer = csv.writer(gpm3_file)
    for k, v in gpm3.items():
        gpm3_writer.writerow([k, v])
    gpm3_file.close()
    kda3_file = open(pos3directory + pos3kdafile, 'w', encoding="utf-8", newline='')
    kda3_writer = csv.writer(kda3_file)
    for k, v in kda3.items():
        kda3_writer.writerow([k, v])
    kda3_file.close()
    fantasy3_file = open(pos3directory + pos3fantasyfile, 'w', encoding="utf-8", newline='')
    fantasy3_writer = csv.writer(fantasy3_file)
    for k, v in fantasy3.items():
        fantasy3_writer.writerow([k, v])
    fantasy3_file.close()

    gpm4_file = open(pos4directory + pos4gpmfile, 'w', encoding="utf-8", newline='')
    gpm4_writer = csv.writer(gpm4_file)
    for k, v in gpm4.items():
        gpm4_writer.writerow([k, v])
    gpm4_file.close()
    kda4_file = open(pos4directory + pos4kdafile, 'w', encoding="utf-8", newline='')
    kda4_writer = csv.writer(kda4_file)
    for k, v in kda4.items():
        kda4_writer.writerow([k, v])
    kda4_file.close()
    fantasy4_file = open(pos4directory + pos4fantasyfile, 'w', encoding="utf-8", newline='')
    fantasy4_writer = csv.writer(fantasy4_file)
    for k, v in fantasy4.items():
        fantasy4_writer.writerow([k, v])
    fantasy4_file.close()

    gpm5_file = open(pos5directory + pos5gpmfile, 'w', encoding="utf-8", newline='')
    gpm5_writer = csv.writer(gpm5_file)
    for k, v in gpm5.items():
        gpm5_writer.writerow([k, v])
    gpm5_file.close()
    kda5_file = open(pos5directory + pos5kdafile, 'w', encoding="utf-8", newline='')
    kda5_writer = csv.writer(kda5_file)
    for k, v in kda5.items():
        kda5_writer.writerow([k, v])
    kda5_file.close()
    fantasy5_file = open(pos5directory + pos5fantasyfile, 'w', encoding="utf-8", newline='')
    fantasy5_writer = csv.writer(fantasy5_file)
    for k, v in fantasy5.items():
        fantasy5_writer.writerow([k, v])
    fantasy5_file.close()

    print("Writing to all files finished.")

# Function that takes in position based stats dictionaries and writes them to csv files
def empty_all_stat_files():
    # TODO: Refactor this to be a function that can be reused
    gpm1_file = open(pos1directory + pos1gpmfile, 'w+', encoding="utf-8", newline='')
    gpm1_file.close()
    kda1_file = open(pos1directory + pos1kdafile, 'w+', encoding="utf-8", newline='')
    kda1_file.close()
    fantasy1_file = open(pos1directory + pos1fantasyfile, 'w+', encoding="utf-8", newline='')
    fantasy1_file.close()

    gpm2_file = open(pos2directory + pos2gpmfile, 'w+', encoding="utf-8", newline='')
    gpm2_file.close()
    kda2_file = open(pos2directory + pos2kdafile, 'w+', encoding="utf-8", newline='')
    kda2_file.close()
    fantasy2_file = open(pos2directory + pos2fantasyfile, 'w+', encoding="utf-8", newline='')
    fantasy2_file.close()

    gpm3_file = open(pos3directory + pos3gpmfile, 'w+', encoding="utf-8", newline='')
    gpm3_file.close()
    kda3_file = open(pos3directory + pos3kdafile, 'w+', encoding="utf-8", newline='')
    kda3_file.close()
    fantasy3_file = open(pos3directory + pos3fantasyfile, 'w+', encoding="utf-8", newline='')
    fantasy3_file.close()

    gpm4_file = open(pos4directory + pos4gpmfile, 'w+', encoding="utf-8", newline='')
    gpm4_file.close()
    kda4_file = open(pos4directory + pos4kdafile, 'w+', encoding="utf-8", newline='')
    kda4_file.close()
    fantasy4_file = open(pos4directory + pos4fantasyfile, 'w+', encoding="utf-8", newline='')
    fantasy4_file.close()

    gpm5_file = open(pos5directory + pos5gpmfile, 'w+', encoding="utf-8", newline='')
    gpm5_file.close()
    kda5_file = open(pos5directory + pos5kdafile, 'w+', encoding="utf-8", newline='')
    kda5_file.close()
    fantasy5_file = open(pos5directory + pos5fantasyfile, 'w+', encoding="utf-8", newline='')
    fantasy5_file.close()

    print("Emptied all files")
