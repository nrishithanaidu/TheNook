from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return jsonify({"status": "Backend running successfully"})

@app.route("/records", methods=["GET"])
def get_records():
    return jsonify([
        {
            "id": 1,
            "song": "Time",
            "artist": "Pink Floyd",
            "album": "Dark Side of the Moon",
            "mood": 5
        },
        {
            "id": 2,
            "song": "Come Together",
            "artist": "The Beatles",
            "album": "Abbey Road",
            "mood": 4
        }
    ])

if __name__ == "__main__":
    app.run(debug=True)
