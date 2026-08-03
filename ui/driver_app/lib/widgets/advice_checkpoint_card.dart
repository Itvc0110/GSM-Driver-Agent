import 'package:flutter/material.dart';

import '../models/advice_v2.dart';

class AdviceCheckpointCard extends StatefulWidget {
  final AdviceCardV2 card;
  final Future<void> Function() onMounted;
  final Future<void> Function(String response) onResponse;

  const AdviceCheckpointCard({
    super.key,
    required this.card,
    required this.onMounted,
    required this.onResponse,
  });

  @override
  State<AdviceCheckpointCard> createState() => _AdviceCheckpointCardState();
}

class _AdviceCheckpointCardState extends State<AdviceCheckpointCard> {
  bool _expanded = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) widget.onMounted();
    });
  }

  @override
  Widget build(BuildContext context) {
    final card = widget.card;
    final actionCode = card.canonicalAction['code']?.toString() ?? 'NO_ACTION';
    final provenanceBadge = card.provenance.isMock
        ? 'MOCK'
        : card.provenance.dataMode.toUpperCase().contains('PROXY')
            ? 'PROXY'
            : null;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFFF0FDF4),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF00AFB9).withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(card.title,
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              ),
              if (provenanceBadge != null)
                Chip(
                  label: Text(provenanceBadge),
                  visualDensity: VisualDensity.compact,
                ),
            ],
          ),
          const SizedBox(height: 8),
          Text(card.summary, style: const TextStyle(height: 1.4)),
          const SizedBox(height: 8),
          Text('Hành động: $actionCode', key: const Key('canonical-action')),
          if (card.actionWindow != null)
            Text(
              '${card.actionWindow!['start']} → ${card.actionWindow!['end']}',
              key: const Key('canonical-window'),
              style: const TextStyle(fontSize: 12, color: Colors.black54),
            ),
          if (_expanded) ...[
            const SizedBox(height: 10),
            Text(card.why, key: const Key('advice-why')),
            for (final number in card.numbers)
              Text('${number.value} ${number.unit} · ${number.source}'),
            const SizedBox(height: 8),
            Text(
              '${card.provenance.dataMode} · ${card.provenance.policyVersion} · '
              '${card.solverSet.join('+')}',
              style: const TextStyle(fontSize: 11, color: Colors.grey),
            ),
          ],
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            children: [
              TextButton(
                onPressed: () => widget.onResponse('accepted'),
                child: const Text('Làm theo'),
              ),
              TextButton(
                onPressed: () => widget.onResponse('dismissed'),
                child: const Text('Bỏ qua'),
              ),
              TextButton(
                onPressed: () {
                  setState(() => _expanded = !_expanded);
                  widget.onResponse('expanded');
                },
                child: const Text('Vì sao'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
