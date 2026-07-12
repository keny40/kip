import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:kip_frontend/models/current_user.dart';
import 'package:kip_frontend/services/auth_service.dart';

void main() {
  CurrentUser adminUser() => CurrentUser(
        id: 1,
        email: 'admin@example.com',
        username: 'admin',
        role: 'admin',
        status: 'active',
        createdAt: DateTime.parse('2026-07-12T00:00:00Z'),
        updatedAt: DateTime.parse('2026-07-12T00:00:00Z'),
      );

  test('login stores token and authorization header is generated', () async {
    final session = AuthSession();
    final client = MockClient((request) async {
      if (request.url.path.endsWith('/auth/login')) {
        return http.Response(
          jsonEncode({'access_token': 'token-123', 'token_type': 'bearer', 'expires_in': 3600}),
          200,
          headers: {'content-type': 'application/json'},
        );
      }
      if (request.url.path.endsWith('/auth/me')) {
        expect(request.headers['authorization'], 'Bearer token-123');
        return http.Response(
          jsonEncode({
            'id': 1,
            'email': 'admin@example.com',
            'username': 'admin',
            'role': 'admin',
            'status': 'active',
            'created_at': '2026-07-12T00:00:00Z',
            'updated_at': '2026-07-12T00:00:00Z',
          }),
          200,
          headers: {'content-type': 'application/json'},
        );
      }
      return http.Response('Not found', 404);
    });

    final service = AuthService(client: client, baseUrl: 'http://localhost:8000', session: session);
    final user = await service.login('admin@example.com', 'password');

    expect(user.role, 'admin');
    expect(service.isLoggedIn, isTrue);
    expect(service.accessToken, 'token-123');
    expect(service.authorizationHeaders(), {'Authorization': 'Bearer token-123'});
  });

  test('login rejects non-admin users and clears the session', () async {
    final session = AuthSession();
    final client = MockClient((request) async {
      if (request.url.path.endsWith('/auth/login')) {
        return http.Response(
          jsonEncode({'access_token': 'token-456', 'token_type': 'bearer', 'expires_in': 3600}),
          200,
          headers: {'content-type': 'application/json'},
        );
      }
      if (request.url.path.endsWith('/auth/me')) {
        return http.Response(
          jsonEncode({
            'id': 2,
            'email': 'user@example.com',
            'username': 'user',
            'role': 'user',
            'status': 'active',
            'created_at': '2026-07-12T00:00:00Z',
            'updated_at': '2026-07-12T00:00:00Z',
          }),
          200,
          headers: {'content-type': 'application/json'},
        );
      }
      return http.Response('Not found', 404);
    });

    final service = AuthService(client: client, baseUrl: 'http://localhost:8000', session: session);

    await expectLater(
      service.login('user@example.com', 'password'),
      throwsA(
        isA<AuthException>().having((error) => error.kind, 'kind', AuthErrorKind.forbidden),
      ),
    );
    expect(service.isLoggedIn, isFalse);
    expect(service.authorizationHeaders(), isEmpty);
  });

  test('logout clears current session state', () async {
    final session = AuthSession();
    final service = AuthService(client: MockClient((_) async => http.Response('{}', 200)), baseUrl: 'http://localhost:8000', session: session);

    session.accessToken = 'token-789';
    session.currentUser = adminUser();
    service.logout();

    expect(service.isLoggedIn, isFalse);
    expect(service.accessToken, isNull);
    expect(service.currentUser, isNull);
  });

  test('invalid credentials and network errors are distinguishable', () async {
    final session = AuthSession();
    final client = MockClient((request) async {
      if (request.url.path.endsWith('/auth/login')) {
        return http.Response('{"detail":"invalid"}', 401, headers: {'content-type': 'application/json'});
      }
      return http.Response('Not found', 404);
    });
    final service = AuthService(client: client, baseUrl: 'http://localhost:8000', session: session);

    await expectLater(
      service.login('admin@example.com', 'wrong'),
      throwsA(
        isA<AuthException>().having((error) => error.kind, 'kind', AuthErrorKind.invalidCredentials),
      ),
    );

    final networkService = AuthService(
      client: MockClient((_) => throw http.ClientException('network failure')),
      baseUrl: 'http://localhost:8000',
      session: AuthSession(),
    );
    await expectLater(
      networkService.login('admin@example.com', 'password'),
      throwsA(
        isA<AuthException>().having((error) => error.kind, 'kind', AuthErrorKind.network),
      ),
    );
  });
}
