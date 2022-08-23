import requests as r
import json as j
import passwords

USERNAME = passwords.USERNAME
PASSWORD = passwords.PASSWORD

def main():
    correct = False
    while not correct:
        TEAMNUM = input("Enter your team number: ")

        if len(TEAMNUM) > 5:
            continue
        if not TEAMNUM.isnumeric():
            continue

        TEAMNUM = int(TEAMNUM)
        break

    #correct = False
    #while not correct:
        #SEASON = input("Enter your season number: ")

        #if len(SEASON) != 4:
            #continue
        #if not SEASON.isnumeric():
            #continue

        #SEASON = int(SEASON)
        #break
    SEASON = 2021

    events = r.get(f"https://ftc-api.firstinspires.org/v2.0/2021/events?teamNumber={TEAMNUM}", auth=(USERNAME, PASSWORD))
    events = events.text

    if "Malformed Parameter Format In Request" in events:
        print(f"Team {TEAMNUM} played no matches during the {SEASON} season.")
        return

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
    main()