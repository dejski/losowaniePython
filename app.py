from flask import Flask, jsonify, request, render_template
import json
import random
from datetime import datetime

app = Flask(__name__)

# Załaduj dane z pliku JSON
def load_data():
    with open("players.json", "r") as file:
        return json.load(file)

# Zapisz dane do pliku JSON
def save_data(data):
    with open("players.json", "w") as file:
        json.dump(data, file)

def modify_total_attributes(player):
    attribute_keys = ['kondycja', 'technika', 'gra_zespolowa', 'uderzenie']
    total_attributes = sum(player.get(key, 0) for key in attribute_keys)

    change_percent = random.uniform(-0.1, 0.1)
    modified_total = total_attributes * (1 + change_percent)

    return modified_total



def draw_teams():
    players = load_data()
    for player in players:
        if player['is_present'] and not player['on_break']:
            player['modified_total'] = modify_total_attributes(player)

    present_players = [player for player in players if player['is_present'] and not player['on_break']]
    random.shuffle(present_players)
    mid = len(present_players) // 2
    team_a, team_b = present_players[:mid], present_players[mid:]

    sum_attributes_team_a = sum(player['modified_total'] for player in team_a)
    sum_attributes_team_b = sum(player['modified_total'] for player in team_b)

    sum_attributes_team_a = round(sum_attributes_team_a)
    sum_attributes_team_b = round(sum_attributes_team_b)

    return team_a, team_b, sum_attributes_team_a, sum_attributes_team_b



# Strona główna z tabelą zawodników
@app.route('/')
def index():
    players = load_data()
    return render_template('index.html', players=players)

# Endpoint do aktualizacji statusu zawodnika
@app.route('/update_status', methods=['POST'])
def update_status():
    data = request.json
    players = load_data()
    for player in players:
        if player["name"] == data.get("name"):
            player["is_present"] = data.get("is_present", False)  # Domyślnie False, jeśli klucz nie istnieje
            player["on_break"] = data.get("on_break", False)  # Domyślnie False
    save_data(players)
    return jsonify(success=True)


@app.route('/draw_teams')
def api_draw_teams():
    print("Losowanie drużyn")  # Do debugowania
    team_a, team_b, sum_a, sum_b = draw_teams()
    current_day = datetime.now().strftime('%A')
    return render_template('teams.html', team_a=team_a, team_b=team_b, sum_a=sum_a, sum_b=sum_b, current_day=current_day)




if __name__ == '__main__':
    app.run(debug=True)
