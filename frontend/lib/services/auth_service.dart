import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import '../models/auth.dart';
import '../models/current_user.dart';

enum AuthErrorKind {
  invalidCredentials,
  unauthorized,
  forbidden,
  network,
  server,
}

class AuthException implements Exception {
  const AuthException(this.kind, this.message);

  factory AuthException.invalidCredentials() =>
      const AuthException(AuthErrorKind.invalidCredentials, '이메일 또는 비밀번호가 올바르지 않습니다.');

  factory AuthException.unauthorized([String message = '로그인 세션이 만료되었습니다. 다시 로그인해 주세요.']) =>
      AuthException(AuthErrorKind.unauthorized, message);

  factory AuthException.forbidden([String message = '관리자 권한이 없습니다.']) =>
      AuthException(AuthErrorKind.forbidden, message);

  factory AuthException.network([String message = '서버 연결에 실패했습니다. 잠시 후 다시 시도해 주세요.']) =>
      AuthException(AuthErrorKind.network, message);

  factory AuthException.server([String message = '로그인 처리 중 오류가 발생했습니다.']) =>
      AuthException(AuthErrorKind.server, message);

  final AuthErrorKind kind;
  final String message;

  @override
  String toString() => message;
}

class AuthSession {
  AuthSession();

  static final AuthSession instance = AuthSession();

  String? accessToken;
  CurrentUser? currentUser;

  bool get isLoggedIn => accessToken != null && currentUser != null;

  void clear() {
    accessToken = null;
    currentUser = null;
  }

  Map<String, String> authorizationHeader() {
    final token = accessToken;
    if (token == null || token.isEmpty) {
      return const <String, String>{};
    }
    return <String, String>{'Authorization': 'Bearer $token'};
  }
}

class AuthService {
  AuthService({http.Client? client, String? baseUrl, AuthSession? session})
      : _client = client ?? http.Client(),
        _baseUrl = baseUrl ?? AppConfig.apiBaseUrl,
        _session = session ?? AuthSession.instance;

  final http.Client _client;
  final String _baseUrl;
  final AuthSession _session;

  AuthSession get session => _session;

  String? get accessToken => _session.accessToken;
  CurrentUser? get currentUser => _session.currentUser;
  bool get isLoggedIn => _session.isLoggedIn;

  Map<String, String> authorizationHeaders() => _session.authorizationHeader();

  Future<CurrentUser> login(String email, String password) async {
    http.Response response;
    try {
      response = await _postJson(
        '/api/v1/auth/login',
        {'email': email, 'password': password},
      );
    } on http.ClientException {
      _session.clear();
      throw AuthException.network();
    } on TimeoutException {
      _session.clear();
      throw AuthException.network();
    }

    if (response.statusCode == 401) {
      _session.clear();
      throw AuthException.invalidCredentials();
    }
    if (response.statusCode < 200 || response.statusCode >= 300) {
      _session.clear();
      throw _exceptionFromResponse();
    }

    final loginResponse = LoginResponse.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
    _session.accessToken = loginResponse.accessToken;

    final user = await fetchCurrentUser();
    if (user.role != 'admin') {
      _session.clear();
      throw AuthException.forbidden();
    }

    _session.currentUser = user;
    return user;
  }

  Future<CurrentUser> fetchCurrentUser() async {
    final token = _session.accessToken;
    if (token == null || token.isEmpty) {
      throw AuthException.unauthorized();
    }

    late final http.Response response;
    try {
      response = await _client.get(
        Uri.parse('$_baseUrl/api/v1/auth/me'),
        headers: {
          'Accept': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );
    } on http.ClientException {
      _session.clear();
      throw AuthException.network();
    } on TimeoutException {
      _session.clear();
      throw AuthException.network();
    }

    if (response.statusCode == 401) {
      _session.clear();
      throw AuthException.unauthorized();
    }
    if (response.statusCode == 403) {
      _session.clear();
      throw AuthException.forbidden();
    }
    if (response.statusCode < 200 || response.statusCode >= 300) {
      _session.clear();
      throw _exceptionFromResponse();
    }

    final user = CurrentUser.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
    if (user.status != 'active') {
      _session.clear();
      throw AuthException.unauthorized();
    }
    _session.currentUser = user;
    return user;
  }

  void logout() {
    _session.clear();
  }

  Future<http.Response> _postJson(String path, Map<String, dynamic> body) {
    return _client.post(
      Uri.parse('$_baseUrl$path'),
      headers: const {'Content-Type': 'application/json', 'Accept': 'application/json'},
      body: jsonEncode(body),
    );
  }

  AuthException _exceptionFromResponse() {
    return AuthException.server();
  }
}
