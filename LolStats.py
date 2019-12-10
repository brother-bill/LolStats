from riotwatcher import RiotWatcher, ApiError
import json

# The values before the region table are for you to modify
gameType = 450  # 450 is Aram, 440 is Flex, 430 is Norms, 420 is Solo/Duo Ranked
apiKey = ""
my_region = "euw1"
username = ""
# If you make champion = None, this will find all champions in a gametype
champion = ""

# Current patch can be found here: https://ddragon.leagueoflegends.com/realms/na.json
patch = "9.23.1"

# Table of region id's for each region
# br1	br1.api.riotgames.com
# eun1	eun1.api.riotgames.com
# euw1	euw1.api.riotgames.com
# jp1	jp1.api.riotgames.com
# kr	kr.api.riotgames.com
# la1	la1.api.riotgames.com
# la2	la2.api.riotgames.com
# na1	na1.api.riotgames.com
# oc1	oc1.api.riotgames.com
# tr1	tr1.api.riotgames.com
# ru	ru.api.riotgames.com

wins = 0
losses = 0
timeSpent = 0
lastPatch = ""

try:
    # Get summoner account information, you can uncomment the prints to view that information
    watcher = RiotWatcher(apiKey)
    # print("Summoner-v4        Row 8-2")
    myAccount = watcher.summoner.by_name(my_region, username)
    # print(json.dumps(myAccount, indent=4, sort_keys=True))
    # print("\n")

    accountID = myAccount["accountId"]
    globalID = myAccount["puuid"]

    # Extract champion ID
    champions = watcher.data_dragon.champions(patch)
    champID = champions["data"][champion]["key"]

    # Get matches for certain game type and champion
    # API only allows 100 matches at a time but my loop accounts for that
    matches = watcher.match.matchlist_by_account(
        my_region,
        accountID,
        gameType,
        begin_time=None,
        end_time=None,
        begin_index=None,
        end_index=None,
        season=None,
        champion=champID,
    )

    totalGames = matches["totalGames"]
    matchCount = 0
    loopCount = 0  # Everytime loopCount increments, that means we viewed 100 matches and will now look for the next 100

    print("Total Games: " + str(totalGames) + "\n")

    while matchCount < totalGames:
        print("Match Count:", (loopCount * 100) + matchCount + 1)

        gameID = matches["matches"][matchCount]["gameId"]
        match = watcher.match.by_id(my_region, gameID)
        timeSpent += match["gameDuration"]

        # Game ID to debug certain matches
        # print("GAME", gameID)

        myID = 100
        found = False
        for player in match["participantIdentities"]:
            currentID = player["player"]["currentAccountId"]
            if accountID in currentID:
                myID = player["participantId"]
                found = True

        # Caused by region transfer, this will not increment loop and will restart searching from current index
        if not found:
            newAccount = watcher.summoner.by_puuid(my_region, globalID)
            accountID = newAccount["accountId"]
            print(
                "REGION TRANSFER OCCURRED: \n IF YOU SEE THIS MESSAGE MORE TIMES THAN THE TIMES YOU TRANSFERRED \n THEN MATCHES AFTER THIS MIGHT BE INACCURATE"
            )

        else:
            print("Patch: " + match["gameVersion"])

            if totalGames - matchCount == 1:
                lastPatch = match["gameVersion"]

            if match["teams"][0]["win"] == "Win":
                if 1 <= myID <= 5:
                    wins += 1
                    print("Win")
                if 5 < myID <= 10:
                    losses += 1
                    print("Loss")

            if match["teams"][0]["win"] == "Fail":
                if 1 <= myID <= 5:
                    losses += 1
                    print("Loss")
                if 5 < myID <= 10:
                    wins += 1
                    print("Win")

            # If for whatever reason I still can't find you in a game
            # This breaks the code so it doesn't display incorrect information
            if myID == 100:
                print("ERROR SUMMONER NOT FOUND")
                break

            # Once matchCount is about to hit 100 if possible, this will reset the counters so the indexs stay inbound and then searches next 100 games
            if matchCount == 99:
                matchCount = 0
                totalGames -= 100
                loopCount += 1
                matches = watcher.match.matchlist_by_account(
                    my_region,
                    accountID,
                    gameType,
                    begin_time=None,
                    end_time=None,
                    begin_index=loopCount * 100,
                    end_index=None,
                    season=None,
                    champion=champID,
                )

            else:
                matchCount += 1

            # Just to space values out
            print()

    print("IGN: " + username + "\n")
    print("Champion: " + "**" + champion + "**" + "\n")
    print("Total Games: " + str((loopCount * 100) + totalGames) + "\n")
    print("Wins: " + str(wins) + "\n")
    print("Losses: " + str(losses) + "\n")
    # Avoids dividing by 0
    if wins + losses != 0:
        print(
            "Win Rate: " + "{:.2f}".format((wins * 100 / (wins + losses))) + "%" + "\n"
        )
    else:
        print("No Win Rate Data")
    print(
        "Hours Spent With Champion In Game: " + "{:.2f}".format(timeSpent / 3600) + "\n"
    )
    print("Oldest Patch: " + lastPatch + "\n")

except ApiError as err:
    if err.response.status_code == 429:
        print(
            "We should retry in {} seconds.".format(err.response.headers["Retry-After"])
        )
        print("this retry-after is handled by default by the RiotWatcher library")
        print("future requests wait until the retry-after time passes")
    elif err.response.status_code == 404:
        print("Data not found")
    else:
        raise

