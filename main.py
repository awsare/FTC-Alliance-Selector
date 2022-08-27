import requests as r
import json as j
from datetime import datetime
from datetime import date
import passwords

import discord
from discord.ext import commands

USERNAME = passwords.USERNAME
PASSWORD = passwords.PASSWORD
TOKEN = passwords.TOKEN

PREFIX = "f."

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix = commands.when_mentioned_or(f"{PREFIX}"), intents=intents)

THIS_SEASON = r.get("http://ftc-api.firstinspires.org/v2.0")
THIS_SEASON = j.loads(THIS_SEASON.text)
THIS_SEASON = THIS_SEASON["currentSeason"]

@client.event
async def on_ready():
    await client.change_presence(activity = discord.Activity(type = discord.ActivityType.listening, name = f"{PREFIX}help"))
    print("Bot is online")

@client.command()
async def stats(ctx, TEAMNUM, SEASON = None):
    if TEAMNUM == None:
        await ctx.send(embed=errorEmbed(ctx, "Team Number Error", "Provide a team number."))
        return
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
            await ctx.send(embed=errorEmbed(ctx, "Season Number Error", f"Season number must be between 2019 and {THIS_SEASON}."))
            return

    events = r.get(f"https://ftc-api.firstinspires.org/v2.0/{SEASON}/events?teamNumber={TEAMNUM}", auth=(USERNAME, PASSWORD))
    events = events.text

    if "Malformed Parameter Format In Request" in events:
        await ctx.send(embed=errorEmbed(ctx, f"Team {TEAMNUM} ({SEASON}-{SEASON+1})", f"Team {TEAMNUM} played no matches during the {SEASON} season."))
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
    
    averageThree = []
    highestThree = []
    for team, info in scores.items():
        total = 0
        highest = 0
        for num in info["Scores"]:
            total += num
            if num > highest:
                highest = num
        average = round(total / len(info["Scores"]), 1)
        scores[team]["Average"] = average
        scores[team]["Highest"] = highest

        scores[team]["Name"] = getName(team, SEASON)
        
        if len(averageThree) < 3:
            averageThree.append(team)
        else:
            if average > scores[averageThree[2]]["Average"]:
                if average > scores[averageThree[1]]["Average"]:
                    if average > scores[averageThree[0]]["Average"]:
                        averageThree[0] = team
                    else:
                        averageThree[1] = team
                else:
                    averageThree[2] = team
        
        if len(highestThree) < 3:
            highestThree.append(team)
        else:
            if highest > scores[highestThree[2]]["Highest"]:
                if highest > scores[highestThree[1]]["Highest"]:
                    if highest > scores[highestThree[0]]["Highest"]:
                        highestThree[0] = team
                    else:
                        highestThree[1] = team
                else:
                    highestThree[2] = team

    embed = discord.Embed(title=f"{TEAMNUM} {getName(TEAMNUM, SEASON)} ({SEASON}-{SEASON+1})", color=0xFFFFFF)
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)

    # why wont it let me put these directly into the fstring
    highscore1 = scores[highestThree[0]]["Highest"]
    highscore1name = scores[highestThree[0]]["Name"]
    highscore2 = scores[highestThree[1]]["Highest"]
    highscore2name = scores[highestThree[1]]["Name"]
    highscore3 = scores[highestThree[2]]["Highest"]
    highscore3name = scores[highestThree[2]]["Name"]
    average1 = scores[averageThree[0]]["Average"]
    average1name = scores[averageThree[0]]["Name"]
    average2 = scores[averageThree[1]]["Average"]
    average2name = scores[averageThree[1]]["Name"]
    average3 = scores[averageThree[2]]["Average"]
    average3name = scores[averageThree[2]]["Name"]

    embed.add_field(name="Best Alliances by Average Score", value=f"{averageThree[0]} {average1name}: {average1} points\n{averageThree[1]} {average2name}: {average2} points\n{averageThree[2]} {average3name}: {average3} points", inline=False)
    embed.add_field(name="Best Alliances by High Score", value=f"{highestThree[0]} {highscore1name}: {highscore1} points\n{highestThree[1]} {highscore2name}: {highscore2} points\n{highestThree[2]} {highscore3name}: {highscore3} points", inline=False)

    today = date.today().strftime("%B %d, %Y")
    time = datetime.today().strftime("%I:%M %p")
    embed.set_footer(text=f"{today} at {time}")
 
    await ctx.send(embed=embed)


def errorEmbed(ctx, title, desc):
    embed = discord.Embed(title=title, description=desc, color=0xFFFFFF)
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
    return embed

def getName(num, season):
    name = r.get(f"https://ftc-api.firstinspires.org/v2.0/{season}/teams?teamNumber={num}", auth=(USERNAME, PASSWORD))
    name = j.loads(name.text)
    name = name["teams"][0]["nameShort"]
    return name

if __name__ == "__main__":
    client.run(TOKEN)