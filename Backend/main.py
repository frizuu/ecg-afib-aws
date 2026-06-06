# Backend FastAPI untuk Smart Health Monitoring - AFIB Detection
# File ini akan berisi:
# - Dummy ECG generator
# - Endpoint generate normal
# - Endpoint generate AFIB
# - Endpoint latest
# - Endpoint history
# - Integrasi DynamoDB dan SNS saat dijalankan di AWS

# Endpoint yang direncanakan:
# GET /
# GET /generate
# GET /generate-window?condition=normal
# GET /generate-window?condition=afib
# GET /latest
# GET /history