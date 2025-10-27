from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess

app = Flask(__name__)
CORS(app)  # Allow frontend requests

@app.route("/formats", methods=["POST"])
def list_formats():
    url = request.json.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    try:
        result = subprocess.run(
            ["yt-dlp", "-F", url],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        return jsonify({"formats": result.stdout})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/download", methods=["POST"])
def download():
    data = request.json
    url = data.get("url")
    code = data.get("code")

    if not url or not code:
        return jsonify({"error": "Missing URL or format code"}), 400

    try:
        subprocess.run(
            ["yt-dlp", "-f", code, url, "-o", "%(title)s.%(ext)s"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        return jsonify({"status": "✅ Download completed!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)