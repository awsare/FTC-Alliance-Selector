import requests as r
import json
import passwords

SEASON = 2021
USERNAME = passwords.USERNAME
PASSWORD = passwords.PASSWORD

TEAMNUM = int(input("Enter your team number: "))
# need teamnum checker

events = r.get(f"https://ftc-api.firstinspires.org/v2.0/2021/events?teamNumber={TEAMNUM}", auth=(USERNAME, PASSWORD))
events = events.text
events = json.loads(events)

codes = []
for event in events["events"]:
    codes.append(event["code"])

scores = {}
for event in codes:
    matches = r.get(f"http://ftc-api.firstinspires.org/v2.0/{SEASON}/matches/{event}", auth=(USERNAME, PASSWORD))
    matches = matches.text
    matches = json.loads(matches)
    for match in matches["matches"]:
        for team in match["teams"]:
            if team["teamNumber"] == TEAMNUM:
                if team["station"] == "Red1":
                    if match["teams"][1]["teamNumber"] not in scores:
                        scores[match["teams"][1]["teamNumber"]] = [match["scoreRedFinal"]]
                    else:
                        scores[match["teams"][1]["teamNumber"]].append(match["scoreRedFinal"])
                elif team["station"] == "Red2":
                    if match["teams"][0]["teamNumber"] not in scores:
                        scores[match["teams"][0]["teamNumber"]] = [match["scoreRedFinal"]]
                    else:
                        scores[match["teams"][0]["teamNumber"]].append(match["scoreRedFinal"])
                elif team["station"] == "Blue1":
                    if match["teams"][3]["teamNumber"] not in scores:
                        scores[match["teams"][3]["teamNumber"]] = [match["scoreBlueFinal"]]
                    else:
                        scores[match["teams"][3]["teamNumber"]].append(match["scoreBlueFinal"])
                elif team["station"] == "Blue2":
                    if match["teams"][2]["teamNumber"] not in scores:
                        scores[match["teams"][2]["teamNumber"]] = [match["scoreBlueFinal"]]
                    else:
                        scores[match["teams"][2]["teamNumber"]].append(match["scoreBlueFinal"])
                continue

print(scores)