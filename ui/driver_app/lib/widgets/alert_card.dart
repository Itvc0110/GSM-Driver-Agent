import 'package:flutter/material.dart';
import '../models/map_context.dart';

class AlertCardWidget extends StatelessWidget {
  final AlertData alert;

  const AlertCardWidget({Key? key, required this.alert}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final isCritical = alert.severity == 'critical';
    final bgColor = isCritical ? const Color(0xFFFFF0F2) : const Color(0xFFF0FDF4);
    final accentColor = isCritical ? const Color(0xFFE53935) : const Color(0xFF00AFB9);
    final iconData = isCritical ? Icons.battery_alert : Icons.cloud_queue;

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: accentColor.withOpacity(0.3), width: 1.5),
        boxShadow: const [
          BoxShadow(
            color: Colors.black12,
            blurRadius: 8,
            offset: Offset(0, 3),
          )
        ],
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: bgColor,
              shape: BoxShape.circle,
            ),
            child: Icon(iconData, color: accentColor, size: 22),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  alert.title,
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 13,
                    color: isCritical ? Colors.red.shade900 : const Color(0xFF1C1C1E),
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  alert.message,
                  style: TextStyle(
                    fontSize: 11.5,
                    color: Colors.grey.shade700,
                  ),
                ),
              ],
            ),
          )
        ],
      ),
    );
  }
}
