# ECG AFIB Detection Backend AWS

Backend FastAPI untuk deteksi AFIB berbasis ECG yang disiapkan untuk AWS EC2 sesuai arsitektur: model H5 dari S3, prediksi ke DynamoDB, raw signal/report ke S3, notifikasi AFIB ke SNS, dan log aplikasi ke CloudWatch melalui log EC2/container.

## Struktur utama
- `backend/app.py` - FastAPI server dengan endpoint `/generate`, `/stream/start`, `/stream/latest`, `/stream/status`, `/stream/stop`, `/predict`, `/predict-stream`, `/predict-dummy`, `/latest`, `/history`
- `backend/config.py` - konfigurasi runtime dari environment variables AWS
- `backend/aws_services.py` - integrasi S3 untuk artefak prediksi dan SNS untuk alert AFIB
- `backend/model.py` - load model H5 dari S3 ke EC2/container sebelum inference
- `backend/signal_utils.py` - preprocessing sinyal ECG, generator data dummy, dan generator sinyal ECG kontinu
- `backend/database.py` - penyimpanan hasil prediksi ke DynamoDB
- `requirements.txt` - paket Python untuk runtime
- `Dockerfile` - container image untuk menjalankan backend
- `Frontend/Dockerfile` - container image untuk build dan serve frontend React dengan Nginx
- `Frontend/nginx.conf` - konfigurasi Nginx untuk frontend dan reverse proxy `/api` ke backend
- `docker-compose.yml` - menjalankan backend dan frontend sebagai satu stack Docker
- `.env.aws.example` - contoh environment AWS
- `aws-iam-policy.example.json` - contoh IAM policy minimal untuk EC2 role

## AWS resources
Siapkan resource berikut sebelum menjalankan container di EC2:

- S3 bucket model, berisi `models/afib_cnn_1d_best.h5`
- S3 bucket prediksi untuk `raw_signal.json` dan `prediction_report.json`
- DynamoDB table `ecg_predictions` dengan partition key `prediction_id` bertipe `String`
- DynamoDB GSI `prediction_created_at_index` dengan partition key `record_type` dan sort key `created_at`
- SNS topic untuk email notification AFIB
- IAM Role pada EC2 dengan izin di `aws-iam-policy.example.json`

## Endpoint
- `GET /generate`
  - Menghasilkan data ECG dummy 5 detik. Default `?afib=false` membuat sinyal normal, sedangkan `?afib=true` membuat sinyal AFIB.
- `POST /stream/start`
  - Memulai sinyal ECG kontinu di background. Gunakan `?afib=false` untuk normal atau `?afib=true` untuk AFIB.
- `GET /stream/latest`
  - Mengambil potongan sinyal terbaru dari buffer stream. Query `?seconds=5` mengambil 5 detik terakhir.
- `GET /stream/status`
  - Melihat apakah stream sedang berjalan, jumlah sampel tersedia, dan mode AFIB/normal.
- `POST /stream/stop`
  - Menghentikan sinyal ECG kontinu.
- `POST /predict`
  - Menerima JSON: `{ "signal": [float], "sample_rate": 250, "threshold": 0.5, "metadata": {} }`
  - Menyimpan metadata ke DynamoDB, artefak ke S3, dan mengirim SNS jika label `AFIB`
- `POST /predict-stream`
  - Mengambil sinyal terbaru dari stream, menjalankan prediksi, lalu menyimpan hasilnya ke DynamoDB/S3/SNS.
- `POST /predict-dummy`
  - Membuat data ECG dummy, menjalankan prediksi, lalu menyimpan hasilnya ke DynamoDB/S3. Tambahkan `?afib=true` untuk dummy AFIB.
- `GET /latest`
  - Mengembalikan metadata model dan prediksi terakhir
- `GET /history`
  - Mengembalikan daftar hasil prediksi yang tersimpan di DynamoDB
## Environment variables

```bash
APP_NAME=ecg-afib-backend
AWS_REGION=ap-southeast-1
DYNAMODB_TABLE=ecg_predictions
DYNAMODB_CREATED_AT_INDEX=prediction_created_at_index
MODEL_S3_BUCKET=your-model-bucket
MODEL_S3_KEY=models/afib_cnn_1d_best.h5
MODEL_ALLOW_DUMMY=false
PREDICTION_S3_BUCKET=your-prediction-bucket
PREDICTION_S3_PREFIX=ecg-predictions
SNS_TOPIC_ARN=arn:aws:sns:ap-southeast-1:123456789012:ecg-afib-alerts
SNS_ALERT_ON_LABEL=AFIB
STREAM_BUFFER_SECONDS=60
STREAM_CHUNK_SECONDS=0.2
```

`MODEL_ALLOW_DUMMY=false` membuat service gagal start jika model H5 tidak tersedia. Gunakan `true` hanya untuk demo sementara.

## Jalankan full stack dengan Docker Compose

Siapkan file environment backend dari contoh:

```bash
cp .env.aws.example .env.aws
nano .env.aws
```

Untuk mode Docker Compose, frontend akan diakses dari port `80` dan request API akan lewat path `/api`, lalu Nginx meneruskannya ke container backend. Jadi frontend tidak perlu memakai Public IP EC2 langsung di `VITE_API_URL`.

Jalankan:

```bash
docker compose up -d --build
```

Akses aplikasi:

```bash
http://EC2_PUBLIC_IP
```

Backend juga tetap terbuka langsung untuk testing:

```bash
http://EC2_PUBLIC_IP:8000
```

Lihat log:

```bash
docker compose logs -f
```

Stop stack:

```bash
docker compose down
```

## Jalankan backend saja di EC2 dengan Docker

```bash
docker build -t ecg-afib-backend .
docker run -d \
  --name ecg-afib-backend \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file .env.aws \
  ecg-afib-backend
```

CloudWatch dapat membaca log dari stdout container melalui CloudWatch Agent atau integrasi log service container yang digunakan.

## Contoh request
Mulai stream ECG normal:
```bash
curl -X POST "http://EC2_PUBLIC_IP:8000/stream/start?afib=false"
```

Ambil 5 detik sinyal terbaru untuk digambar frontend:
```bash
curl "http://EC2_PUBLIC_IP:8000/stream/latest?seconds=5"
```

Prediksi dari stream terbaru:
```bash
curl -X POST "http://EC2_PUBLIC_IP:8000/predict-stream?seconds=5"
```

Stop stream:
```bash
curl -X POST "http://EC2_PUBLIC_IP:8000/stream/stop"
```

```bash
curl "http://EC2_PUBLIC_IP:8000/generate?afib=true"
```

```bash
curl -X POST "http://EC2_PUBLIC_IP:8000/predict-dummy?afib=true"
```

Untuk `/predict`, kirim minimal 100 sampel ECG dari frontend atau ambil payload signal dari `/generate`.
