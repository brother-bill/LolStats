from riotwatcher import RiotWatcher, ApiError
import json, requests

# The values before the region table are for you to modify
apiKey = "Put API Key Here"  # Get API key here: https://developer.riotgames.com/
gameType = 450  # 450 is Aram, 440 is Ranked Flex, 430 is Norms, 420 is Solo/Duo Ranked, 0 is Customs
username = "TheSwag VT"  # Username of anyone in a current game with specified game type
my_region = "na1"

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

# Current patch can be found here: https://ddragon.leagueoflegends.com/realms/na.json
response = json.loads(
    requests.get("https://ddragon.leagueoflegends.com/realms/na.json").text
)
patch = response["v"]

try:
    # Get summoner account information, you can uncomment the prints to view that information
    watcher = RiotWatcher(apiKey)
    myAccount = watcher.summoner.by_name(my_region, username)
    game = watcher.spectator.by_summoner(my_region, myAccount["id"])
    champion = {}

    for player1 in game["participants"]:
        champions1 = watcher.data_dragon.champions(patch)
        champID1 = champions1["data"]
        for i, j in champID1.items():
            if int(player1["championId"]) == int(j["key"]):
                champion.update({player1["summonerName"]: j["id"]})

    # print("Summoner-v4        Row 8-2")
    for user, champ in champion.items():

        myAccount = watcher.summoner.by_name(my_region, user)
        # print(json.dumps(myAccount, indent=4, sort_keys=True))
        # print("\n")

        accountID = myAccount["accountId"]
        globalID = myAccount["puuid"]
        wins = 0
        losses = 0
        timeSpent = 0
        lastPatch = ""

        # Extract champion ID
        champions = watcher.data_dragon.champions(patch)
        champID = champions["data"][champ]["key"]

        matches = None
        try:
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
        except ApiError as err:
            print("Data not found")

        totalGames = 0
        matchCount = 0
        loopCount = 0  # Everytime loopCount increments, that means we viewed 100 matches and will now look for the next 100

        # If no matches were found for a champion on a user, then go to next index
        while matches and matchCount < len(matches["matches"]):

            gameID = matches["matches"][matchCount]["gameId"]
            match = watcher.match.by_id(my_region, gameID)
            timeSpent += match["gameDuration"]

            # Find player in match, currentAccountId should track player even if they name changed or region transferred
            found = False
            for player in match["participantIdentities"]:
                if accountID in player["player"]["currentAccountId"]:
                    playerID = player["participantId"]
                    found = True

            if not found:
                print(
                    "Summoner wasn't found for match "
                    + str(matchCount)
                    + " with champ: "
                    + str(champ)
                    + "\nCould be an API issue or account problem"
                )
                break

            # print("Patch: " + match["gameVersion"])

            # Search if player won or not
            for participant in match["participants"]:
                if participant["participantId"] == playerID:
                    if participant["stats"]["win"]:
                        wins += 1
                        # print("Win" + "\n")
                    else:
                        losses += 1
                        # print("Loss" + "\n")

            if matchCount == len(matches["matches"]) - 1:
                lastPatch = match["gameVersion"]
            timeSpent += match["gameDuration"]
            totalGames += 1

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

        print("IGN: " + user)
        print("Champion: " + "**" + champ + "**")
        print("Total Games: " + str(totalGames))
        print("Wins: " + str(wins))
        print("Losses: " + str(losses))
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

