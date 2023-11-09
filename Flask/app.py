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
from flask_cors import CORS

import torch
import torch.nn as nn
from torchvision import transforms
import timm
import unicodedata
import cv2
import pickle
from PIL import Image

app = Flask(__name__)
CORS(app)

users = [
    {"id": 1, "username": "john_doe", "point": 0, "success_missions" : [], "own_gifticons" : []},
    {"id": 2, "username": "jane_doe", "point": 0, "success_missions" : [], "own_gifticons" : []}
]

missions = [
    {"spot" : "동대구역", "mission_name": "사진 찍기", "success_point" : 10},
    {"spot" : "EXCO", "mission_name": "사진 찍기", "success_point" : 15},
    {"spot" : "83 타워", "mission_name": "사진 찍기", "success_point" : 18},
    {"spot" : "김광석 길", "mission_name": "사진 찍기", "success_point" : 30},
    {"spot" : "디아크", "mission_name": "사진 찍기", "success_point" : 50},
    {"spot" : "달성공원", "mission_name": "사진 찍기", "success_point" : 5},
    {"spot" : "감영공원", "mission_name": "사진 찍기", "success_point" : 10},
    {"spot" : "국채보상운동기념공원", "mission_name": "사진 찍기", "success_point" : 30},
    {"spot" : "희움 위안부 역사관", "mission_name": "사진 찍기", "success_point" : 20},
    {"spot" : "서문시장", "mission_name": "사진 찍기", "success_point" : 25},
    {"spot" : "서남시장", "mission_name": "사진 찍기", "success_point" : 25},
    {"spot" : "대구 수목원", "mission_name": "사진 찍기", "success_point" : 25},
    {"spot" : "주교좌 성당", "mission_name": "사진 찍기", "success_point" : 25},
    {"spot" : "이월드", "mission_name": "사진 찍기", "success_point" : 25}
]


gifticons = [
    {"gifticon_name" : "중앙 떡볶이", "require_point" : 20},
    {"gifticon_name" : "은하네 우동집", "require_point" : 30}
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

# mission list
@app.route('/api/mission_list/')
def get_missions():
    return jsonify({"missions": missions})

# gifticon list
@app.route('/api/gifticon_list/')
def get_gifticons():
    return jsonify({"gifticons": gifticons})

# check image
class VerificationModel:
    def __init__(self, model_path, pickle_path):
        self.model = timm.create_model('efficientnet_b0', pretrained=True)
        self.model.classifier = nn.Sequential(
        nn.Linear(1280, 512),
        nn.ReLU(),
        nn.Linear(512, 128),
        )
        checkpoint = torch.load(model_path)
        self.model.load_state_dict(checkpoint)
        self.model.eval()  # Set the model to inference mode

        with open(pickle_path, 'rb') as handle:
            self.image_test_dict = pickle.load(handle)

        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def data_load(self, input_path):
        data = cv2.imread(input_path)
        data = cv2.cvtColor(data, cv2.COLOR_BGR2RGB)
        data = cv2.resize(data, (224, 224))
        data = Image.fromarray(data)
        data = self.transform(data)
        return data.unsqueeze(dim=0)

    def predict(self, input_path, keyword):
        keyword = unicodedata.normalize('NFC', keyword)
        data = self.data_load(input_path)
        output1 = self.image_test_dict[keyword]
        output2 = self.model(data)
        n = output1.shape[0]
        output2 = torch.cat([output2] * n)

        count = sum(torch.pow(output1 - output2, 2).sum(dim=1).sqrt() < 0.68)
        result = (count >= 1).int()
        return result.item()

@app.route('/api/check', methods=['POST'])
def check_picture():
    data = request.json
    # input_path = 입력 이미지 경로
    # keyword = 해당 장소
    
    # jsom 형태로 받아오면
    # input_path = data.get('input_path')
    # keyword = data.get('keyword')
    
    model_path = './best_model.pth'
    pickle_path = "image_test_dict.pickle"

    inference_model = VerificationModel(model_path, pickle_path)
    result = inference_model.predict(input_path, keyword)
    #print(result)
    if result == 1:
        judge = True
    else:
        judge = False
    return jsonify({"Judge" : judge})

# create user
@app.route('/api/create_users', methods=['POST'])
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