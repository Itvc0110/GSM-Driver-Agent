class DriverLocationData {
  final double lat;
  final double lng;
  final double heading;
  final double speedKmh;

  DriverLocationData({
    required this.lat,
    required this.lng,
    required this.heading,
    required this.speedKmh,
  });

  factory DriverLocationData.fromJson(Map<String, dynamic> json) {
    return DriverLocationData(
      lat: (json['lat'] as num).toDouble(),
      lng: (json['lng'] as num).toDouble(),
      heading: (json['heading'] as num? ?? 0.0).toDouble(),
      speedKmh: (json['speed_kmh'] as num? ?? 0.0).toDouble(),
    );
  }
}

class DemandZoneData {
  final String h3Index;
  final double lat;
  final double lng;
  final double intensity;
  final int freshnessSec;

  DemandZoneData({
    required this.h3Index,
    required this.lat,
    required this.lng,
    required this.intensity,
    required this.freshnessSec,
  });

  factory DemandZoneData.fromJson(Map<String, dynamic> json) {
    return DemandZoneData(
      h3Index: json['h3_index'] as String,
      lat: (json['lat'] as num).toDouble(),
      lng: (json['lng'] as num).toDouble(),
      intensity: (json['intensity'] as num).toDouble(),
      freshnessSec: json['freshness_sec'] as int? ?? 30,
    );
  }
}

class ChargingStationData {
  final String id;
  final String name;
  final double lat;
  final double lng;
  final int availablePorts;
  final int totalPorts;
  final double distanceKm;

  ChargingStationData({
    required this.id,
    required this.name,
    required this.lat,
    required this.lng,
    required this.availablePorts,
    required this.totalPorts,
    required this.distanceKm,
  });

  factory ChargingStationData.fromJson(Map<String, dynamic> json) {
    return ChargingStationData(
      id: json['id'] as String,
      name: json['name'] as String,
      lat: (json['lat'] as num).toDouble(),
      lng: (json['lng'] as num).toDouble(),
      availablePorts: json['available_ports'] as int,
      totalPorts: json['total_ports'] as int,
      distanceKm: (json['distance_km'] as num).toDouble(),
    );
  }
}

class AlertData {
  final String id;
  final String type;
  final String title;
  final String message;
  final String severity;

  AlertData({
    required this.id,
    required this.type,
    required this.title,
    required this.message,
    required this.severity,
  });

  factory AlertData.fromJson(Map<String, dynamic> json) {
    return AlertData(
      id: json['id'] as String,
      type: json['type'] as String,
      title: json['title'] as String,
      message: json['message'] as String,
      severity: json['severity'] as String,
    );
  }
}

class MapContextData {
  final String scenarioId;
  final int seed;
  final String dataMode;
  final String timestamp;
  final DriverLocationData driverLocation;
  final List<DemandZoneData> demandZones;
  final List<ChargingStationData> chargingStations;
  final List<AlertData> alerts;

  MapContextData({
    required this.scenarioId,
    required this.seed,
    required this.dataMode,
    required this.timestamp,
    required this.driverLocation,
    required this.demandZones,
    required this.chargingStations,
    required this.alerts,
  });

  factory MapContextData.fromJson(Map<String, dynamic> json) {
    return MapContextData(
      scenarioId: json['scenario_id'] as String,
      seed: json['seed'] as int,
      dataMode: json['data_mode'] as String? ?? 'synthetic',
      timestamp: json['timestamp'] as String,
      driverLocation: DriverLocationData.fromJson(json['driver_location']),
      demandZones: (json['demand_zones'] as List)
          .map((e) => DemandZoneData.fromJson(e))
          .toList(),
      chargingStations: (json['charging_stations'] as List)
          .map((e) => ChargingStationData.fromJson(e))
          .toList(),
      alerts: (json['alerts'] as List)
          .map((e) => AlertData.fromJson(e))
          .toList(),
    );
  }
}
