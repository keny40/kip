import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

import 'package:kip_frontend/models/admin_import.dart';
import 'package:kip_frontend/services/api_client.dart';

void main() {
  test('builds multipart admin csv upload request and parses result', () async {
    late http.BaseRequest capturedRequest;
    final client = _RecordingClient((request) async {
      capturedRequest = request;
      expect(request.method, 'POST');
      expect(request.url.path, '/api/v1/admin/imports/players');
      expect(request.url.queryParameters['dry_run'], 'true');
      expect(request.headers['Authorization'], 'Bearer admin-token');
      expect(request.headers['Accept'], 'application/json');
      expect(request, isA<http.MultipartRequest>());
      final multipart = request as http.MultipartRequest;
      expect(multipart.files, hasLength(1));
      expect(multipart.files.single.field, 'file');
      expect(multipart.files.single.filename, 'players.csv');
      expect(multipart.files.single.contentType.toString(), 'text/csv');
      return http.StreamedResponse(
        Stream.value(
          utf8.encode(
            jsonEncode({
              'import_type': 'players',
              'filename': 'players.csv',
              'dry_run': true,
              'total': 1,
              'created': 1,
              'updated': 0,
              'skipped': 0,
              'failed': 0,
              'errors': const [],
            }),
          ),
        ),
        200,
        headers: {'content-type': 'application/json'},
      );
    });

    final apiClient = ApiClient(client: client, baseUrl: 'http://localhost:8000', bearerToken: 'admin-token');
    final result = await apiClient.importAdminCsv(
      importType: 'players',
      bytes: utf8.encode('player_number,name,grade,region,status\n1,Alice,A1,Seoul,active\n'),
      filename: 'players.csv',
      dryRun: true,
    );

    expect(capturedRequest, isA<http.MultipartRequest>());
    expect(result, isA<AdminImportResult>());
    expect(result.importType, 'players');
    expect(result.dryRun, isTrue);
    expect(result.created, 1);
  });
}

class _RecordingClient extends http.BaseClient {
  _RecordingClient(this.onSend);

  final Future<http.StreamedResponse> Function(http.BaseRequest request) onSend;

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) {
    return onSend(request);
  }
}
