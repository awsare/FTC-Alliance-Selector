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

THIS_SEASON = r.get("http://ftc-api.firstinspires.org/v2.0")
THIS_SEASON = j.loads(THIS_SEASON.text)
THIS_SEASON = THIS_SEASON["currentSeason"]

@client.event
async def on_ready():
    await client.change_presence(activity = discord.Activity(type = discord.ActivityType.listening, name = f"{PREFIX}help"))
    print("Bot is online")

@client.command()
async def stats(ctx, TEAMNUM, SEASON = None):

    if len(TEAMNUM) > 5:
        await ctx.send(embed=errorEmbed(ctx, "Team Number Error", "Team number must be five digits or less."))
        return
    if not TEAMNUM.isnumeric():
        await ctx.send(embed=errorEmbed(ctx, "Team Number Error", "Team number must be numeric."))
        return
    TEAMNUM = int(TEAMNUM)
    
    if SEASON == None:
        SEASON = THIS_SEASON
    else:
        if len(SEASON) != 4:
            await ctx.send(embed=errorEmbed(ctx, "Season Number Error", "Season number must be four digits."))
            return
        if not SEASON.isnumeric():
            await ctx.send(embed=errorEmbed(ctx, "Season Number Error", "Season number must be numeric."))
            return
        SEASON = int(SEASON)
        if SEASON < 2019 or SEASON > THIS_SEASON:
            await ctx.send(embed=errorEmbed(ctx, "Season Number Error", f"Season number must be between 2019 and {THIS_SEASON}"))
            return

    events = r.get(f"https://ftc-api.firstinspires.org/v2.0/{SEASON}/events?teamNumber={TEAMNUM}", auth=(USERNAME, PASSWORD))
    events = events.text

    if "Malformed Parameter Format In Request" in events:
        await ctx.send(embed=errorEmbed(ctx, TEAMNUM, f"Team {TEAMNUM} has played no matches during the {SEASON} season."))
        return

    events = j.loads(events)

    codes = []
    for event in events["events"]:
        codes.append(event["code"])

    scores = {}
    for event in codes:
        matches = r.get(f"http://ftc-api.firstinspires.org/v2.0/{SEASON}/matches/{event}", auth=(USERNAME, PASSWORD))
        matches = j.loads(matches.text)

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


def errorEmbed(ctx, title, desc):
    embed = discord.Embed(title=title, description=desc, color=0xFFFFFF)
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
    return embed

if __name__ == "__main__":
    client.run(TOKEN)