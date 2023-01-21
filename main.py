import requests as r
import json as j
from datetime import datetime
from datetime import date
import pytz

import passwords


import disnake
from disnake.ext import commands

USERNAME = passwords.USERNAME
PASSWORD = passwords.PASSWORD
TOKEN = passwords.TOKEN
PREFIX = "f."

ALLIANCE_COUNT = 6

intents = disnake.Intents.default()
intents.message_content = True
command_sync_flags = commands.CommandSyncFlags.default()
client = commands.Bot(command_prefix = commands.when_mentioned_or(f"{PREFIX}"), intents=intents, command_sync_flags=command_sync_flags)
client.remove_command('help')

THIS_SEASON = r.get("http://ftc-api.firstinspires.org/v2.0")
THIS_SEASON = j.loads(THIS_SEASON.text)
THIS_SEASON = THIS_SEASON["currentSeason"]

@client.event
async def on_ready():
    await client.change_presence(activity = disnake.Activity(type = disnake.ActivityType.listening, name = f"{PREFIX}help"))
    print("Bot is online")

@client.slash_command(description="Find the best alliances")
async def alliances(ctx, team_num, season_num = None):
    await ctx.response.defer()

    if team_num == None:
        await ctx.send(embed=errorEmbed(ctx, "Team Number Error", "Provide a team number."))
        return
    if len(team_num) > 5:
        await ctx.send(embed=errorEmbed(ctx, "Team Number Error", "Team number must be five digits or less."))
        return
    if not team_num.isnumeric():
        await ctx.send(embed=errorEmbed(ctx, "Team Number Error", "Team number must be numeric."))
        return
    team_num = int(team_num)
    if team_num < 1 or team_num > 99999:
        await ctx.send(embed=errorEmbed(ctx, "Team Number Error", "Team number must be between 1 and 99999."))
        return
    
    if season_num == None:
        season_num = THIS_SEASON
    else:
        if len(season_num) != 4:
            await ctx.send(embed=errorEmbed(ctx, "Season Number Error", "Season number must be four digits."))
            return
        if not season_num.isnumeric():
            await ctx.send(embed=errorEmbed(ctx, "Season Number Error", "Season number must be numeric."))
            return
        season_num = int(season_num)
        if season_num < 2019 or season_num > THIS_SEASON:
            await ctx.send(embed=errorEmbed(ctx, "Season Number Error", f"Season number must be between 2019 and {THIS_SEASON}."))
            return

    events = r.get(f"https://ftc-api.firstinspires.org/v2.0/{season_num}/events?teamNumber={team_num}", auth=(USERNAME, PASSWORD))
    events = events.text

    if "Malformed Parameter Format In Request" in events:
        await ctx.send(embed=errorEmbed(ctx, f"Team {team_num} ({season_num}-{season_num+1})", f"Team {team_num} played no matches during the {season_num} season."))
        return

    events = j.loads(events)

    if events["eventCount"] == 0:
        await ctx.send(embed=errorEmbed(ctx, f"Team {team_num} ({season_num}-{season_num+1})", f"Team {team_num} played no matches during the {season_num} season."))
        return

    codes = []
    for event in events["events"]:
        if (event["published"] == True):
            codes.append(event["code"])

    scores = {}
    for event in codes:
        matches = r.get(f"http://ftc-api.firstinspires.org/v2.0/{season_num}/matches/{event}", auth=(USERNAME, PASSWORD))
        matches = j.loads(matches.text)

        for match in matches["matches"]:
            for team in match["teams"]:
                if team["teamNumber"] == team_num:
                    if match["scoreRedFinal"] != match["scoreBlueFinal"]:
                        redwl = match["scoreRedFinal"] > match["scoreBlueFinal"]
                        bluewl = match["scoreRedFinal"] < match["scoreBlueFinal"]
                    if team["station"] == "Red1":
                        if match["teams"][1]["teamNumber"] not in scores:
                            scores[match["teams"][1]["teamNumber"]] = {"Scores":[match["scoreRedFinal"]], "WL":[redwl]}
                        else:
                            scores[match["teams"][1]["teamNumber"]]["Scores"].append(match["scoreRedFinal"])
                            scores[match["teams"][1]["teamNumber"]]["WL"].append(redwl)
                    elif team["station"] == "Red2":
                        if match["teams"][0]["teamNumber"] not in scores:
                            scores[match["teams"][0]["teamNumber"]] = {"Scores":[match["scoreRedFinal"]], "WL":[redwl]}
                        else:
                            scores[match["teams"][0]["teamNumber"]]["Scores"].append(match["scoreRedFinal"])
                            scores[match["teams"][0]["teamNumber"]]["WL"].append(redwl)
                    elif team["station"] == "Blue1":
                        if match["teams"][3]["teamNumber"] not in scores:
                            scores[match["teams"][3]["teamNumber"]] = {"Scores":[match["scoreBlueFinal"]], "WL":[bluewl]}
                        else:
                            scores[match["teams"][3]["teamNumber"]]["Scores"].append(match["scoreBlueFinal"])
                            scores[match["teams"][3]["teamNumber"]]["WL"].append(bluewl)
                    elif team["station"] == "Blue2":
                        if match["teams"][2]["teamNumber"] not in scores:
                            scores[match["teams"][2]["teamNumber"]] = {"Scores":[match["scoreBlueFinal"]], "WL":[bluewl]}
                        else:
                            scores[match["teams"][2]["teamNumber"]]["Scores"].append(match["scoreBlueFinal"])
                            scores[match["teams"][2]["teamNumber"]]["WL"].append(bluewl)
                    break
    
    teamsList = []
    for team in scores:
        teamsList.append(team)

    for team, info in scores.items():
        totalScore = 0
        highest = 0
        totalW = 0
        totalMatches = len(info["WL"])

        for num in info["Scores"]:
            totalScore += num
            if num > highest:
                highest = num

        for wl in info["WL"]:
            if wl == True:
                totalW += 1

        average = round(totalScore / len(info["Scores"]), 1)
        wlpercent = round(totalW/len(info["WL"]), 2) * 100
        scores[team]["Average"] = average
        scores[team]["Highest"] = highest
        scores[team]["Win Rate"] = wlpercent
        scores[team]["Matches Played"] = totalMatches
        scores[team]["Name"] = getName(team, season_num)
    
    averageList = teamsList.copy()
    averageList.sort(key=lambda x: (scores[x]["Average"], scores[x]["Matches Played"]), reverse=True)

    highestList = teamsList.copy()
    highestList.sort(key=lambda x: (scores[x]["Highest"], scores[x]["Matches Played"]), reverse=True)

    winrateList = teamsList.copy()
    winrateList.sort(key=lambda x: (scores[x]["Win Rate"], scores[x]["Matches Played"]), reverse=True)

    embed = disnake.Embed(title=f"{team_num} {getName(team_num, season_num)} ({season_num}-{season_num+1})", color=0xFFFFFF)
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)

    print(j.dumps(scores, indent=1))

    averageField = ""
    for index, team in enumerate(averageList):
        if index > ALLIANCE_COUNT - 1:
            break
        averageField += f"{averageList[index]} {scores[averageList[index]]['Name']}: {scores[averageList[index]]['Average']} points ({scores[averageList[index]]['Matches Played']})\n"
    
    highestField = ""
    for index, team in enumerate(highestList):
        if index > ALLIANCE_COUNT - 1:
            break
        highestField += f"{highestList[index]} {scores[highestList[index]]['Name']}: {scores[highestList[index]]['Highest']} points ({scores[highestList[index]]['Matches Played']})\n"
    
    winrateField = ""
    for index, team in enumerate(winrateList):
        if index > ALLIANCE_COUNT - 1:
            break
        winrateField += f"{winrateList[index]} {scores[winrateList[index]]['Name']}: {scores[winrateList[index]]['Win Rate']}% ({scores[winrateList[index]]['Matches Played']})\n"

    embed.add_field(name="Best Alliances by Average Score", value=averageField, inline=False)
    embed.add_field(name="Best Alliances by High Score", value=highestField, inline=False)
    embed.add_field(name="Best Alliances by Win Rate", value=winrateField, inline=False)
    
    today = date.today().strftime("%B %d, %Y")
    time = datetime.now(pytz.timezone("US/Eastern")).strftime("%I:%M %p")
    embed.set_footer(text=f"{today} at {time} EST")

    await ctx.followup.send(embed=embed)

