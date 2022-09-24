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

            scores[team]["Name"] = getName(team, SEASON)
        
        averageList = teamsList.copy()
        averageList.sort(key=lambda x: scores[x]["Average"], reverse=True)

        highestList = teamsList.copy()
        highestList.sort(key=lambda x: scores[x]["Highest"], reverse=True)

        winrateList = teamsList.copy()
        winrateList.sort(key=lambda x: scores[x]["Win Rate"], reverse=True)

        embed = discord.Embed(title=f"{TEAMNUM} {getName(TEAMNUM, SEASON)} ({SEASON}-{SEASON+1})", color=0xFFFFFF)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)

        embed.add_field(name="Best Alliances by Average Score", value=f"{averageList[0]} {scores[averageList[0]]['Name']}: {scores[averageList[0]]['Average']} points\n{averageList[1]} {scores[averageList[1]]['Name']}: {scores[averageList[1]]['Average']} points\n{averageList[2]} {scores[averageList[2]]['Name']}: {scores[averageList[2]]['Average']} points\n{averageList[3]} {scores[averageList[3]]['Name']}: {scores[averageList[3]]['Average']} points\n{averageList[4]} {scores[averageList[4]]['Name']}: {scores[averageList[4]]['Average']} points", inline=False)
        embed.add_field(name="Best Alliances by High Score", value=f"{highestList[0]} {scores[highestList[0]]['Name']}: {scores[highestList[0]]['Highest']} points\n{highestList[1]} {scores[highestList[1]]['Name']}: {scores[highestList[1]]['Highest']} points\n{highestList[2]} {scores[highestList[2]]['Name']}: {scores[highestList[2]]['Highest']} points\n{highestList[3]} {scores[highestList[3]]['Name']}: {scores[highestList[3]]['Highest']} points\n{highestList[4]} {scores[highestList[4]]['Name']}: {scores[highestList[4]]['Highest']} points", inline=False)
        embed.add_field(name="Best Alliances by Win Rate", value=f"{winrateList[0]} {scores[winrateList[0]]['Name']}: {scores[winrateList[0]]['Win Rate']}%\n{winrateList[1]} {scores[winrateList[1]]['Name']}: {scores[winrateList[1]]['Win Rate']}%\n{winrateList[2]} {scores[winrateList[2]]['Name']}: {scores[winrateList[2]]['Win Rate']}%\n{winrateList[3]} {scores[winrateList[3]]['Name']}: {scores[winrateList[3]]['Win Rate']}%\n{winrateList[4]} {scores[winrateList[4]]['Name']}: {scores[winrateList[4]]['Win Rate']}%", inline=False)
        
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