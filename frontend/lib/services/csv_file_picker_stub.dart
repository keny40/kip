import 'csv_file_picker.dart';

CsvFilePicker createPlatformCsvFilePicker() => _UnsupportedCsvFilePicker();

class _UnsupportedCsvFilePicker implements CsvFilePicker {
  @override
  Future<CsvFileSelection?> pickCsvFile() async {
    return null;
  }
}