@client.slash_command(description="Team stats")
async def stats(ctx, team_num, season_num = None):
    await ctx.response.defer()

    if team_num == None:
        await ctx.send(embed=errorEmbed(ctx, "Team Number Error", "Provide a team number."))
        return
    if len(team_num) > 5:
        await ctx.send(embed=errorEmbed(ctx, "Team Number Error", "Team number must be five digits or less."))
        return
    if not team_num.isnumeric():
        await ctx.send(embed=errorEmbed(ctx, "Team Number Error", "Team number must be numeric."))
        return
    team_num = int(team_num)
    if team_num < 1 or team_num > 99999:
        await ctx.send(embed=errorEmbed(ctx, "Team Number Error", "Team number must be between 1 and 99999."))
        return
    
    if season_num == None:
        season_num = THIS_SEASON
    else:
        if len(season_num) != 4:
            await ctx.send(embed=errorEmbed(ctx, "Season Number Error", "Season number must be four digits."))
            return
        if not season_num.isnumeric():
            await ctx.send(embed=errorEmbed(ctx, "Season Number Error", "Season number must be numeric."))
            return
        season_num = int(season_num)
        if season_num < 2019 or season_num > THIS_SEASON:
            await ctx.send(embed=errorEmbed(ctx, "Season Number Error", f"Season number must be between 2019 and {THIS_SEASON}."))
            return

    events = r.get(f"https://ftc-api.firstinspires.org/v2.0/{season_num}/events?teamNumber={team_num}", auth=(USERNAME, PASSWORD))
    events = events.text

    if "Malformed Parameter Format In Request" in events:
        await ctx.send(embed=errorEmbed(ctx, f"Team {team_num} ({season_num}-{season_num+1})", f"Team {team_num} played no matches during the {season_num} season."))
        return

    events = j.loads(events)

    if events["eventCount"] == 0:
        await ctx.send(embed=errorEmbed(ctx, f"Team {team_num} ({season_num}-{season_num+1})", f"Team {team_num} played no matches during the {season_num} season."))
        return

    codes = []
    for event in events["events"]:
        if (event["published"] == True):
            codes.append(event["code"])

    scores = {}
    for event in codes:
        matches = r.get(f"http://ftc-api.firstinspires.org/v2.0/{season_num}/matches/{event}", auth=(USERNAME, PASSWORD))
        matches = j.loads(matches.text)

        for match in matches["matches"]:
            for team in match["teams"]:
                if team["teamNumber"] == team_num:
                    if match["scoreRedFinal"] != match["scoreBlueFinal"]:
                        redwl = match["scoreRedFinal"] > match["scoreBlueFinal"]
                        bluewl = match["scoreRedFinal"] < match["scoreBlueFinal"]
                    if team["station"] == "Red1":
                        if match["teams"][0]["teamNumber"] not in scores:
                            scores[match["teams"][0]["teamNumber"]] = {"Scores":[match["scoreRedFinal"]], "WL":[redwl]}
                        else:
                            scores[match["teams"][0]["teamNumber"]]["Scores"].append(match["scoreRedFinal"])
                            scores[match["teams"][0]["teamNumber"]]["WL"].append(redwl)
                    elif team["station"] == "Red2":
                        if match["teams"][1]["teamNumber"] not in scores:
                            scores[match["teams"][1]["teamNumber"]] = {"Scores":[match["scoreRedFinal"]], "WL":[redwl]}
                        else:
                            scores[match["teams"][1]["teamNumber"]]["Scores"].append(match["scoreRedFinal"])
                            scores[match["teams"][1]["teamNumber"]]["WL"].append(redwl)
                    elif team["station"] == "Blue1":
                        if match["teams"][2]["teamNumber"] not in scores:
                            scores[match["teams"][2]["teamNumber"]] = {"Scores":[match["scoreBlueFinal"]], "WL":[bluewl]}
                        else:
                            scores[match["teams"][2]["teamNumber"]]["Scores"].append(match["scoreBlueFinal"])
                            scores[match["teams"][2]["teamNumber"]]["WL"].append(bluewl)
                    elif team["station"] == "Blue2":
                        if match["teams"][3]["teamNumber"] not in scores:
                            scores[match["teams"][3]["teamNumber"]] = {"Scores":[match["scoreBlueFinal"]], "WL":[bluewl]}
                        else:
                            scores[match["teams"][3]["teamNumber"]]["Scores"].append(match["scoreBlueFinal"])
                            scores[match["teams"][3]["teamNumber"]]["WL"].append(bluewl)
                    break

    print(j.dumps(scores, indent=1))

    embed = disnake.Embed(title=f"{team_num} {getName(team_num, season_num)} ({season_num}-{season_num+1})", color=0xFFFFFF)
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)
    
    today = date.today().strftime("%B %d, %Y")
    time = datetime.now(pytz.timezone("US/Eastern")).strftime("%I:%M %p")
    embed.set_footer(text=f"{today} at {time} EST")

    await ctx.followup.send(embed=embed)


def errorEmbed(ctx, title, desc):
    embed = disnake.Embed(title=title, description=desc, color=0xFFFFFF)
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)\
    
    today = date.today().strftime("%B %d, %Y")
    time = datetime.now(pytz.timezone("US/Eastern")).strftime("%I:%M %p")
    embed.set_footer(text=f"{today} at {time} EST")
    return embed

def getName(num, season):
    name = r.get(f"https://ftc-api.firstinspires.org/v2.0/{season}/teams?teamNumber={num}", auth=(USERNAME, PASSWORD))
    name = j.loads(name.text)
    name = name["teams"][0]["nameShort"]
    return name

if __name__ == "__main__":
    client.run(TOKEN)
