import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/map_context.dart';
import '../models/driver_state.dart';

class ApiService {
  // Use 10.0.2.2 for Android Emulator, or 127.0.0.1 when using 'adb reverse tcp:8000 tcp:8000' on USB device
  static const String baseUrl = 'http://127.0.0.1:8000';

  Future<MapContextData?> fetchMapContext({String scenarioId = 'default_hcm', int seed = 42}) async {
    try {
      final uri = Uri.parse('$baseUrl/api/v1/map-context?scenario_id=$scenarioId&seed=$seed');
      final response = await http.get(uri).timeout(const Duration(seconds: 5));
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
      final response = await http.get(uri).timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return DriverStateData.fromJson(data);
      }
    } catch (e) {
      print('Error fetching driver state: $e');
    }
    return null;
  }
}
