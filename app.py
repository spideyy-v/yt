from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
from urllib.parse import urlparse, parse_qs # Import URL parsing tools

app = Flask(__name__)
CORS(app)  # Allow frontend requests

# Define a common user agent to pretend we're a browser
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

def clean_url(url):
    """Strips extra query parameters like '?si=' from YouTube URLs."""
    try:
        parsed_url = urlparse(url)
        # Check if it's a 'watch' link and has a 'v' parameter
        if "youtube.com" in parsed_url.netloc and "watch" in parsed_url.path:
            v_param = parse_qs(parsed_url.query).get('v')
            if v_param:
                # Reconstruct a clean URL
                return f"https://www.youtube.com/watch?v={v_param[0]}"
    except Exception:
        pass # If parsing fails, just use the original URL
    
    # If not a standard 'watch' link (e.g., youtu.be), return it as is.
    # yt-dlp is good at handling those.
    return url

@app.route("/formats", methods=["POST"])
def list_formats():
    url = request.json.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400
    
    cleaned_url = clean_url(url)

    try:
        # We add --user-agent to pretend to be a browser
        # and --no-check-certificate as a fallback.
        # We also capture stderr to the pipe to get the full output, including errors.
        result = subprocess.run(
            [
                "yt-dlp", "-F", cleaned_url, 
                "--user-agent", USER_AGENT, 
                "--no-check-certificate"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, # Capture stderr separately
            text=True,
            encoding='utf-8' # Specify encoding
        )
        
        # Check if yt-dlp wrote to stderr
        if result.stderr:
            # If "ERROR" is in stderr, it's a real error
            if "ERROR:" in result.stderr.upper():
                return jsonify({"error": result.stderr}), 500
            # Otherwise, it might just be warnings
        
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

    cleaned_url = clean_url(url)

    try:
        # Add the same arguments here
        result = subprocess.run(
            [
                "yt-dlp", "-f", code, cleaned_url, 
                "-o", "%(title)s.%(ext)s", 
                "--user-agent", USER_AGENT, 
                "--no-check-certificate"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, # Capture stderr separately
            text=True,
            encoding='utf-8' # Specify encoding
        )
        
        # Check if yt-dlp wrote to stderr
        if result.stderr:
            if "ERROR:" in result.stderr.upper():
                return jsonify({"error": result.stderr}), 500

        return jsonify({"status": "✅ Download completed!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # The gunicorn command in the Dockerfile will be used by Render anyway.
    app.run(debug=True)

