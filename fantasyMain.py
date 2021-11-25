import pandas as pd
import requests
import json
from datetime import datetime
import os

cd = '/Users/aidankilbourn/Desktop/Dota Fantasy/GameJsons/'
steamAPIBASE = "http://api.steampowered.com/"
steamKey = '8E66EC3262A8928C78C0E573625E3C8F'
steamGETGAME = steamAPIBASE + 'IDOTA2Match_570/GetMatchDetails/V001?key=' + steamKey
steamGETLEAGUE = steamAPIBASE + 'IDOTA2Match_570/GetMatchHistory/V001?key='+steamKey + '&league_id='
openDotaGETGAME = 'https://api.opendota.com/api/matches/'
weeks = []
lineups = {}

leagues = {
    #13659, #bts 9(DEMO ONLY REMOVE IN FINAL BUILD)
    13256 : ['INT', 'Major'] #TI10 (DEMO ONLY REMOVE IN FINAL BUILD)
}
def readInit():
    try: 
        f = open('init.txt', 'r')
    except:
        print('no init file found, don\'t delete it next time idiot')
        return
    
    # Reads timestamps to divide weeks
    line = f.readline().strip()
    while line != '':
        weeks.append(datetime.strptime(line, '%a %b %d %H:%M:%S %Y'))
        line = f.readline().strip()

    # Reads player fantasy teams, comma delimited
    line = f.readline().strip()
    while line != '':
        # Format:
        # weekNum,person,args(list of players, comma delimited)
        args = line.split(',')
        weekNum = args.pop(0)
        person = args.pop(0)
        lineups[weekNum] = {person: []}
        for playerID in args:
            lineups[weekNum][person].append(playerID)
        line = f.readline().strip()
#Calls the openDotaAPI in order to get the JSON for a game, saves it in the folder
#Returns a file object that can be used to access the JSON
def saveJson(gameID):
    fileName = cd + gameID + '.txt'
    currFile = open(fileName, 'w')
    print("File created with name:", fileName)
    #Make the API call to openDota
    APICALL = openDotaGETGAME + gameID
    g = requests.get(APICALL).text
    currFile.write(g)
    return currFile
#Takes a json file and turns it into a column of a df 
#returns a set of sets(df) with the 10 players, their names, id, team id, fantasy components,
#total fantasy score and region/time data
def parseScore(jsonInputFname, csvOutputFname):
    jsonFileInput = open(jsonInputFname, encoding='utf8')
    csvOutput = open(csvOutputFname, 'a', encoding='utf8')

    game = json.loads(jsonFileInput.read())
    stats = ['account_id', 'personaname', 'kills', 'deaths', 'assists',
    'last_hits', 'gold_per_min', 'tower_kills', 'roshan_kills', 'observer_uses', 'sentry_uses', 
    'camps_stacked', 'rune_pickups',  'stuns', 'first_blood', 'teamfights', 'start_time', '(Time)']
    gameStats = []
    playerStats = {}
    numTeamfights = len(game['teamfights'])
    for stat in stats:
        playerStats[stat] = []
    for playerNum in range(0,10):
        player = game['players'][playerNum] 
        for stat in stats:
            try:
                playerStats[stat].append(player[stat])
            except KeyError:
                playerStats[stat].append(0)
        #need to do some fancy stuff for first blood, teamfights
        playerStats['teamfights'][playerNum] = round(numTeamfights * player['teamfight_participation'])
    gameTime = playerStats['start_time'][0]
    for playerNum in range(0, 10):
        playerStats['(Time)'][playerNum] = datetime.utcfromtimestamp(int(gameTime)).strftime('%a %b %d %H:%M:%S %Y')
    for event in game['objectives']:
        if event['type'] == 'CHAT_MESSAGE_FIRSTBLOOD':
            playerStats['first_blood'][event['slot']] = 1
            break
    df = pd.DataFrame(playerStats)
    df['fantasy_score'] = df['kills'] * 0.3 + df['deaths'] * -0.3 + df['assists'] * 0.15 + df['last_hits'] * 0.003 + df['gold_per_min'] * 0.002
    df['fantasy_score'] += df['tower_kills'] * 1 + df['roshan_kills'] * 1 + df['teamfights'] * 3 + df['observer_uses']* 0.5 + df['sentry_uses']* 0.5 
    df['fantasy_score'] += df['rune_pickups'] * 0.25 + df['first_blood'] * 4.0 + df['stuns'] * 0.05 + df['camps_stacked'] * 0.5
    df['week'] =getWeeks(df['(Time)'])
    new_df = df[['account_id', 'personaname', 'week', 'fantasy_score']]
    if os.stat(csvOutputFname).st_size == 0:
        new_df.to_csv(path_or_buf = csvOutputFname, sep='\t', index = False, header = True, mode = 'a')
    else:
        new_df.to_csv(path_or_buf = csvOutputFname, sep='\t', index = False, header = False, mode = 'a')
    #add date/time/region info
    return new_df

