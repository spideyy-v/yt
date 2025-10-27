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
    
    return url

@app.route("/formats", methods=["POST"])
def list_formats():
    url = request.json.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400
    
    cleaned_url = clean_url(url)

    # We add --force-ipv4 as our new attempt
    command = [
        "yt-dlp", "-F", cleaned_url, 
        "--user-agent", USER_AGENT, 
        "--no-check-certificate",
        "--force-ipv4"
    ]

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        # Check stderr for any "ERROR" messages
        stderr_output = result.stderr or ""
        if "ERROR:" in stderr_output.upper():
            return jsonify({"error": f"yt-dlp failed: {stderr_output}"}), 500
        
        # If no real error, but stdout is empty, something is wrong
        if not result.stdout:
            error_message = f"No formats found. yt-dlp output: {stderr_output}" if stderr_output else "No formats found and no error reported."
            return jsonify({"error": error_message}), 500

        return jsonify({"formats": result.stdout})
        
    except Exception as e:
        return jsonify({"error": f"Server exception: {str(e)}"}), 500


@app.route("/download", methods=["POST"])
def download():
    data = request.json
    url = data.get("url")
    code = data.get("code")

    if not url or not code:
        return jsonify({"error": "Missing URL or format code"}), 400

    cleaned_url = clean_url(url)

    # Add the same --force-ipv4 argument here
    command = [
        "yt-dlp", "-f", code, cleaned_url, 
        "-o", "%(title)s.%(ext)s", 
        "--user-agent", USER_AGENT, 
        "--no-check-certificate",
        "--force-ipv4"
    ]

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        stderr_output = result.stderr or ""
        if "ERROR:" in stderr_output.upper():
            return jsonify({"error": f"yt-dlp failed: {stderr_output}"}), 500

        return jsonify({"status": "✅ Download completed!"})
    except Exception as e:
        return jsonify({"error": f"Server exception: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
