import 'package:flutter/material.dart';

String adminValue(Object? value) {
  if (value == null || value.toString().isEmpty) return '-';
  return value.toString();
}

String adminDate(DateTime? value) {
  if (value == null) return '-';
  return value
      .toLocal()
      .toIso8601String()
      .replaceFirst('T', ' ')
      .split('.')
      .first;
}

class AdminFilterPanel extends StatelessWidget {
  const AdminFilterPanel({
    super.key,
    required this.children,
    required this.onSearch,
    required this.onReset,
  });

  final List<Widget> children;
  final VoidCallback onSearch;
  final VoidCallback onReset;

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0,
      child: ExpansionTile(
        initiallyExpanded: true,
        title: const Text('필터'),
        childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
        children: [
          Wrap(spacing: 12, runSpacing: 12, children: children),
          const SizedBox(height: 12),
          Row(
            children: [
              FilledButton.icon(
                key: const Key('admin_filter_search'),
                onPressed: onSearch,
                icon: const Icon(Icons.search),
                label: const Text('검색'),
              ),
              const SizedBox(width: 8),
              OutlinedButton.icon(
                key: const Key('admin_filter_reset'),
                onPressed: onReset,
                icon: const Icon(Icons.refresh),
                label: const Text('초기화'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class AdminPaginationBar extends StatelessWidget {
  const AdminPaginationBar({
    super.key,
    required this.page,
    required this.pageSize,
    required this.total,
    required this.onPrevious,
    required this.onNext,
    required this.onPageSizeChanged,
  });

  final int page;
  final int pageSize;
  final int total;
  final VoidCallback? onPrevious;
  final VoidCallback? onNext;
  final ValueChanged<int?> onPageSizeChanged;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      alignment: WrapAlignment.end,
      crossAxisAlignment: WrapCrossAlignment.center,
      spacing: 8,
      children: [
        Text('총 $total건 · $page페이지'),
        DropdownButton<int>(
          key: const Key('admin_page_size'),
          value: pageSize,
          items: const [10, 20, 50, 100]
              .map((value) =>
                  DropdownMenuItem(value: value, child: Text('$value개')))
              .toList(),
          onChanged: onPageSizeChanged,
        ),
        IconButton(
            onPressed: onPrevious,
            icon: const Icon(Icons.chevron_left),
            tooltip: '이전 페이지'),
        IconButton(
            onPressed: onNext,
            icon: const Icon(Icons.chevron_right),
            tooltip: '다음 페이지'),
      ],
    );
  }
}

Widget adminMessageCard(BuildContext context, String message,
    {bool error = false}) {
  return Card(
    elevation: 0,
    color: error ? Theme.of(context).colorScheme.errorContainer : null,
    child: Padding(
      padding: const EdgeInsets.all(24),
      child: Center(child: Text(message)),
    ),
  );
}