#takes a set of games and checks if it's been processed
#returns false if the game has already been processed
def updateProcessedGames(gameID, region, division, seriesID, team1Name, team2Name):
    if (team1Name > team2Name):
        temp = team1Name
        team1Name = team2Name
        team2Name = temp
    f = open("processedGames.txt", 'r+t')
    attributes = team1Name, team2Name, gameID, region, division, seriesID
    str = ' '.join(attributes)
    if f.read().__contains__(str): return False

    print("Adding game w/ info:", str)
    f.write(str)
    f.write('\n')
    return True

def getNewGames():
    f = open("processedGames.txt", 'r') 
    newGames = {}
    pGames = f.read()
    for league in leagues:
        l = json.loads(requests.get(steamGETLEAGUE + str(league)).text)
        for game in l['result']['matches']:
            if pGames.find(str(game['match_id'])) < 0:
                newGames[game['match_id']] = [game['match_id'], league, game['series_id'], game['radiant_team_id'], game['dire_team_id']]

    print(len(newGames), 'new games found')
    return newGames

def fillGameNames(match_id, league, series_id, radiant_team_id, dire_team_id):
    gameData = []
    gameData.append(match_id)
    try:
        region = leagues[league][0]
        division = leagues[league[1]]
    except :
        region = '???'
        division = '?'
    gameData.append(region)
    gameData.append(division)
    gameData.append(series_id)
    teamList = json.loads(open('teams.txt', 'r').read())
    tracker = 0
    for team in teamList:
        if tracker < 2 and team['team_id'] == radiant_team_id:
            gameData.append(team['tag'])
            tracker += 3
        elif tracker%3 == 0 and team['team_id'] == dire_team_id:
            gameData.append(team['tag'])
            tracker += 5
        elif tracker > 7:
            break
    while len(gameData) < 6:
        gameData.append('Unknown Team')
    return gameData

def createTestGame(gameID = '6256990442'):
    f = open('test.txt', 'w')
    f.write(requests.get("https://api.opendota.com/api/matches/" + gameID).text)
    f.close()

def updateTeams():
    f = open('teams.txt', 'w')
    f.write(requests.get("https://api.opendota.com/api/teams").text)
    f.close()

def calcScores(week, players):
    df = pd.read_csv('scores.txt', sep='\t')
    scoreDf = df[df['week'] == week].groupby(['account_id']).apply(lambda x : x.sort_values(by = 'fantasy_score', ascending = False).head(2).reset_index(drop = True).sum())
    totalScore = 0
    for player in players:
        totalScore += scoreDf.at[player, 'fantasy_score']
    return totalScore

def update():
    f = open('processedGames.txt', 'a')
    newGames = getNewGames()
    for game in newGames:
        print(game)
        saveJson(str(game))
        for word in fillGameNames(*newGames[game]):
            f.write(str(word) + '\t')
        f.write('\n')
        print(fillGameNames(*newGames[game]))
    f.flush()
    f.close()

def getWeeks(dates):
    weekNums = []
    for date in dates:
        weekNums.append(getWeek(date))
    return weekNums

def getWeek(date):
    for x in range(0, len(weeks)):
        if weeks[x] > datetime.strptime(date, '%a %b %d %H:%M:%S %Y'):
            return x
    return -1

def endWeek():
    weeks.append(datetime.today())


#f = open('kurt.txt', 'r')
#parseScore(f)
#test = getNewGames()
#print(test)
#pdate()
#getNewGames()
#TODO: Use time in order to get fantasy score for a given player for a week
#TODO: Create a pandas table with playerID as index, and weekly score as values from data
#TODO: Create excel interface
readInit() #remember to call this every time
#parseScore('kurt.txt', 'scores.txt')
players = [51144617, 122688781]
print(calcScores(0, players))
# update()
