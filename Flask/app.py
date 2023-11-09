# app.py
# from flask import Flask, jsonify

# app = Flask(__name__)

# @app.route('/api/test', methods=['GET'])
# def test_api():
#     data = {"message": "This is a test response from Flask API"}
#     print('sdf')
#     return jsonify(data)

# if __name__ == '__main__':
#     app.run(debug=True)

from flask import Flask, jsonify, request

app = Flask(__name__)

users = [
    {"id": 1, "username": "john_doe", "point": 0, "success_missions" : [], "own_gifticons" : []},
    {"id": 2, "username": "jane_doe", "point": 0, "success_missions" : [], "own_gifticons" : []}
]

missions = [
    {"spot" : "station", "mission_name": "take", "success_point" : 10},
    {"spot" : "exco", "mission_name": "dive", "success_point" : 20}
]

gifticons = [
    {"gifticon_name" : "coffe", "require_point" : 20},
    {"gifticon_name" : "cake", "require_point" : 30}
]

# user list
@app.route('/api/users', methods=['GET'])
def get_users():
    return jsonify({"users": users})

# user info
@app.route('/api/users/<string:username>', methods=['GET'])
def get_user(username):
    user = next((user for user in users if user['username'] == username), None)
    if user:
        return jsonify(user)
    return jsonify({"message": "User not found"}), 404

# add gifticon
@app.route('/api/gift', methods=['POST'])
def add_gift():
    data = request.json
    username = data.get('username')
    gifticon_name = data.get('gifticon_name')

    user = next((user for user in users if user['username'] == username), None)
    if user:
        gifticon = next((gifticon for gifticon in gifticons if gifticon['gifticon_name'] == gifticon_name), None)
        if gifticon:
            user['own_gifticons'].append(gifticon_name)
            user['point'] -= gifticon['require_point']
            return jsonify({"message": f"Gifticon '{gifticon_name}' added successfully to {username}'s own_gifticons",
                            "user": user})
        else:
            return jsonify({"message": "Gifticon not found"}), 404
    else:
        return jsonify({"message": "User not found"}), 404

# mission complete reward
@app.route('/api/complete_mission', methods=['POST'])
def complete_mission():
    data = request.json
    username = data.get('username')
    mission_name = data.get('mission_name')
    spot = data.get('spot')

    user = next((user for user in users if user['username'] == username), None)
    if user:
        mission = next((mission for mission in missions if mission['mission_name'] == mission_name and mission['spot'] == spot), None)
        if mission:
            spot_mission_name = f"{mission['spot']}_{mission_name}"
            user['success_missions'].append(spot_mission_name)
            user['point'] += mission['success_point']
            return jsonify({"message": f"Mission '{mission_name}' completed successfully by {username} at {spot}",
                            "user": user})
        else:
            return jsonify({"message": "Mission not found"}), 404
    else:
        return jsonify({"message": "User not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)

# mission list
@app.route('/api/mission_list/')
def get_missions():
    return jsonify({"missions": missions})

# gifticon list
@app.route('/api/gifticon_list/')
def get_missions():
    return jsonify({"gifticons": gifticons})

# create user
@app.route('/create_users', methods=['POST'])
def create_user():
    data = request.json
    new_user = {
        "id": len(users) + 1,
        "username": data['username'],
        "point": 0,
        "success_missions" : [],
        "own_gifticons" : []
    }
    users.append(new_user)
    return jsonify({"message": "User created successfully", "user": new_user}), 201


if __name__ == '__main__':
    app.run(debug=True)