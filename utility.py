import requests
import json
APICALL = 'https://www.dota2.com/webapi/IDOTA2League/GetLeaguesData/v001?league_ids=13741,13742,13712,13713,13738,13740,13709,13710,13716,13717,13747,13748'
f = open('teamList.txt', 'r', encoding = 'utf8')
g = json.loads(f.read())

# for l in g['leagues']:
l = g['leagues'][10]

players = l['registered_players']
ng = l['node_groups']
# for item in ng:
#     print(item.keys())
ts= ng[0]['team_standings']
print(ts)
teamdict = {}
for team in ts:
    print(team['team_id'], team['team_tag'])
    teamdict[team['team_id']] = team['team_tag']
print(teamdict)
for player in players:
    print(player['name'])
print('\n')
for player in players:
    print(player['account_id'])
print('\n')
for player in players:
    print(teamdict[player['team_id']])
# print(t, '\ndone')
    # ng = json.loads(str(l['node_groups']))
    # for t in ng['team_standings']:
    #     print(t['team_name'])
