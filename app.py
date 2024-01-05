from datetime import datetime

from flask import Flask, render_template, jsonify, request
import json
import random

app = Flask(__name__)

# Załaduj dane z pliku JSON
def load_data():
    with open("players.json", "r") as file:
        players = json.load(file)
        for player in players:
            player.setdefault('info', '')  # Ustawia domyślną wartość, jeśli klucz 'info' nie istnieje
        return players

# Zapisz dane do pliku JSON
def save_data(data):
    with open("players.json", "w") as file:
        json.dump(data, file, indent=4)

# Modyfikacja sumy cech zawodnika
def modify_total_attributes(player):
    attribute_keys = ['kondycja', 'technika', 'gra_zespolowa', 'uderzenie']
    total_attributes = sum(player.get(key, 0) for key in attribute_keys)
    change_percent = random.uniform(-0.1, 0.1)
    return total_attributes * (1 + change_percent)

# Losowanie drużyn
def draw_teams(players):
    for player in players:
        player['modified_total'] = modify_total_attributes(player)

    # Sortowanie zawodników i dzielenie na drużyny
    sorted_players = sorted(players, key=lambda x: x['modified_total'], reverse=True)
    team_a, team_b = [], []
    sum_a, sum_b = 0, 0

    for player in sorted_players:
        if sum_a <= sum_b:
            team_a.append(player)
            sum_a += player['modified_total']
        else:
            team_b.append(player)
            sum_b += player['modified_total']

    sum_a = round(sum_a)
    sum_b = round(sum_b)

    return team_a, team_b, sum_a, sum_b

# Strona główna
@app.route('/')
def index():
    players = load_data()
    players.sort(key=lambda x: x['name'])
    return render_template('index.html', players=players)

# Endpoint do aktualizacji stanu zawodnika
@app.route('/update_status', methods=['POST'])
def update_status():
    data = request.json
    players = load_data()
    for player in players:
        if player["name"] == data["name"]:
            player["is_present"] = data["is_present"]
            player["on_break"] = data["on_break"]
            player["info"] = data.get("info", "")  # Bezpieczne pobieranie 'info'
    save_data(players)
    return jsonify(success=True)


# Endpoint do losowania drużyn
@app.route('/draw_teams')
def api_draw_teams():
    players = [player for player in load_data() if player['is_present'] and not player['on_break']]
    team_a, team_b, sum_a, sum_b = draw_teams(players)
    current_day = datetime.now().strftime('%A')
    return render_template('teams.html', team_a=team_a, team_b=team_b, sum_a=sum_a, sum_b=sum_b, current_day=current_day)

# Endpoint do wyczyszczenia selekcji
@app.route('/clear_selection', methods=['POST'])
def clear_selection():
    players = load_data()
    for player in players:
        player['is_present'] = False
        player['on_break'] = False
    save_data(players)
    return jsonify(success=True)

if __name__ == '__main__':
    app.run(debug=True)
