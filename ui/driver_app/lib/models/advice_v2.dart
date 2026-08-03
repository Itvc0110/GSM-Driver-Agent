class AdviceNumberV2 {
  final String id;
  final num value;
  final String unit;
  final String source;
  final String artifactRef;

  const AdviceNumberV2({
    required this.id,
    required this.value,
    required this.unit,
    required this.source,
    required this.artifactRef,
  });

  factory AdviceNumberV2.fromJson(Map<String, dynamic> json) => AdviceNumberV2(
        id: json['id'] as String,
        value: json['value'] as num,
        unit: json['unit'] as String,
        source: json['source'] as String,
        artifactRef: json['artifact_ref'] as String,
      );
}

class AdviceProvenanceV2 {
  final String snapshotRef;
  final List<String> solverInputRefs;
  final List<String> solverReportRefs;
  final String policyVersion;
  final String checkpointSchemaVersion;
  final String dataMode;
  final bool isMock;

  const AdviceProvenanceV2({
    required this.snapshotRef,
    required this.solverInputRefs,
    required this.solverReportRefs,
    required this.policyVersion,
    required this.checkpointSchemaVersion,
    required this.dataMode,
    required this.isMock,
  });

  factory AdviceProvenanceV2.fromJson(Map<String, dynamic> json) => AdviceProvenanceV2(
        snapshotRef: json['snapshot_ref'] as String,
        solverInputRefs: List<String>.from(json['solver_input_refs'] as List),
        solverReportRefs: List<String>.from(json['solver_report_refs'] as List),
        policyVersion: json['policy_version'] as String,
        checkpointSchemaVersion: json['checkpoint_schema_version'] as String,
        dataMode: json['data_mode'] as String,
        isMock: json['is_mock'] as bool,
      );
}

class AdviceCardV2 {
  final String checkpointId;
  final String displayId;
  final String topic;
  final String surface;
  final Map<String, dynamic> canonicalAction;
  final Map<String, dynamic>? actionWindow;
  final List<Map<String, dynamic>> futurePlan;
  final String title;
  final String summary;
  final String why;
  final Map<String, dynamic> validity;
  final String confidenceBand;
  final List<String> caveatIds;
  final List<AdviceNumberV2> numbers;
  final AdviceProvenanceV2 provenance;
  final List<String> solverSet;
  final List<String> responseOptions;

  const AdviceCardV2({
    required this.checkpointId,
    required this.displayId,
    required this.topic,
    required this.surface,
    required this.canonicalAction,
    required this.actionWindow,
    required this.futurePlan,
    required this.title,
    required this.summary,
    required this.why,
    required this.validity,
    required this.confidenceBand,
    required this.caveatIds,
    required this.numbers,
    required this.provenance,
    required this.solverSet,
    required this.responseOptions,
  });

  factory AdviceCardV2.fromJson(Map<String, dynamic> json) => AdviceCardV2(
        checkpointId: json['checkpoint_id'] as String,
        displayId: json['display_id'] as String,
        topic: json['topic'] as String,
        surface: json['surface'] as String,
        canonicalAction: Map<String, dynamic>.from(json['canonical_action'] as Map),
        actionWindow: json['action_window'] == null
            ? null
            : Map<String, dynamic>.from(json['action_window'] as Map),
        futurePlan: (json['future_plan'] as List)
            .map((value) => Map<String, dynamic>.from(value as Map))
            .toList(),
        title: json['title'] as String,
        summary: json['summary'] as String,
        why: json['why'] as String,
        validity: Map<String, dynamic>.from(json['validity'] as Map),
        confidenceBand: json['confidence_band'] as String,
        caveatIds: List<String>.from(json['caveat_ids'] as List),
        numbers: (json['numbers'] as List)
            .map((value) => AdviceNumberV2.fromJson(value as Map<String, dynamic>))
            .toList(),
        provenance: AdviceProvenanceV2.fromJson(
            json['provenance'] as Map<String, dynamic>),
        solverSet: List<String>.from(json['solver_set'] as List),
        responseOptions: List<String>.from(json['response_options'] as List),
      );
}

class AdviceEnvelopeV2 {
  final String status;
  final String surface;
  final String generatedAt;
  final String? silentReason;
  final List<AdviceCardV2> items;

  const AdviceEnvelopeV2({
    required this.status,
    required this.surface,
    required this.generatedAt,
    required this.silentReason,
    required this.items,
  });

  factory AdviceEnvelopeV2.fromJson(Map<String, dynamic> json) => AdviceEnvelopeV2(
        status: json['status'] as String,
        surface: json['surface'] as String,
        generatedAt: json['generated_at'] as String,
        silentReason: (json['silent'] as Map<String, dynamic>?)?['reason_code'] as String?,
        items: (json['items'] as List)
            .map((value) => AdviceCardV2.fromJson(value as Map<String, dynamic>))
            .toList(),
      );
}

class AdviceFetchResultV2 {
  final bool disabled;
  final AdviceEnvelopeV2? envelope;

  const AdviceFetchResultV2({required this.disabled, this.envelope});
}
