import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/map_context.dart';
import '../models/driver_state.dart';
import '../models/advice_v2.dart';

class ApiService {
  // Use 10.0.2.2 for Android Emulator, or 127.0.0.1 when using 'adb reverse tcp:8000 tcp:8000' on USB device
  final String baseUrl;
  final http.Client _client;

  ApiService({this.baseUrl = 'http://127.0.0.1:8000', http.Client? client})
      : _client = client ?? http.Client();

  Future<MapContextData?> fetchMapContext({String scenarioId = 'default_hcm', int seed = 42}) async {
    try {
      final uri = Uri.parse('$baseUrl/api/v1/map-context?scenario_id=$scenarioId&seed=$seed');
      final response = await _client.get(uri).timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return MapContextData.fromJson(data);
      }
    } catch (e) {
      print('Error fetching map context: $e');
    }
    return null;
  }

  Future<DriverStateData?> fetchDriverState({String scenarioId = 'default_hcm', int seed = 42}) async {
    try {
      final uri = Uri.parse('$baseUrl/api/v1/driver/state?scenario_id=$scenarioId&seed=$seed');
      final response = await _client.get(uri).timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return DriverStateData.fromJson(data);
      }
    } catch (e) {
      print('Error fetching driver state: $e');
    }
    return null;
  }

  Future<AdviceFetchResultV2> fetchAdviceV2({
    required String surface,
    required String driverId,
    required String date,
    required int nowMin,
    required int shiftStartMin,
    required int shiftEndMin,
    required bool isDriving,
  }) async {
    final uri = Uri.parse('$baseUrl/api/v2/advice').replace(queryParameters: {
      'surface': surface,
      'driver_id': driverId,
      'date': date,
      'now_min': '$nowMin',
      'shift_start_min': '$shiftStartMin',
      'shift_end_min': '$shiftEndMin',
      'is_driving': '$isDriving',
    });
    try {
      final response = await _client.get(uri).timeout(const Duration(seconds: 5));
      if (response.statusCode == 503) {
        return const AdviceFetchResultV2(disabled: true);
      }
      if (response.statusCode == 200) {
        return AdviceFetchResultV2(
          disabled: false,
          envelope: AdviceEnvelopeV2.fromJson(
              json.decode(response.body) as Map<String, dynamic>),
        );
      }
    } catch (e) {
      print('Error fetching advice v2: $e');
    }
    return const AdviceFetchResultV2(disabled: false);
  }

  Future<void> acknowledgeAdviceDisplay(AdviceCardV2 card) async {
    await _postAdviceEvent(card, 'display', {
      'display_id': card.displayId,
      'client_event_id': 'mount-${card.displayId}',
      'mounted_at': DateTime.now().toUtc().toIso8601String(),
    });
  }

  Future<void> respondToAdvice(AdviceCardV2 card, String response) async {
    await _postAdviceEvent(card, 'response', {
      'display_id': card.displayId,
      'client_event_id': _clientEventId(response),
      'response': response,
      'occurred_at': DateTime.now().toUtc().toIso8601String(),
    });
  }

  Future<void> _postAdviceEvent(
      AdviceCardV2 card, String endpoint, Map<String, dynamic> body) async {
    final uri = Uri.parse(
        '$baseUrl/api/v2/advice/${Uri.encodeComponent(card.checkpointId)}/$endpoint');
    final response = await _client.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: json.encode(body),
    ).timeout(const Duration(seconds: 5));
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw Exception('$endpoint advice -> ${response.statusCode}');
    }
  }

  String _clientEventId(String kind) =>
      '$kind-${DateTime.now().microsecondsSinceEpoch}-${identityHashCode(this)}';
}
