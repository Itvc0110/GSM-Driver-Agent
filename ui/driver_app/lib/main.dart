import 'package:flutter/material.dart';
import 'screens/home_screen.dart';

void main() {
  runApp(const GsmDriverApp());
}

class GsmDriverApp extends StatelessWidget {
  const GsmDriverApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'GSM Driver App',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        primaryColor: const Color(0xFF00AFB9),
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF00AFB9),
          primary: const Color(0xFF00AFB9),
          secondary: const Color(0xFF1C1C1E),
        ),
        scaffoldBackgroundColor: const Color(0xFFE8F1FA),
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }
}
