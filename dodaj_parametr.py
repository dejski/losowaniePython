import json

with open('players.json', 'r', encoding='utf-8') as f:
    players = json.load(f)

for p in players:
    p['pokazuj'] = True

with open('players.json', 'w', encoding='utf-8') as f:
    json.dump(players, f, indent=4, ensure_ascii=False)

print('Zaktualizowano pokazuj=True dla wszystkich graczy.')
