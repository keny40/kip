class AppConfig {
  static const String apiBaseUrl = String.fromEnvironment(
    'KIP_API_BASE_URL',
    defaultValue: 'http://localhost:8000',
  );
}
