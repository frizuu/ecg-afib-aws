# AI/ML Notes

## Ringkasan

Bagian AI/ML bertugas menjelaskan dan menyiapkan logika prediksi kondisi jantung pasien berdasarkan data ECG dummy.

Pada proyek ini, data ECG tidak berasal dari ESP32 atau sensor AD8232 secara langsung. Data ECG digantikan dengan dummy ECG generator agar sistem tetap bisa diuji tanpa perangkat fisik.

Sistem tetap mengikuti konsep utama Real-Time AFib Monitoring, yaitu:
- Menggunakan data ECG
- Menggunakan window 1250 sampel
- Menghasilkan status NORMAL atau AFIB
- Menghasilkan nilai probabilitas AFIB
- Menampilkan hasil ke dashboard

## Konsep Dummy ECG

Dummy ECG generator digunakan untuk mensimulasikan dua kondisi:

### 1. NORMAL

Data NORMAL dibuat dengan karakteristik:
- Sinyal lebih stabil
- Pola lebih teratur
- Variasi sinyal lebih kecil
- BPM berada di rentang normal
- Probabilitas AFIB rendah

Output yang diharapkan:

```json
{
  "label": "NORMAL",
  "afib_probability": 0.2623,
  "bpm": 60,
  "sample_count": 1250
}
```
2. AFIB

Data AFIB dibuat dengan karakteristik:

Sinyal lebih tidak teratur
Variasi sinyal lebih besar
Pola puncak lebih acak
BPM cenderung lebih tinggi
Probabilitas AFIB tinggi

Output yang diharapkan:

{
  "label": "AFIB",
  "afib_probability": 0.8054,
  "bpm": 121,
  "sample_count": 1250
}
Window Sampel

Sistem menggunakan window sebanyak:

1250 sampel ECG

Window ini digunakan sebagai jumlah data yang diproses untuk menghasilkan prediksi kondisi pasien.

Threshold Prediksi

Threshold yang digunakan:

afib_probability > 0.5 = AFIB
afib_probability <= 0.5 = NORMAL

Artinya:

Jika probabilitas AFIB lebih dari 0.5, sistem menganggap kondisi pasien AFIB.
Jika probabilitas AFIB kurang dari atau sama dengan 0.5, sistem menganggap kondisi pasien NORMAL.
Output AI/ML ke Backend

Bagian AI/ML menghasilkan data berikut:

{
  "label": "AFIB",
  "afib_probability": 0.8054,
  "bpm": 121,
  "sample_count": 1250,
  "timestamp": "2026-06-06T07:15:10"
}

Field yang harus dipertahankan:

label
afib_probability
bpm
sample_count
timestamp
Catatan Pengembangan Lanjutan

Untuk versi awal, sistem menggunakan dummy prediction.

Jika tersedia model asli, bagian dummy prediction dapat diganti dengan model:

afib_model.tflite

Alur pengembangan lanjutan:

Menyiapkan dataset ECG.
Melakukan preprocessing data.
Melatih model klasifikasi AFIB.
Mengubah model menjadi format TFLite.
Mengintegrasikan model ke backend FastAPI.
Backend menggunakan model untuk menghasilkan prediksi NORMAL atau AFIB.
