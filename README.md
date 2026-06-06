# ECG AFIB AWS - Smart Health Monitoring

## Ringkasan Proyek

Proyek ini merupakan implementasi Prototype Smart Health Monitoring berbasis cloud untuk simulasi pemantauan kondisi jantung pasien. Sistem mengacu pada konsep Real-Time AFib Monitoring dengan data ECG, window 1250 sampel, dan hasil prediksi berupa NORMAL atau AFIB.

Pada implementasi ini, ESP32 dan sensor AD8232 tidak digunakan secara langsung. Data ECG digantikan dengan dummy ECG generator untuk mensimulasikan kondisi normal dan AFIB.

## Arsitektur Sistem

Dummy ECG Generator
↓
FastAPI Backend
↓
Prediksi NORMAL / AFIB
↓
DynamoDB
↓
SNS Alert jika AFIB
↓
Frontend Dashboard
↓
S3 untuk dokumentasi dan screenshot

## Komponen AWS

- EC2: menjalankan backend FastAPI
- Security Group: membuka akses SSH dan API
- DynamoDB: menyimpan hasil monitoring
- SNS: mengirim email alert ketika AFIB terdeteksi
- S3: menyimpan screenshot dan dokumentasi

## Endpoint Backend

- GET /
- GET /generate
- GET /generate-window?condition=normal
- GET /generate-window?condition=afib
- GET /latest
- GET /history

## Contoh Response

```json
{
  "status": "PREDICTED",
  "patient_id": "P001",
  "data_source": "dummy",
  "requested_condition": "AFIB",
  "label": "AFIB",
  "afib_probability": 0.8054,
  "bpm": 121,
  "sample_count": 1250,
  "timestamp": "2026-06-06T07:15:10"
}
```
Progress DevOps

DevOps telah menyelesaikan:

Membuat EC2 instance Ubuntu.
Mengatur Security Group untuk port 22 dan 8000.
Melakukan SSH ke EC2 menggunakan key pair.
Menginstall Python, pip, venv, git, FastAPI, Uvicorn, dan boto3.
Deploy backend FastAPI ke EC2.
Membuat DynamoDB table SmartHealthMonitoring.
Menyimpan data hasil prediksi ke DynamoDB.
Membuat SNS topic SmartHealthAFibAlert.
Mengirim email alert ketika AFIB terdeteksi.
Membuat S3 bucket untuk dokumentasi.
Upload screenshot bukti AWS ke S3.


Tugas: Dev Ops

Menyiapkan EC2.
Mengatur Security Group.
Deploy FastAPI ke EC2.
Menyiapkan DynamoDB.
Menyiapkan SNS.
Menyiapkan S3.
Menyediakan endpoint untuk frontend.

Output:

Backend berjalan di AWS.
Data masuk DynamoDB.
Alert AFIB terkirim lewat SNS.
Screenshot AWS tersedia di S3.



Tugas: Backend

Merapikan main.py.
Membuat endpoint API.
Menjaga format response JSON.
Membuat requirements.txt.
Membuat mode lokal agar bisa jalan tanpa AWS.

Output:

main.py
requirements.txt
Backend bisa jalan di localhost:8000.



Tugas:AI/ML

Menjelaskan dummy ECG normal dan AFIB.
Menjelaskan window 1250 sampel.
Menjelaskan threshold AFIB.
Jika tersedia, menyiapkan model afib_model.tflite.

Output:

Penjelasan metode dummy ECG.
Penjelasan threshold AFIB.
Fungsi generate ECG normal dan AFIB.



Tugas:Frontend

Membuat dashboard HTML/CSS/JS.
Menampilkan status NORMAL atau AFIB.
Menampilkan BPM.
Menampilkan probabilitas AFIB.
Menampilkan sample count.
Membuat tombol Generate Normal dan Generate AFIB.
Menampilkan history.

Output:

index.html
style.css
script.js.



Tugas:Dokumentasi

Menyusun laporan.
Membuat diagram arsitektur.
Menjelaskan flow sistem.
Mengumpulkan screenshot hasil AWS.
Membuat PPT.

Output:

Laporan proyek.
PPT.
Diagram arsitektur.
Screenshot hasil pengujian.
Kondisi Saat AWS Menyala


## Saat AWS menyala, backend berjalan di EC2.

Frontend memakai:

const API_BASE = "http://IP_EC2:8000";

Yang bisa dilakukan:

Test endpoint di /docs.
Test normal dan AFIB.
Cek data masuk DynamoDB.
Cek email alert SNS.
Frontend mengambil data dari backend cloud.

Catatan: jika EC2 stop/start, IP publik bisa berubah.

## Kondisi Saat AWS Mati

Saat AWS mati, tim tetap bisa kerja lokal.

Jalankan backend lokal:

cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000

Frontend memakai:

const API_BASE = "http://localhost:8000";

Yang bisa dilakukan:

Backend dikembangkan lokal.
Frontend dikembangkan lokal.
AI/ML mengembangkan dummy ECG.
Dokumentasi tetap bisa dikerjakan.

