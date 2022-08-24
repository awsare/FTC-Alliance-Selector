import requests as r
import json as j
import passwords

import discord
from discord.ext import commands

USERNAME = passwords.USERNAME
PASSWORD = passwords.PASSWORD
TOKEN = passwords.TOKEN

PREFIX = "f."

client = commands.Bot(command_prefix = commands.when_mentioned_or(f"{PREFIX}"))
client.remove_command('help')

@client.event
async def on_ready():
    await client.change_presence(activity = discord.Activity(type = discord.ActivityType.listening, name = f"{PREFIX}help"))
    print("Bot is online")

@client.command()
async def stats(ctx, TEAMNUM, SEASON = None):

    if len(TEAMNUM) > 5:
        pass
    if not TEAMNUM.isnumeric():
        pass
    TEAMNUM = int(TEAMNUM)
    
    if SEASON == None:
        SEASON = 2021
    else:
        if len(SEASON) != 4:
            pass
        if not SEASON.isnumeric():
            pass
        SEASON = int(SEASON)

    events = r.get(f"https://ftc-api.firstinspires.org/v2.0/{SEASON}/events?teamNumber={TEAMNUM}", auth=(USERNAME, PASSWORD))
    events = events.text

    if "Malformed Parameter Format In Request" in events:
        pass

    events = j.loads(events)

    codes = []
    for event in events["events"]:
        codes.append(event["code"])

    scores = {}
    for event in codes:
        matches = r.get(f"http://ftc-api.firstinspires.org/v2.0/{SEASON}/matches/{event}", auth=(USERNAME, PASSWORD))
        matches = matches.text
        matches = j.loads(matches)

        for match in matches["matches"]:
            for team in match["teams"]:
                if team["teamNumber"] == TEAMNUM:
                    if team["station"] == "Red1":
                        if match["teams"][1]["teamNumber"] not in scores:
                            scores[match["teams"][1]["teamNumber"]] = {"Scores":[match["scoreRedFinal"]]}
                        else:
                            scores[match["teams"][1]["teamNumber"]]["Scores"].append(match["scoreRedFinal"])
                    elif team["station"] == "Red2":
                        if match["teams"][0]["teamNumber"] not in scores:
                            scores[match["teams"][0]["teamNumber"]] = {"Scores":[match["scoreRedFinal"]]}
                        else:
                            scores[match["teams"][0]["teamNumber"]]["Scores"].append(match["scoreRedFinal"])
                    elif team["station"] == "Blue1":
                        if match["teams"][3]["teamNumber"] not in scores:
                            scores[match["teams"][3]["teamNumber"]] = {"Scores":[match["scoreBlueFinal"]]}
                        else:
                            scores[match["teams"][3]["teamNumber"]]["Scores"].append(match["scoreBlueFinal"])
                    elif team["station"] == "Blue2":
                        if match["teams"][2]["teamNumber"] not in scores:
                            scores[match["teams"][2]["teamNumber"]] = {"Scores":[match["scoreBlueFinal"]]}
                        else:
                            scores[match["teams"][2]["teamNumber"]]["Scores"].append(match["scoreBlueFinal"])
                    continue
    
    for team, score in scores.items():
        total = 0
        highest = 0
        for num in score["Scores"]:
            total += num
            if num > highest:
                highest = num
        average = round(total / len(score["Scores"]), 2)
        scores[team]["Average"] = average
        scores[team]["Highest"] = highest
    
    print(j.dumps(scores, indent=2))


if __name__ == "__main__":
    client.run(TOKEN)