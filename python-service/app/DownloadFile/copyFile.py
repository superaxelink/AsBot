import os
#import boto3
import shutil
import logging
import subprocess
    

#Delete file from downloads directory
def delete_local_file(folder_path):
    try:
        if os.path.exists(folder_path):
            if os.path.isfile(folder_path):
                os.remove(folder_path)  # Удаление файла
            elif os.path.isdir(folder_path):
                shutil.rmtree(folder_path) 
            if not os.path.exists(folder_path):
                return True
            else:    
                logging.error("Error al borrar el archivo local")
                return False
        else:
            logging.error("Error al borrar el archivo local. La ruta no existe.")
            return False 
    except Exception as e:
        logging.error(f"Error al borrar el archivo local {folder_path}: {e}")
        return False
