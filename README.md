# ECG AFIB Detection Backend

Backend sederhana untuk deteksi aritmia menggunakan model CNN 1D / dummy inference. Proyek ini disiapkan agar dapat dijalankan secara lokal dan mudah dibawa ke AWS menggunakan Docker.

## Struktur utama
- `backend/app.py` - FastAPI server dengan endpoint `/generate`, `/predict`, `/latest`
- `backend/model.py` - model CNN dummy atau pemuatan model H5 jika ada
- `backend/signal.py` - preprocessing sinyal ECG dan generator data dummy
- `requirements.txt` - paket Python untuk runtime
- `Dockerfile` - container image untuk menjalankan backend

## Persiapan lokal
1. Buat environment Python:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Jalankan server:
   ```powershell
   uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
   ```

## Endpoint
- `GET /generate`
  - Menghasilkan data ECG dummy 5 detik dan label contoh
- `POST /predict`
  - Menerima JSON: `{ "signal": [float], "sample_rate": 250 }`
  - Mengembalikan probabilitas AFIB, label, dan BPM
- `GET /latest`
  - Mengembalikan metadata model dan prediksi terakhir

## Contoh request
```powershell
curl -X GET http://127.0.0.1:8000/generate
```

```powershell
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d "{\"signal\": [0.0, 0.1, -0.05, ...], \"sample_rate\": 250}"
```

## Deployment ke AWS
1. Build image Docker:
   ```powershell
   docker build -t ecg-afib-backend .
   ```
2. Jalankan container lokal:
   ```powershell
   docker run --rm -p 8000:8000 ecg-afib-backend
   ```
3. Deploy ke AWS App Runner / ECS / ECR sebagai container image.

> Jika ingin menggunakan model nyata nanti, tempatkan file H5 di folder `Models/` dengan nama `afib_cnn_1d_best.h5`.

## Struktur repository
- `backend/` - service FastAPI utama
- `requirements.txt` - dependency Python
- `Dockerfile` - container image runtime
- `.dockerignore` - file yang diabaikan oleh Docker build
- `README.md` - dokumentasi proyek
- `legacy/` - contoh script lama (`AritmiaAFIB.py`, `Train2.py`)
- `Models/` - lokasi model
