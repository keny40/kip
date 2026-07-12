import '../services/api_service.dart';

class AppRepository {
  const AppRepository(this._apiService);

  final ApiService _apiService;

  Future<void> ping() async {
    await _apiService.ping();
  }
}
