from riotwatcher import RiotWatcher, ApiError
import json
import time

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
my_region = "na1"

# Get API key here: https://developer.riotgames.com/
apiKey = " "
patch = "9.24.1"

# List of queue types found here: http://static.developer.riotgames.com/docs/lol/queues.json
gameType = 450  # 450 is Aram, 440 is Ranked Flex, 430 is Norms, 420 is Solo/Duo Ranked, 0 is Customs

# Table of champions for each username to find stats on, None finds all games in gametype regardless of champion
table = {
    "username1": ["Gangplank", "Illaoi"],
    "username2": ["Katarina", "Illaoi"],
    "username3": [None],
}

# All values above this line can be modified

try:
    # Get summoner account information, you can uncomment the prints to view that information
    watcher = RiotWatcher(apiKey)
    championList = watcher.data_dragon.champions(patch)
    statsList = []

    for user, champions in table.items():

        # Extract summoner ID
        summoner = watcher.summoner.by_name(my_region, user)
        print(json.dumps(summoner, indent=4, sort_keys=True))
        accountID = summoner["accountId"]
        globalID = summoner["puuid"]

        for champ in champions:

            print("IGN: " + str(user) + "\n")
            print("Champion: " + "**" + str(champ) + "**" + "\n")

            # Extract champion ID
            if champ:
                champID = championList["data"][champ]["key"]
            else:
                champID = None

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

            lastPatch = ""
            win = 0
            loss = 0
            timeSpent = 0
            totalGames = 0

            matchCount = 0
            loopCount = 0  # Everytime loopCount increments, that means we viewed 100 matches and will now look for the next 100

            while matchCount < len(matches["matches"]):

                # Retreive game ID for specific match
                gameID = matches["matches"][matchCount]["gameId"]
                # print(gameID)
                match = watcher.match.by_id(my_region, gameID)

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

                print("Match Count:", (loopCount * 100) + matchCount + 1)
                print("Patch: " + match["gameVersion"])

                # Search if player won or not
                for participant in match["participants"]:
                    if participant["participantId"] == playerID:
                        if participant["stats"]["win"]:
                            win += 1
                            print("Win" + "\n")
                        else:
                            loss += 1
                            print("Loss" + "\n")

                if matchCount == len(matches["matches"]) - 1:
                    lastPatch = match["gameVersion"]
                timeSpent += match["gameDuration"]
                totalGames += 1

                # Once matchCount is about to hit 100 if possible, this will reset the counters so the indexs stay inbound and then searches next 100 games
                if matchCount == 99:
                    matchCount = 0
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

            # Storing printed values and other stats to dump all stats for each player and their champions at the end
            # This avoids losing stats with limited terminal history
            statsList.append("IGN: " + str(user))
            statsList.append("Champion: " + "**" + str(champ) + "**")
            statsList.append("Total Games: " + str(totalGames))
            statsList.append("Wins: " + str(win))
            statsList.append("Losses: " + str(loss))
            if win + loss != 0:
                statsList.append(
                    "Win Rate: " + str(round((win * 100 / (win + loss)), 2)) + "%"
                )
            else:
                statsList.append("No Win Rate Data")

            statsList.append(
                "Hours Spent In Game: " + "{:.2f}".format(timeSpent / 3600)
            )
            statsList.append("Oldest Patch: " + lastPatch)

    for stat in statsList:
        print(stat + "\n")

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
