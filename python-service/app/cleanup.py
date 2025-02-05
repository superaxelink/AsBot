import os
import shutil
import json

# Code snippet to delete downloads folder

def clean_folder():

# Need to define file_path before

    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'messages.json') 

    with open(os.path.abspath(file_path)) as f:
        MESSAGES = json.load(f)

    base_folder=os.getcwd()#os.path.join(os.getcwd(), 'app')
    # Sanitize the folder name
    downloads_path = os.path.join(base_folder,MESSAGES['folder_names']['main_downloads_folder'])

    for filename in os.listdir(downloads_path):
        file_path = os.path.join(downloads_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

if __name__ == '__main__':
    clean_folder()
