import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import '../models/map_context.dart';

class MapWidget extends StatefulWidget {
  final MapContextData mapContext;

  const MapWidget({Key? key, required this.mapContext}) : super(key: key);

  @override
  State<MapWidget> createState() => _MapWidgetState();
}

class _MapWidgetState extends State<MapWidget> {
  GoogleMapController? _controller;

  // Hanoi Bounding Box Geo-fence limits
  static final LatLngBounds _hanoiBounds = LatLngBounds(
    southwest: const LatLng(20.8000, 105.6000), // Ranh giới Nam - Tây Hà Nội
    northeast: const LatLng(21.2500, 106.0500), // Ranh giới Bắc - Đông Hà Nội
  );

  @override
  Widget build(BuildContext context) {
    final driverLoc = widget.mapContext.driverLocation;
    final initialPos = CameraPosition(
      target: LatLng(driverLoc.lat, driverLoc.lng),
      zoom: 14.5,
    );

    // Build Markers
    final Set<Marker> markers = {
      Marker(
        markerId: const MarkerId('driver_position'),
        position: LatLng(driverLoc.lat, driverLoc.lng),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueCyan),
        infoWindow: InfoWindow(
          title: 'Tài xế GSM (Hà Nội)',
          snippet: 'Vận tốc: ${driverLoc.speedKmh} km/h',
        ),
      ),
      ...widget.mapContext.chargingStations.map((stn) {
        return Marker(
          markerId: MarkerId(stn.id),
          position: LatLng(stn.lat, stn.lng),
          icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueGreen),
          infoWindow: InfoWindow(
            title: stn.name,
            snippet: 'Cổng sạc: ${stn.availablePorts}/${stn.totalPorts} (${stn.distanceKm} km)',
          ),
        );
      }),
    };

    // Build Circles for H3 Demand Zones
    final Set<Circle> circles = widget.mapContext.demandZones.map((zone) {
      return Circle(
        circleId: CircleId(zone.h3Index),
        center: LatLng(zone.lat, zone.lng),
        radius: zone.intensity * 350,
        fillColor: Colors.red.withOpacity(0.35),
        strokeColor: Colors.deepOrange,
        strokeWidth: 2,
      );
    }).toSet();

    return GoogleMap(
      initialCameraPosition: initialPos,
      cameraTargetBounds: CameraTargetBounds(_hanoiBounds), // Khóa phạm vi chỉ di chuyển trong Hà Nội
      minMaxZoomPreference: const MinMaxZoomPreference(11.0, 18.0), // Khóa Zoom tối thiểu không cho thu nhỏ ngoài Hà Nội
      markers: markers,
      circles: circles,
      myLocationEnabled: false,
      zoomControlsEnabled: false,
      mapToolbarEnabled: false,
      onMapCreated: (controller) {
        _controller = controller;
      },
    );
  }
}
