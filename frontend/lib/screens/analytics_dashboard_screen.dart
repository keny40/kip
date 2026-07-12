import 'package:flutter/material.dart';

import '../models/analytics.dart';
import '../services/api_client.dart';

class AnalyticsDashboardScreen extends StatefulWidget {
  const AnalyticsDashboardScreen({super.key});

  @override
  State<AnalyticsDashboardScreen> createState() => _AnalyticsDashboardScreenState();
}

class _AnalyticsDashboardScreenState extends State<AnalyticsDashboardScreen> {
  late Future<AnalyticsDashboardSummary> _future = ApiClient().fetchAnalyticsDashboard();

  void _reload() {
    setState(() {
      _future = ApiClient().fetchAnalyticsDashboard();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('분석'),
        actions: [
          IconButton(
            onPressed: _reload,
            icon: const Icon(Icons.refresh_outlined),
            tooltip: 'Refresh',
          ),
        ],
      ),
      body: FutureBuilder<AnalyticsDashboardSummary>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return _ErrorState(message: snapshot.error.toString(), onRetry: _reload);
          }
          final summary = snapshot.data;
          if (summary == null) {
            return const _EmptyState(message: '표시할 분석 데이터가 없습니다.');
          }
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Text('시스템 현황', style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 16),
              Wrap(
                spacing: 12,
                runSpacing: 12,
                children: [
                  _MetricCard(label: '경주', value: '${summary.totalRaces}'),
                  _MetricCard(label: '예정', value: '${summary.scheduledRaces}'),
                  _MetricCard(label: '진행 중', value: '${summary.inProgressRaces}'),
                  _MetricCard(label: '완료', value: '${summary.completedRaces}'),
                  _MetricCard(label: '선수', value: '${summary.totalPlayers}'),
                  _MetricCard(label: '결과', value: '${summary.totalResults}'),
                  _MetricCard(label: '경기장', value: '${summary.trackCount}'),
                ],
              ),
              const SizedBox(height: 16),
              Card(
                elevation: 0,
                child: ListTile(
                  title: const Text('최근 경주일'),
                  trailing: Text(summary.latestRaceDate ?? '-'),
                ),
              ),
              const SizedBox(height: 16),
              FilledButton.icon(
                onPressed: _reload,
                icon: const Icon(Icons.analytics),
                label: const Text('새로고침'),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _MetricCard extends StatelessWidget {
  const _MetricCard({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 160,
      child: Card(
        elevation: 0,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: Theme.of(context).textTheme.labelLarge),
              const SizedBox(height: 8),
              Text(value, style: Theme.of(context).textTheme.headlineSmall),
            ],
          ),
        ),
      ),
    );
  }
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('분석을 불러오지 못했습니다', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            FilledButton(onPressed: onRetry, child: const Text('다시 시도')),
          ],
        ),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Center(child: Text(message, textAlign: TextAlign.center));
  }
}
