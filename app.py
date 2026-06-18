import json
import random
import locale
from datetime import datetime

from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

RANDOMNESS = 0.03  # 3%
DRAW_ATTEMPTS = 300
EXTRA_PLAYER_WEIGHT = 0.60



# Załaduj dane z pliku JSON
def load_data():
    with open("players.json", "r", encoding="utf-8") as file:
        players = json.load(file)
        for player in players:
            player.setdefault("info", "")
            player.setdefault("pokazuj", True)
            player.setdefault("is_present", False)
            player.setdefault("on_break", False)
        return players


# Zapisz dane do pliku JSON
def save_data(data):
    with open("players.json", "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


RANDOMNESS = 0.03
DRAW_ATTEMPTS = 1000
EXTRA_PLAYER_WEIGHT = 0.60


def base_total(player):
    attribute_keys = ["kondycja", "technika", "gra_zespolowa", "uderzenie"]
    return sum(player.get(key, 0) for key in attribute_keys)


def modified_total(player):
    total = base_total(player)
    change_percent = random.uniform(-RANDOMNESS, RANDOMNESS)
    return total * (1 + change_percent)


def team_base_total(team):
    return sum(base_total(p) for p in team)


def effective_team_total(team, opponent_team):
    total = sum(p.get("draw_total", 0) for p in team)

    if len(team) > len(opponent_team):
        weakest = min(team, key=lambda p: p.get("draw_total", 0))
        total -= weakest.get("draw_total", 0) * (1 - EXTRA_PLAYER_WEIGHT)

    return total


def effective_team_attribute_sum(team, opponent_team, attr):
    total = sum(p.get(attr, 0) for p in team)

    if len(team) > len(opponent_team):
        weakest = min(team, key=lambda p: p.get("draw_total", 0))
        total -= weakest.get(attr, 0) * (1 - EXTRA_PLAYER_WEIGHT)

    return total


def evaluate_draw(team_a, team_b):
    attrs = ["kondycja", "technika", "gra_zespolowa", "uderzenie"]

    total_a = effective_team_total(team_a, team_b)
    total_b = effective_team_total(team_b, team_a)

    total_diff = abs(total_a - total_b)

    attr_diff = 0
    for attr in attrs:
        a_attr = effective_team_attribute_sum(team_a, team_b, attr)
        b_attr = effective_team_attribute_sum(team_b, team_a, attr)
        attr_diff += abs(a_attr - b_attr)

    score = (total_diff * 3.0) + (attr_diff * 1.5)

    return score


def build_candidate(players):
    working = []

    for player in players:
        p = dict(player)
        p["draw_total"] = modified_total(p)
        working.append(p)

    random.shuffle(working)

    if len(players) % 2 == 0:
        target_a = len(players) // 2
    else:
        # Przy nieparzystej liczbie raz większa może być A, raz B
        target_a = random.choice([
            len(players) // 2,
            len(players) // 2 + 1
        ])

    team_a = working[:target_a]
    team_b = working[target_a:]

    return team_a, team_b


def losuj(players):
    if len(players) < 2:
        return players, [], team_base_total(players), 0

    best_team_a = None
    best_team_b = None
    best_score = float("inf")

    for _ in range(DRAW_ATTEMPTS):
        team_a, team_b = build_candidate(players)
        score = evaluate_draw(team_a, team_b)

        if score < best_score:
            best_score = score
            best_team_a = team_a
            best_team_b = team_b

    sum_a = team_base_total(best_team_a)
    sum_b = team_base_total(best_team_b)

    return best_team_a, best_team_b, sum_a, sum_b


# Strona główna
@app.route("/")
def index():
    show_draw_button = request.args.get("show") == "true"
    players = load_data()

    # ukryj niepokazywanych
    players = [p for p in players if p.get("pokazuj", True)]

    # sortowanie PL
    try:
        locale.setlocale(locale.LC_COLLATE, "pl_PL.UTF-8")
        key_fn = lambda p: locale.strxfrm(p.get("name", ""))
    except locale.Error:
        key_fn = lambda p: p.get("name", "")

    players.sort(key=key_fn)
    return render_template(
        "index.html",
        players=players,
        show_draw_button=show_draw_button
    )


# Endpoint do aktualizacji stanu zawodnika
@app.route("/update_status", methods=["POST"])
def update_status():
    data = request.json
    pid = data.get("id")

    if pid is None:
        return jsonify(success=False, error="Missing id"), 400

    players = load_data()

    for p in players:
        if str(p.get("id")) == str(pid):
            if "is_present" in data:
                p["is_present"] = bool(data["is_present"])
            if "on_break" in data:
                p["on_break"] = bool(data["on_break"])
            if "info" in data:
                p["info"] = data["info"]
            break

    save_data(players)
    return jsonify(success=True)


# Endpoint do losowania drużyn
@app.route("/losuj")
def api_losuj():
    players = [
        player for player in load_data()
        if player.get("is_present", False) and not player.get("on_break", False)
    ]

    team_a, team_b, sum_a, sum_b = losuj(players)

    # sortowanie PL
    try:
        locale.setlocale(locale.LC_COLLATE, "pl_PL.UTF-8")
        key_fn = lambda p: locale.strxfrm(p.get("name", ""))
    except locale.Error:
        key_fn = lambda p: p.get("name", "")

    team_a = sorted(team_a, key=key_fn)
    team_b = sorted(team_b, key=key_fn)

    current_day = datetime.now().strftime("%A")
    return render_template(
        "teams.html",
        team_a=team_a,
        team_b=team_b,
        sum_a=sum_a,
        sum_b=sum_b,
        current_day=current_day
    )


# Endpoint do wyczyszczenia selekcji
@app.route("/clear_selection", methods=["POST"])
def clear_selection():
    players = load_data()
    for player in players:
        player["is_present"] = False
        player["on_break"] = False
    save_data(players)
    return jsonify(success=True)


@app.route("/edycja")
def edycja():
    return render_template("edycja.html")


@app.route("/get_data", methods=["GET"])
def get_data():
    with open("players.json", "r", encoding="utf-8") as file:
        data = json.load(file)
    return jsonify(data)


@app.route("/update_data", methods=["POST"])
def update_data():
    new_data = request.json
    with open("players.json", "w", encoding="utf-8") as file:
        json.dump(new_data, file, indent=4, ensure_ascii=False)
    return jsonify({"status": "success"})


if __name__ == "__main__":
    app.run(debug=True)