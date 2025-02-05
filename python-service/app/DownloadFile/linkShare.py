import io
import os
import hmac
import time
import hashlib
import zipfile
from flask import Flask, send_file,abort


app = Flask(__name__)

# Secret key for generating secure tokens
SECRET_KEY = 'ff5f76b059b3de3adead4c2739a5fdf0a29b282cf1adf814524f77450b21eb7a'

# URL expiration time in seconds
EXPIRATION_TIME = 300  # 5 minutes

def generate_token(filename, timestamp):
    message = f'{filename}{timestamp}'.encode('utf-8')
    return hmac.new(SECRET_KEY.encode('utf-8'), message, hashlib.sha256).hexdigest()

#Test route
@app.route('/hello')
def hello_world():
    return "hello wolrd"

#Route to download file
@app.route('/files/<path:folder_path>/<timestamp>/<token>')
def download_folder(folder_path, timestamp, token):
    #main_path = '/app/downloads/'
    #full_path = main_path + folder_path
    full_path = folder_path

    if not os.path.exists(full_path) or not os.path.isdir(full_path):
        return abort(404)

    # Create a ZIP file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(full_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = file#file_path#os.path.relpath(file_path, base_folder)
                zip_file.write(file_path, arcname)

    zip_buffer.seek(0)

    current_time = int(time.time())
    if current_time > int(timestamp):
        return abort(403)  # URL has expired

    expected_token = generate_token(folder_path, timestamp)
    #expected_token = generate_token(full_path, timestamp)
    if token != expected_token:
        return abort(403)  # Invalid token

    # Send the ZIP file
    return send_file(zip_buffer, as_attachment=True, download_name='archive.zip', mimetype='application/zip')

def create_url(file_path):
    timestamp = str(int(time.time()) + EXPIRATION_TIME)
    #main_path = '/app/downloads/'
    #downloadable_folder = os.path.relpath(file_path, start=main_path)
    downloadable_folder = file_path
    token = generate_token(downloadable_folder, timestamp)
    link = f'http://142.93.48.99/files/' + f'{downloadable_folder}/{timestamp}/{token}'
    return link

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
