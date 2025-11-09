# export_to_drive.py

from pathlib import Path
from typing import Optional, Dict
import os, io

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Usa la MISMA ruta que Excel exporta:
from app.exports_tools.excel_export_local import EXCEL_PATH as LOCAL_XLSX

# Importante: borra token.json al cambiar este scope
SCOPES = ["https://www.googleapis.com/auth/drive"]

def get_service():
    creds: Optional[Credentials] = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as f:
            f.write(creds.to_json())
    return build("drive", "v3", credentials=creds)

def _get_or_create_folder(service, name: str, parent_id: str) -> str:
    q = f"name='{name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    r = service.files().list(q=q, fields="files(id)", pageSize=1).execute()
    files = r.get("files", [])
    if files:
        return files[0]["id"]
    meta = {"name": name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent_id]}
    return service.files().create(body=meta, fields="id").execute()["id"]

def ensure_folder(service, folder_path: str) -> str:
    parent_id = "root"
    for name in [p.strip() for p in folder_path.split("/") if p.strip()]:
        parent_id = _get_or_create_folder(service, name, parent_id)
    return parent_id

def find_drive_file_by_name(service, name: str) -> Optional[Dict]:
    escaped = name.replace("'", r"\'")
    q = f"name = '{escaped}' and trashed = false"
    r = service.files().list(q=q, fields="files(id,name,modifiedTime)", orderBy="modifiedTime desc", pageSize=1).execute()
    files = r.get("files", [])
    return files[0] if files else None

def download_drive_file(service, file_id: str, local_path: str) -> None:
    request = service.files().get_media(fileId=file_id)
    with io.FileIO(local_path, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

def upload_file(service, local_path: Path | str, folder_path: str) -> str:
    local_path = Path(local_path)
    folder_id = ensure_folder(service, folder_path)
    q = f"name='{local_path.name}' and '{folder_id}' in parents and trashed=false"
    r = service.files().list(q=q, fields="files(id)", pageSize=1).execute()
    files = r.get("files", [])
    media = MediaFileUpload(str(local_path), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", resumable=True)
    if files:
        file_id = files[0]["id"]
        service.files().update(fileId=file_id, media_body=media).execute()
    else:
        meta = {"name": local_path.name, "parents": [folder_id]}
        file_id = service.files().create(body=meta, media_body=media, fields="id").execute()["id"]
    return file_id

def run_download_from_drive():
    service = get_service()
    drive_file = find_drive_file_by_name(service, LOCAL_XLSX.name)
    if drive_file:
        LOCAL_XLSX.parent.mkdir(parents=True, exist_ok=True)
        download_drive_file(service, drive_file["id"], str(LOCAL_XLSX))
        return True, f"Descargado desde Drive a: {LOCAL_XLSX}"
    return False, "El archivo no existe en Drive."

def run_upload_to_drive():
    service = get_service()
    file_id = upload_file(service=service, local_path=LOCAL_XLSX, folder_path="Solicitudes")
    return f"Subido/actualizado en Drive. file_id = {file_id}"
