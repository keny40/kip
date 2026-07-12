class AdminImportError {
  const AdminImportError({
    required this.rowNumber,
    required this.errorCode,
    required this.errorMessage,
  });

  final int rowNumber;
  final String errorCode;
  final String errorMessage;

  factory AdminImportError.fromJson(Map<String, dynamic> json) {
    return AdminImportError(
      rowNumber: json['row_number'] as int,
      errorCode: json['error_code'] as String,
      errorMessage: json['error_message'] as String,
    );
  }
}

class AdminImportResult {
  const AdminImportResult({
    required this.importType,
    required this.filename,
    required this.dryRun,
    required this.total,
    required this.created,
    required this.updated,
    required this.skipped,
    required this.failed,
    required this.errors,
  });

  final String importType;
  final String filename;
  final bool dryRun;
  final int total;
  final int created;
  final int updated;
  final int skipped;
  final int failed;
  final List<AdminImportError> errors;

  factory AdminImportResult.fromJson(Map<String, dynamic> json) {
    return AdminImportResult(
      importType: json['import_type'] as String,
      filename: json['filename'] as String,
      dryRun: json['dry_run'] as bool,
      total: json['total'] as int,
      created: json['created'] as int,
      updated: json['updated'] as int,
      skipped: json['skipped'] as int,
      failed: json['failed'] as int,
      errors: (json['errors'] as List<dynamic>)
          .map((item) => AdminImportError.fromJson(item as Map<String, dynamic>))
          .toList(),
    );
  }
}
