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
    async with ctx.typing():
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
            scores[team]["Name"] = getName(team, SEASON)
        
        averageList = teamsList.copy()
        averageList.sort(key=lambda x: (scores[x]["Average"], scores[x]["Matches Played"]), reverse=True)

        highestList = teamsList.copy()
        highestList.sort(key=lambda x: (scores[x]["Highest"], scores[x]["Matches Played"]), reverse=True)

        winrateList = teamsList.copy()
        winrateList.sort(key=lambda x: (scores[x]["Win Rate"], scores[x]["Matches Played"]), reverse=True)

        embed = discord.Embed(title=f"{TEAMNUM} {getName(TEAMNUM, SEASON)} ({SEASON}-{SEASON+1})", color=0xFFFFFF)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)

        print(j.dumps(scores, indent=1))

        averageField = ""
        for index, team in enumerate(averageList):
            if index > 4:
                break
            averageField += f"{averageList[index]} {scores[averageList[index]]['Name']}: {scores[averageList[index]]['Average']} points ({scores[averageList[index]]['Matches Played']})\n"
        
        highestField = ""
        for index, team in enumerate(highestList):
            if index > 4:
                break
            highestField += f"{highestList[index]} {scores[highestList[index]]['Name']}: {scores[highestList[index]]['Highest']} points ({scores[averageList[index]]['Matches Played']})\n"
        
        winrateField = ""
        for index, team in enumerate(winrateList):
            if index > 4:
                break
            winrateField += f"{winrateList[index]} {scores[winrateList[index]]['Name']}: {scores[winrateList[index]]['Win Rate']}% ({scores[averageList[index]]['Matches Played']})\n"

        embed.add_field(name="Best Alliances by Average Score", value=averageField, inline=False)
        embed.add_field(name="Best Alliances by High Score", value=highestField, inline=False)
        embed.add_field(name="Best Alliances by Win Rate", value=winrateField, inline=False)
        
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
