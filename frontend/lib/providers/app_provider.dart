import 'package:flutter/foundation.dart';

class AppProvider extends ChangeNotifier {
  bool _isReady = false;

  bool get isReady => _isReady;

  void markReady() {
    _isReady = true;
    notifyListeners();
  }
}
