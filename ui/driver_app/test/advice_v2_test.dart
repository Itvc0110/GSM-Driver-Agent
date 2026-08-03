import 'package:driver_app/models/advice_v2.dart';
import 'package:driver_app/widgets/advice_checkpoint_card.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

Map<String, dynamic> fixture() => {
      'status': 'ready',
      'surface': 'nudge',
      'generated_at': '2026-08-03T09:00:00+07:00',
      'items': [
        {
          'checkpoint_id': 'ckpt-1',
          'display_id': 'display-1',
          'topic': 'energy',
          'surface': 'nudge',
          'canonical_action': {'code': 'SWAP', 'label_id': 'action.swap'},
          'action_window': null,
          'future_plan': [],
          'title': 'Đổi pin',
          'summary': 'Đổi pin trong khung được đề xuất.',
          'why': 'State runtime đã đủ.',
          'validity': {
            'valid_from': '2026-08-03T09:00:00+07:00',
            'valid_until': '2026-08-03T09:20:00+07:00',
            'freshness_deadline': '2026-08-03T09:20:00+07:00',
          },
          'confidence_band': 'high',
          'caveat_ids': [],
          'numbers': [],
          'provenance': {
            'snapshot_ref': 'state_snapshot:sha256:x',
            'solver_input_refs': ['solver_input:sha256:x'],
            'solver_report_refs': ['solver_report:sha256:x'],
            'policy_version': 'test',
            'checkpoint_schema_version': '1.1.0',
            'data_mode': 'live',
            'is_mock': false,
          },
          'solver_set': ['S2'],
          'response_options': ['accepted', 'dismissed', 'expanded'],
        }
      ],
    };

void main() {
  test('model preserves canonical server fields', () {
    final card = AdviceEnvelopeV2.fromJson(fixture()).items.single;
    expect(card.canonicalAction['code'], 'SWAP');
    expect(card.actionWindow, isNull);
    expect(card.provenance.dataMode, 'live');
  });

  testWidgets('mounted ACK runs once post-frame and expanded is side-channel',
      (tester) async {
    final card = AdviceEnvelopeV2.fromJson(fixture()).items.single;
    var mounted = 0;
    final responses = <String>[];
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: AdviceCheckpointCard(
          card: card,
          onMounted: () async {
            mounted++;
          },
          onResponse: (response) async {
            responses.add(response);
          },
        ),
      ),
    ));
    await tester.pump();
    expect(mounted, 1);
    expect(find.text('Hành động: SWAP'), findsOneWidget);
    await tester.pump();
    expect(mounted, 1);

    await tester.tap(find.text('Vì sao'));
    await tester.pump();
    expect(find.byKey(const Key('advice-why')), findsOneWidget);
    expect(responses, ['expanded']);
  });
}
