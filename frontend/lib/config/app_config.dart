class AppConfig {
  static const String _configuredApiBaseUrl = String.fromEnvironment(
    'KIP_API_BASE_URL',
    defaultValue: 'http://localhost:8000',
  );

  static String get apiBaseUrl => _configuredApiBaseUrl.isEmpty
      ? Uri.base.origin
      : _configuredApiBaseUrl;
}
