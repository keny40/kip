// ignore_for_file: deprecated_member_use

import 'dart:html' as html;

void openExternalLink(String url) {
  html.window.open(url, '_blank');
}
