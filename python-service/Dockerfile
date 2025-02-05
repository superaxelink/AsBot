FROM python:3.10

# Set environment variable to disable Python output buffering
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /usr/src/python-service

# Copy requirements.txt to the working directory
COPY app/requirements.txt ./app/

# Install cron
RUN apt-get update && apt-get install -y cron

# install Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable

# install ChromeDriver
RUN CHROME_DRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE` \
    && wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/ \
    && rm /tmp/chromedriver.zip

# Install Python dependencies
RUN pip install --no-cache-dir -r ./app/requirements.txt

# Copy the rest of the application files to the container
COPY . .

# Give execution rights on the cron job
RUN chmod 0644 /usr/src/python-service/app/cronjob

# Apply the cron job (make it active in the container)
RUN crontab /usr/src/python-service/app/cronjob

# Create the cron log file (this ensures it exists before cron runs)
RUN touch /usr/src/python-service/app/cron.log

# Define el comando que se ejecutará cuando el contenedor se inicie
CMD ["sh", "-c", "python3 app/main.py & gunicorn -w 1 -b 0.0.0.0:5000 app.DownloadFile.linkShare:app"]