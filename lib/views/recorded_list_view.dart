import 'dart:convert';
import 'dart:io';

import 'package:emotion_detector/config.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:loader_overlay/loader_overlay.dart';

class RecordListView extends StatefulWidget {
  final List<String> records;
  const RecordListView({
    Key? key,
    required this.records,
  }) : super(key: key);

  @override
  _RecordListViewState createState() => _RecordListViewState();
}

class _RecordListViewState extends State<RecordListView> {
  String returnedEmotion = "";

  @override
  Widget build(BuildContext context) {
    // Show only the most recent recording
    if (widget.records.isEmpty) {
      return const Center(child: Text('No records yet'));
    }
    final String mostRecentRecord = widget.records.first;

    return ListView(
      shrinkWrap: true,
      children: [
        ExpansionTile(
          title: const Text('New recording'),
          subtitle: Text(_getDateFromFilePath(filePath: mostRecentRecord)),
          initiallyExpanded: true,
          children: [
            Container(
              height: 100,
              padding: const EdgeInsets.all(10),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  ElevatedButton(
                    child: const Text('Check Emotion'),
                    onPressed: () => _checkEmotion(filePath: mostRecentRecord),
                  ),
                  const SizedBox(height: 10),
                  Text(
                    'Emotion: $returnedEmotion',
                    style: const TextStyle(
                        fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                ],
              ),
            ),
          ],
        ),
      ],
    );
  }

  /// Sends the recording to the server and shows the emotion it returns.
  /// If anything goes wrong, a message is shown and the loading overlay is closed.
  Future<void> _checkEmotion({required String filePath}) async {
    context.loaderOverlay.show();
    try {
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('$apiBaseUrl/detect_emotion'),
      );
      request.files.add(await http.MultipartFile.fromPath(
        'audio',
        filePath,
        filename: 'recording.m4a',
      ));

      final response = await request.send().timeout(const Duration(seconds: 60));
      final body = await response.stream.bytesToString();
      if (response.statusCode != 200) {
        throw HttpException('Server replied with status ${response.statusCode}');
      }

      final emotion = jsonDecode(body)['emotion'] as String;
      if (!mounted) return;
      setState(() => returnedEmotion = emotion);
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).hideCurrentSnackBar();
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text(
            'Could not detect the emotion. Check that the server is running and the address is correct.'),
      ));
    } finally {
      if (mounted) context.loaderOverlay.hide();
    }
  }

  String _getDateFromFilePath({required String filePath}) {
    final String fromEpoch = filePath.substring(
        filePath.lastIndexOf('/') + 1, filePath.lastIndexOf('.'));

    final DateTime recordedDate =
        DateTime.fromMillisecondsSinceEpoch(int.parse(fromEpoch));
    return '${recordedDate.year}-${recordedDate.month}-${recordedDate.day}';
  }
}
