import pytest
import subprocess
import os
import sys
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
sys.path.append(project_dir)
from DownloadFile.copyFile import *
#import DownloadFile.downloadFile as dwf
#import DownloadFile.webscraper as wsp
def test_default():
  print("jao")

def test_copy_file_to_s3(mocker):
  # Simula el comportamiento de subprocess.run
  mocker.patch('subprocess.run', return_value=subprocess.CompletedProcess(args="", returncode=0, stdout="", stderr=""))

  # Llama a la función que quieres probar
  result = copy_file_to_s3('local_folder_path', 's3_bucket_name')

  # Verifica que subprocess.run haya sido llamado con los argumentos correctos
  subprocess.run.assert_called_once_with(
    "aws s3 cp local_folder_path s3://s3_bucket_name/local_folder_path --recursive",
    shell=True,
    capture_output=True,
    text=True
  )

  # Verifica que el resultado sea el esperado
  assert result == 'local_folder_path'

def test_delete_local_file(mocker):
  mocker.patch('subprocess.run', return_value=subprocess.CompletedProcess(args="", returncode=0, stdout="", stderr=""))

  delete_local_file('local_folder_path')

  subprocess.run.assert_called_once_with(
    "rm local_folder_path",
    shell=True,
    capture_output=True,
    text=True
  )

def test_generate_download_link(mocker):
  # Arrange
  # Mock the boto3 client and its generate_presigned_url method
  mock_client = mocker.Mock()
  mock_generate_presigned_url = mocker.Mock(return_value='https://example.com/download_link')
  mock_client.generate_presigned_url = mock_generate_presigned_url
  mocker.patch('boto3.client', return_value=mock_client)

  # Act
  # Call the function you want to test
  result = generate_download_link('test_bucket', 'test_object_key')

  # Assert
  # Check if the generate_presigned_url method of the mocked client was called with the correct arguments
  mock_generate_presigned_url.assert_called_once_with(
    'get_object',
    Params={'Bucket': 'test_bucket', 'Key': 'test_object_key'},
    ExpiresIn=300
  )
  # Check if the result matches the expected URL
  assert result == 'https://example.com/download_link'