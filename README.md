# ECG AFIB Detection Backend AWS

Backend FastAPI untuk deteksi AFIB berbasis ECG yang disiapkan untuk AWS EC2 sesuai arsitektur: model H5 dari S3, prediksi ke DynamoDB, raw signal/report ke S3, notifikasi AFIB ke SNS, dan log aplikasi ke CloudWatch melalui log EC2/container.

## Struktur utama
- `backend/app.py` - FastAPI server dengan endpoint `/generate`, `/generate-afib`, `/predict`, `/predict-dummy`, `/latest`, `/history`, `/health`, `/test`
- `backend/config.py` - konfigurasi runtime dari environment variables AWS
- `backend/aws_services.py` - integrasi S3 untuk artefak prediksi dan SNS untuk alert AFIB
- `backend/model.py` - load model H5 dari S3 ke EC2/container sebelum inference
- `backend/signal.py` - preprocessing sinyal ECG dan generator data dummy
- `backend/database.py` - penyimpanan hasil prediksi ke DynamoDB
- `requirements.txt` - paket Python untuk runtime
- `Dockerfile` - container image untuk menjalankan backend
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
  - Menghasilkan data ECG dummy 5 detik. Tambahkan `?afib=true` untuk membuat sinyal AFIB.
- `GET /generate-afib`
  - Menghasilkan data ECG dummy AFIB secara langsung
- `POST /predict`
  - Menerima JSON: `{ "signal": [float], "sample_rate": 250, "threshold": 0.5, "metadata": {} }`
  - Menyimpan metadata ke DynamoDB, artefak ke S3, dan mengirim SNS jika label `AFIB`
- `POST /predict-dummy`
  - Membuat data ECG dummy, menjalankan prediksi, lalu menyimpan hasilnya ke DynamoDB/S3. Tambahkan `?afib=true` untuk dummy AFIB.
- `GET /latest`
  - Mengembalikan metadata model dan prediksi terakhir
- `GET /history`
  - Mengembalikan daftar hasil prediksi yang tersimpan di DynamoDB
- `GET /health` atau `GET /test`
  - Health check untuk EC2 load balancer atau monitoring

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
```

`MODEL_ALLOW_DUMMY=false` membuat service gagal start jika model H5 tidak tersedia. Gunakan `true` hanya untuk demo endpoint dan smoke test.

## Jalankan di EC2 dengan Docker

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
```bash
curl http://EC2_PUBLIC_IP:8000/health
```

```bash
curl "http://EC2_PUBLIC_IP:8000/generate?afib=true"
```

```bash
curl -X POST "http://EC2_PUBLIC_IP:8000/predict-dummy?afib=true"
```

Untuk `/predict`, kirim minimal 100 sampel ECG dari frontend atau ambil payload signal dari `/generate`.
