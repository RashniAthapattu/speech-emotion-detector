import 'dart:io';
import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';
import 'package:emotion_detector/views/recorded_list_view.dart';
import 'package:emotion_detector/views/recorder_view.dart';

class RecorderHomeView extends StatefulWidget {
  final String _title;

  const RecorderHomeView({Key? key, required String title})
      : _title = title,
        super(key: key);

  @override
  _RecorderHomeViewState createState() => _RecorderHomeViewState();
}

class _RecorderHomeViewState extends State<RecorderHomeView> {
  List<String> records = [];

  @override
  void initState() {
    super.initState();
    _loadRecords();
  }

  /// Lists the saved recordings, newest first.
  Future<void> _loadRecords() async {
    final Directory dir = await getApplicationDocumentsDirectory();
    final List<String> found = dir
        .listSync()
        .map((entity) => entity.path)
        .where((path) => path.endsWith('.m4a'))
        .toList()
      ..sort();
    if (!mounted) return;
    setState(() => records = found.reversed.toList());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget._title),
      ),
      body: Column(
        children: [
          Expanded(
            flex: 2,
            child: RecordListView(
              records: records,
            ),
          ),
          Expanded(
            flex: 1,
            child: RecorderView(
              onSaved: _onRecordComplete,
            ),
          ),
        ],
      ),
    );
  }

  void _onRecordComplete() {
    _loadRecords();
  }
}
