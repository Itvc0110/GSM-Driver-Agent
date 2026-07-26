class PayoutSummaryData {
  final double value;
  final String currency;
  final int tripsCount;
  final String scenarioId;
  final int seed;
  final String dataMode;
  final bool isMock;

  PayoutSummaryData({
    required this.value,
    required this.currency,
    required this.tripsCount,
    required this.scenarioId,
    required this.seed,
    required this.dataMode,
    required this.isMock,
  });

  factory PayoutSummaryData.fromJson(Map<String, dynamic> json) {
    return PayoutSummaryData(
      value: (json['value'] as num).toDouble(),
      currency: json['currency'] as String? ?? 'VND',
      tripsCount: json['trips_count'] as int,
      scenarioId: json['scenario_id'] as String,
      seed: json['seed'] as int,
      dataMode: json['data_mode'] as String? ?? 'synthetic',
      isMock: json['is_mock'] as bool? ?? true,
    );
  }
}

class DriverStateData {
  final String driverId;
  final String driverName;
  final String shiftStatus;
  final int socPercent;
  final double vehicleRangeKm;
  final PayoutSummaryData payoutSummary;

  DriverStateData({
    required this.driverId,
    required this.driverName,
    required this.shiftStatus,
    required this.socPercent,
    required this.vehicleRangeKm,
    required this.payoutSummary,
  });

  factory DriverStateData.fromJson(Map<String, dynamic> json) {
    return DriverStateData(
      driverId: json['driver_id'] as String,
      driverName: json['driver_name'] as String,
      shiftStatus: json['shift_status'] as String,
      socPercent: json['soc_percent'] as int,
      vehicleRangeKm: (json['vehicle_range_km'] as num).toDouble(),
      payoutSummary: PayoutSummaryData.fromJson(json['payout_summary']),
    );
  }
}
