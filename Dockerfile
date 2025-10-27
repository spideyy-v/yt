# 1. Start from a base Python image
FROM python:3.10-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Install system dependencies (FFmpeg is needed by yt-dlp for merging)
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# 4. Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy your application code into the container
COPY . .

# 6. Expose the port Render expects (10000)
EXPOSE 10000

# 7. Define the command to run your app using gunicorn
# This tells gunicorn to run the 'app' variable from the 'app.py' file
# and listen on port 10000, which Render provides.
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]
