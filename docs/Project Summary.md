# Project Summary

## Judul Proyek

ECG AFIB AWS - Smart Health Monitoring

## Ringkasan Proyek

Proyek ini merupakan sistem Smart Health Monitoring untuk melakukan simulasi pemantauan kondisi jantung pasien. Sistem ini mengadaptasi konsep Real-Time AFib Monitoring, yaitu pemantauan sinyal ECG untuk mendeteksi kondisi NORMAL atau AFIB.

Pada implementasi ini, perangkat ESP32 dan sensor AD8232 tidak digunakan secara langsung. Sebagai gantinya, sistem menggunakan dummy ECG generator untuk mensimulasikan data ECG normal dan AFIB. Data tersebut kemudian diproses oleh backend FastAPI.

## Tujuan Proyek

Tujuan proyek ini adalah:

1. Membuat sistem monitoring kondisi jantung berbasis cloud.
2. Mensimulasikan data ECG normal dan AFIB.
3. Menampilkan hasil prediksi kondisi pasien.
4. Menyimpan hasil monitoring ke database.
5. Mengirim alert jika kondisi AFIB terdeteksi.
6. Menyediakan dashboard untuk visualisasi monitoring.

## Arsitektur Sistem

Alur sistem:

Dummy ECG Generator  
→ FastAPI Backend  
→ Prediksi NORMAL / AFIB  
→ DynamoDB  
→ SNS Alert jika AFIB  
→ Frontend Dashboard  
→ S3 Dokumentasi  

## Komponen Sistem

### 1. Dummy ECG Generator

Dummy ECG generator digunakan sebagai pengganti data dari ESP32 dan sensor AD8232. Generator ini menghasilkan dua jenis data:

- Data NORMAL
- Data AFIB

### 2. Backend FastAPI

Backend bertugas menerima atau membuat data dummy ECG, memproses data, menghasilkan prediksi, menyimpan hasil ke DynamoDB, dan mengirim alert SNS jika kondisi AFIB terdeteksi.

Endpoint utama:

- `/generate-window?condition=normal`
- `/generate-window?condition=afib`
- `/latest`
- `/history`

### 3. DynamoDB

DynamoDB digunakan untuk menyimpan hasil monitoring pasien.

Data yang disimpan:

- patient_id
- timestamp
- label
- afib_probability
- bpm
- sample_count
- requested_condition

### 4. SNS

SNS digunakan untuk mengirim email alert jika hasil prediksi menunjukkan kondisi AFIB.

### 5. S3

S3 digunakan untuk menyimpan screenshot, bukti pengujian, dan dokumentasi proyek.

### 6. Frontend Dashboard

Frontend digunakan untuk menampilkan hasil monitoring kepada pengguna.

Komponen dashboard:

- Status pasien NORMAL atau AFIB
- BPM
- Probabilitas AFIB
- Sample count
- Timestamp
- History monitoring
- Tombol Generate Normal
- Tombol Generate AFIB

## Output Sistem

Contoh output sistem:

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

Hasil Pengujian
Pengujian NORMAL

Pada pengujian kondisi NORMAL, sistem menghasilkan:

Label: NORMAL
Probabilitas AFIB rendah
Data masuk ke DynamoDB
Tidak mengirim alert SNS
Pengujian AFIB

Pada pengujian kondisi AFIB, sistem menghasilkan:

Label: AFIB
Probabilitas AFIB tinggi
Data masuk ke DynamoDB
Email alert dikirim melalui SNS
Kondisi Saat AWS Menyala

Saat AWS menyala, backend berjalan pada EC2 dan dapat diakses melalui IP publik EC2.

Frontend menggunakan:

const API_BASE = "http://IP_EC2:8000";

Yang dapat dilakukan:

Test endpoint FastAPI.
Test kondisi NORMAL.
Test kondisi AFIB.
Cek data masuk DynamoDB.
Cek email alert dari SNS.
Frontend mengambil data dari backend cloud.

Catatan: jika EC2 dimatikan lalu dinyalakan kembali, Public IP bisa berubah.

Kondisi Saat AWS Mati

Saat AWS mati, endpoint cloud tidak dapat diakses. Namun, tim tetap bisa mengerjakan proyek secara lokal.

Backend lokal dijalankan dengan:

cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000

Frontend lokal menggunakan:

const API_BASE = "http://localhost:8000";

Yang tetap bisa dikerjakan:

Backend dikembangkan lokal.
Frontend dikembangkan lokal.
AI/ML mengembangkan dummy ECG generator.
Dokumentasi menyusun laporan dan PPT.
Kesimpulan

Sistem Smart Health Monitoring berhasil diimplementasikan menggunakan dummy ECG generator dan layanan AWS. Backend FastAPI berhasil berjalan di EC2, hasil prediksi berhasil disimpan ke DynamoDB, alert AFIB berhasil dikirim melalui SNS, dan dokumentasi dapat disimpan pada S3. Sistem ini dapat digunakan sebagai prototype monitoring kondisi jantung berbasis cloud.