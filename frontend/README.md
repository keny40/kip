# KIP Frontend

Flutter Web front-end for the KIP local MVP demo.

## Run

```bash
flutter run -d chrome \
  --web-port 5001 \
  --dart-define=KIP_API_BASE_URL=http://127.0.0.1:8000
```

If the API runs on a different host, update `KIP_API_BASE_URL` accordingly.
