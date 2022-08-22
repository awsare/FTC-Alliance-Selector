import requests as r
import json
import passwords

SEASON = 2021
USERNAME = passwords.USERNAME
PASSWORD = passwords.PASSWORD

TEAMNUM = int(input("Enter your team number: "))
# need teamnum checker

print("Enter your team's event codes. Enter done when finished.")
codes = []
while True:
    code = input("Enter an event code: ")
    if code.lower() == "done":
        break
    # need code checker
    codes.append(code)

scores = []
for event in codes:
    matches = r.get(f"http://ftc-api.firstinspires.org/v2.0/{SEASON}/matches/{event}", auth=(USERNAME, PASSWORD))
    matches = matches.text
    matches = json.loads(matches)
    for match in matches["matches"]:
        for team in match["teams"]:
            if team["teamNumber"] == TEAMNUM:
                if team["station"] == "Red1":
                    scores.append({match["teams"][1]["teamNumber"] : match["scoreRedFinal"]})
                elif team["station"] == "Red2":
                    scores.append({match["teams"][0]["teamNumber"] : match["scoreRedFinal"]})
                elif team["station"] == "Blue1":
                    scores.append({match["teams"][3]["teamNumber"] : match["scoreBlueFinal"]})
                elif team["station"] == "Blue2":
                    scores.append({match["teams"][2]["teamNumber"] : match["scoreBlueFinal"]})
                continue

print(scores)