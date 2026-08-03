import 'package:flutter/material.dart';
import '../models/map_context.dart';
import '../models/driver_state.dart';
import '../models/advice_v2.dart';
import '../services/api_service.dart';
import '../widgets/map_widget.dart';
import '../widgets/alert_card.dart';
import '../widgets/advice_checkpoint_card.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ApiService _apiService = ApiService();
  MapContextData? _mapContext;
  DriverStateData? _driverState;
  AdviceEnvelopeV2? _adviceEnvelope;
  bool _adviceV2Disabled = false;
  bool _isLoading = true;
  bool _isOnline = false;
  int _selectedBottomNavIndex = 0;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    final mapCtx = await _apiService.fetchMapContext();
    final drvState = await _apiService.fetchDriverState();
    AdviceFetchResultV2? adviceResult;
    if (drvState != null) {
      final scenario = drvState.payoutSummary.scenarioId;
      final adviceDate = scenario.contains(':') ? scenario.split(':').last : '';
      if (adviceDate.isNotEmpty) {
        adviceResult = await _apiService.fetchAdviceV2(
          surface: 'nudge',
          driverId: drvState.driverId,
          date: adviceDate,
          nowMin: 14 * 60,
          shiftStartMin: 6 * 60,
          shiftEndMin: 22 * 60,
          isDriving: false,
        );
      }
    }
    setState(() {
      _mapContext = mapCtx;
      _driverState = drvState;
      _adviceEnvelope = adviceResult?.envelope;
      _adviceV2Disabled = adviceResult?.disabled ?? false;
      _isLoading = false;
    });
  }

  void _showAgentDialog() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) {
        return Container(
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
          ),
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: Colors.grey.shade300,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Row(
                children: const [
                  CircleAvatar(
                    backgroundColor: Color(0xFFE0F7FA),
                    child: Icon(Icons.smart_toy, color: Color(0xFF00AFB9)),
                  ),
                  SizedBox(width: 12),
                  Text(
                    'Trợ Lý Xanh',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              if (_adviceEnvelope?.status == 'ready' &&
                  _adviceEnvelope!.items.isNotEmpty)
                AdviceCheckpointCard(
                  card: _adviceEnvelope!.items.first,
                  onMounted: () => _apiService
                      .acknowledgeAdviceDisplay(_adviceEnvelope!.items.first),
                  onResponse: (response) => _apiService
                      .respondToAdvice(_adviceEnvelope!.items.first, response),
                )
              else
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: const Color(0xFFF0FDF4),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: const Color(0xFF00AFB9).withOpacity(0.3)),
                  ),
                  child: Text(
                    'Chưa có AdviceCheckpoint hợp lệ từ backend trong phiên này.\n'
                    'Trợ lý sẽ chỉ hiển thị hành động, thời điểm và số liệu khi có nguồn dữ liệu đã được kiểm chứng.'
                    '${_adviceV2Disabled ? '\nAPI v2 đang tắt — ứng dụng giữ trạng thái an toàn.' : ''}',
                    style: const TextStyle(fontSize: 13.5, height: 1.5,
                        color: Color(0xFF1C1C1E)),
                  ),
                ),
              const SizedBox(height: 20),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () => Navigator.pop(context),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF00AFB9),
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                  ),
                  child: const Text(
                    'Đóng',
                    style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                  ),
                ),
              )
            ],
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final formattedValue = _driverState != null
        ? _driverState!.payoutSummary.value.toStringAsFixed(0).replaceAllMapped(
            RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'),
            (Match m) => '${m[1]}.',
          )
        : '202.000';

    return Scaffold(
      backgroundColor: const Color(0xFFE8F1FA),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF00AFB9)))
          : Stack(
              children: [
                // 1. Map Base Layer
                Positioned.fill(
                  child: _mapContext != null
                      ? MapWidget(mapContext: _mapContext!)
                      : const Center(child: Text('Không thể tải dữ liệu bản đồ')),
                ),

                // 2. Top Header Elements (Menu, Balance Pill, Quota, Battery)
                Positioned(
                  top: 50,
                  left: 16,
                  right: 16,
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      // Menu Button
                      Container(
                        width: 48,
                        height: 48,
                        decoration: const BoxDecoration(
                          color: Colors.white,
                          shape: BoxShape.circle,
                          boxShadow: [
                            BoxShadow(color: Colors.black12, blurRadius: 8, offset: Offset(0, 3)),
                          ],
                        ),
                        child: IconButton(
                          icon: const Icon(Icons.menu, color: Color(0xFF1C1C1E)),
                          onPressed: () {},
                        ),
                      ),

                      // Balance Pill
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(30),
                          boxShadow: const [
                            BoxShadow(color: Colors.black12, blurRadius: 8, offset: Offset(0, 3)),
                          ],
                        ),
                        child: Text(
                          '$formattedValue.000đ',
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: Color(0xFF1C1C1E),
                          ),
                        ),
                      ),

                      // Progress / Quota Circle & Battery Pill
                      Row(
                        children: [
                          Container(
                            width: 48,
                            height: 48,
                            decoration: const BoxDecoration(
                              color: Colors.white,
                              shape: BoxShape.circle,
                              boxShadow: [
                                BoxShadow(color: Colors.black12, blurRadius: 8, offset: Offset(0, 3)),
                              ],
                            ),
                            child: Center(
                              child: Text(
                                '${_driverState?.payoutSummary.tripsCount ?? 0}.0/8',
                                style: const TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.bold,
                                  color: Color(0xFF1C1C1E),
                                ),
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          if (_driverState != null)
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                              decoration: BoxDecoration(
                                color: _driverState!.socPercent < 25
                                    ? Colors.red
                                    : const Color(0xFF00AFB9),
                                borderRadius: BorderRadius.circular(16),
                              ),
                              child: Row(
                                children: [
                                  const Icon(Icons.battery_charging_full, size: 14, color: Colors.white),
                                  const SizedBox(width: 2),
                                  Text(
                                    '${_driverState!.socPercent}%',
                                    style: const TextStyle(
                                      fontSize: 11,
                                      fontWeight: FontWeight.bold,
                                      color: Colors.white,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                        ],
                      ),
                    ],
                  ),
                ),

                // 3. Risk & Weather Alert Cards Banner
                if (_mapContext != null && _mapContext!.alerts.isNotEmpty)
                  Positioned(
                    top: 112,
                    left: 0,
                    right: 0,
                    child: Column(
                      children: _mapContext!.alerts
                          .map((alert) => AlertCardWidget(alert: alert))
                          .toList(),
                    ),
                  ),

                // 4. Right Side Floating Control Stack (Timer Ring & Action Buttons)
                Positioned(
                  top: 240,
                  right: 16,
                  child: Column(
                    children: [
                      // Layer Button
                      _buildFloatingCircleBtn(Icons.layers_outlined, () {}),
                      const SizedBox(height: 12),
                      // Timer Ring Widget
                      Container(
                        width: 52,
                        height: 52,
                        decoration: const BoxDecoration(
                          color: Colors.white,
                          shape: BoxShape.circle,
                          boxShadow: [
                            BoxShadow(color: Colors.black12, blurRadius: 8, offset: Offset(0, 3)),
                          ],
                        ),
                        child: Stack(
                          alignment: Alignment.center,
                          children: [
                            const SizedBox(
                              width: 46,
                              height: 46,
                              child: CircularProgressIndicator(
                                value: 0.7,
                                strokeWidth: 3,
                                valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF00AFB9)),
                                backgroundColor: Color(0xFFE0E0E0),
                              ),
                            ),
                            const Text(
                              '01:04',
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.bold,
                                color: Color(0xFF1C1C1E),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 12),
                      // Calendar Button
                      _buildFloatingCircleBtn(Icons.calendar_today_outlined, () {}),
                      const SizedBox(height: 12),
                      // History Button
                      _buildFloatingCircleBtn(Icons.history, () {}),
                    ],
                  ),
                ),

                // 5. Main CTA Button ("Mở nhận chuyến") & Info Cards
                Positioned(
                  bottom: 110,
                  left: 16,
                  right: 16,
                  child: Column(
                    children: [
                      // Main CTA Dark Pill Button
                      GestureDetector(
                        onTap: () {
                          setState(() {
                            _isOnline = !_isOnline;
                          });
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text(
                                _isOnline
                                    ? '⚡ Đã bật chế độ SẴN SÀNG NHẬN CHUYẾN'
                                    : '⏸️ Đã tạm dừng nhận chuyến',
                              ),
                              backgroundColor: const Color(0xFF00AFB9),
                            ),
                          );
                        },
                        child: Container(
                          width: 260,
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          decoration: BoxDecoration(
                            color: _isOnline ? const Color(0xFF00AFB9) : const Color(0xFF1C1C1E),
                            borderRadius: BorderRadius.circular(32),
                            boxShadow: const [
                              BoxShadow(color: Colors.black26, blurRadius: 12, offset: Offset(0, 4)),
                            ],
                          ),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(
                                _isOnline ? Icons.power_settings_new : Icons.electric_bolt,
                                color: Colors.white,
                                size: 22,
                              ),
                              const SizedBox(width: 8),
                              Text(
                                _isOnline ? 'Đang nhận chuyến' : 'Mở nhận chuyến',
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 16,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 14),

                      // Info Cards Row
                      Row(
                        children: [
                          Expanded(
                            child: Container(
                              padding: const EdgeInsets.all(14),
                              decoration: BoxDecoration(
                                color: Colors.white,
                                borderRadius: BorderRadius.circular(16),
                                boxShadow: const [
                                  BoxShadow(color: Colors.black12, blurRadius: 6, offset: Offset(0, 2)),
                                ],
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: const [
                                      Text(
                                        'Số dư ví',
                                        style: TextStyle(fontSize: 12, color: Colors.grey),
                                      ),
                                      Icon(Icons.chevron_right, size: 16, color: Colors.grey),
                                    ],
                                  ),
                                  const SizedBox(height: 6),
                                  Text(
                                    '$formattedValue.000đ',
                                    style: const TextStyle(
                                      fontSize: 15,
                                      fontWeight: FontWeight.bold,
                                      color: Color(0xFF1C1C1E),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Container(
                              padding: const EdgeInsets.all(14),
                              decoration: BoxDecoration(
                                color: Colors.white,
                                borderRadius: BorderRadius.circular(16),
                                boxShadow: const [
                                  BoxShadow(color: Colors.black12, blurRadius: 6, offset: Offset(0, 2)),
                                ],
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: const [
                                      Text(
                                        'Thông báo',
                                        style: TextStyle(fontSize: 12, color: Colors.grey),
                                      ),
                                      Icon(Icons.chevron_right, size: 16, color: Colors.grey),
                                    ],
                                  ),
                                  const SizedBox(height: 6),
                                  const Text(
                                    '1 tin mới từ GSM',
                                    style: TextStyle(
                                      fontSize: 13,
                                      fontWeight: FontWeight.w600,
                                      color: Color(0xFF00AFB9),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),

                // 6. Floating Xanh AI Assistant Bot (Bottom Right)
                Positioned(
                  bottom: 120,
                  right: 12,
                  child: GestureDetector(
                    onTap: _showAgentDialog,
                    child: Container(
                      width: 58,
                      height: 58,
                      decoration: BoxDecoration(
                        color: const Color(0xFF00AFB9),
                        shape: BoxShape.circle,
                        boxShadow: const [
                          BoxShadow(color: Colors.black26, blurRadius: 10, offset: Offset(0, 4)),
                        ],
                        border: Border.all(color: Colors.white, width: 2),
                      ),
                      child: const Icon(
                        Icons.smart_toy,
                        color: Colors.white,
                        size: 30,
                      ),
                    ),
                  ),
                ),

                // 7. Bottom Navigation Bar (5 GSM Tabs)
                Positioned(
                  bottom: 0,
                  left: 0,
                  right: 0,
                  child: Container(
                    padding: const EdgeInsets.only(top: 10, bottom: 20, left: 8, right: 8),
                    decoration: const BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
                      boxShadow: [
                        BoxShadow(color: Colors.black12, blurRadius: 10, offset: Offset(0, -3)),
                      ],
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceAround,
                      children: [
                        _buildNavItem(0, Icons.flash_on, 'Xanh Now'),
                        _buildNavItem(1, Icons.location_on, 'Chọn điểm\nđến'),
                        _buildNavItem(2, Icons.assignment, 'Chuyến\ncủa tôi'),
                        _buildNavItem(3, Icons.directions_car, 'Mua xe\nVinFast'),
                        _buildNavItem(4, Icons.settings, 'Cài đặt'),
                      ],
                    ),
                  ),
                ),
              ],
            ),
    );
  }

  Widget _buildFloatingCircleBtn(IconData icon, VoidCallback onPressed) {
    return Container(
      width: 46,
      height: 46,
      decoration: const BoxDecoration(
        color: Colors.white,
        shape: BoxShape.circle,
        boxShadow: [
          BoxShadow(color: Colors.black12, blurRadius: 8, offset: Offset(0, 3)),
        ],
      ),
      child: IconButton(
        icon: Icon(icon, color: const Color(0xFF1C1C1E), size: 20),
        onPressed: onPressed,
      ),
    );
  }

  Widget _buildNavItem(int index, IconData icon, String label) {
    final isSelected = _selectedBottomNavIndex == index;
    final color = isSelected ? const Color(0xFF00AFB9) : Colors.grey.shade600;

    return GestureDetector(
      onTap: () {
        setState(() {
          _selectedBottomNavIndex = index;
        });
      },
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color, size: 24),
          const SizedBox(height: 4),
          Text(
            label,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 10,
              fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
              color: color,
              height: 1.1,
            ),
          ),
        ],
      ),
    );
  }
}
