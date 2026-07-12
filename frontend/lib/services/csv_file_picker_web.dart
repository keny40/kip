// ignore_for_file: deprecated_member_use

import 'dart:async';
import 'dart:convert';
import 'dart:html' as html;

import 'csv_file_picker.dart';

CsvFilePicker createPlatformCsvFilePicker() => WebCsvFilePicker();

class WebCsvFilePicker implements CsvFilePicker {
  @override
  Future<CsvFileSelection?> pickCsvFile() async {
    final input = html.FileUploadInputElement()
      ..accept = '.csv,text/csv'
      ..multiple = false;
    input.style
      ..position = 'fixed'
      ..left = '-10000px'
      ..top = '0'
      ..width = '1px'
      ..height = '1px'
      ..opacity = '0';
    html.document.body?.append(input);
    final selectionEvent = Completer<void>();
    late final StreamSubscription<html.Event> changeSubscription;
    late final StreamSubscription<html.Event> inputSubscription;

    void completeSelectionEvent([html.Event? _]) {
      if (!selectionEvent.isCompleted) {
        selectionEvent.complete();
      }
    }

    changeSubscription = input.onChange.listen(completeSelectionEvent);
    inputSubscription = input.onInput.listen(completeSelectionEvent);

    input.click();

    await selectionEvent.future;
    await changeSubscription.cancel();
    await inputSubscription.cancel();

    final file = input.files?.isNotEmpty == true ? input.files!.first : null;
    if (file == null) {
      return null;
    }

    final reader = html.FileReader();
    final completer = Completer<CsvFileSelection?>();
    reader.onLoadEnd.listen((_) {
      final result = reader.result;
      if (result is String) {
        completer.complete(
          CsvFileSelection(
            filename: file.name,
            bytes: utf8.encode(result),
          ),
        );
        return;
      }
      completer.complete(null);
    });
    reader.readAsText(file);
    return completer.future;
  }
}
