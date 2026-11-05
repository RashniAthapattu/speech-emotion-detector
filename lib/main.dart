import 'package:flutter/material.dart';
import 'package:emotion_detector/views/recorder_home_view.dart';
import 'package:loader_overlay/loader_overlay.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Emotion detector',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      home: const LoaderOverlay(
        child: RecorderHomeView(
          title: 'Emotion detector',
        ),
      ),
    );
  }
}
