FROM ghcr.io/cirruslabs/flutter:stable AS build

WORKDIR /app

COPY frontend/pubspec.yaml frontend/pubspec.lock ./frontend/
WORKDIR /app/frontend
RUN flutter pub get

COPY frontend/ /app/frontend/
ARG KIP_API_BASE_URL=http://localhost:8000
RUN flutter build web --release --dart-define=KIP_API_BASE_URL=${KIP_API_BASE_URL}

FROM nginx:1.27-alpine

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/frontend/build/web /usr/share/nginx/html

EXPOSE 5001

CMD ["nginx", "-g", "daemon off;"]
