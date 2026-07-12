import 'csv_file_picker_stub.dart' if (dart.library.html) 'csv_file_picker_web.dart';

class CsvFileSelection {
  const CsvFileSelection({
    required this.filename,
    required this.bytes,
  });

  final String filename;
  final List<int> bytes;
}

abstract class CsvFilePicker {
  Future<CsvFileSelection?> pickCsvFile();
}

CsvFilePicker createCsvFilePicker() => createPlatformCsvFilePicker();
