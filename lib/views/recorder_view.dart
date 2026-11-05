import 'dart:io';

import 'package:flutter/material.dart';

import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';

class RecorderView extends StatefulWidget {
  final Function onSaved;

  const RecorderView({Key? key, required this.onSaved}) : super(key: key);
  @override
  _RecorderViewState createState() => _RecorderViewState();
}

enum RecordingState {
  UnSet,
  Set,
  Recording,
  Stopped,
}

class _RecorderViewState extends State<RecorderView> {
  IconData _recordIcon = Icons.mic_none;
  String _recordText = 'Click To Start';
  RecordingState _recordingState = RecordingState.UnSet;

  final record = Record();

  @override
  void initState() {
    super.initState();
    record.hasPermission().then((hasPermission) {
      if (hasPermission && mounted) {
        setState(() {
          _recordingState = RecordingState.Set;
          _recordIcon = Icons.mic;
          _recordText = 'Record';
        });
      }
    });
  }

  @override
  void dispose() {
    _recordingState = RecordingState.UnSet;
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      alignment: Alignment.center,
      children: [
        MaterialButton(
          onPressed: () async {
            await _onRecordButtonPressed();
            setState(() {});
          },
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(50),
          ),
          child: SizedBox(
            width: 150,
            height: 150,
            child: Icon(
              _recordIcon,
              size: 50,
            ),
          ),
        ),
        Align(
            alignment: Alignment.bottomCenter,
            child: Padding(
              padding: const EdgeInsets.all(8),
              child: Text(_recordText),
            ))
      ],
    );
  }

  Future<void> _onRecordButtonPressed() async {
    switch (_recordingState) {
      case RecordingState.Set:
        await _recordVoice();
        break;

      case RecordingState.Recording:
        await _stopRecording();
        _recordingState = RecordingState.Stopped;
        _recordIcon = Icons.fiber_manual_record;
        _recordText = 'Record new one';
        break;

      case RecordingState.Stopped:
        await _recordVoice();
        break;

      case RecordingState.UnSet:
        ScaffoldMessenger.of(context).hideCurrentSnackBar();

        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Please allow recording from settings.'),
        ));
        break;
    }
  }

  _startRecording() async {
    Directory appDirectory = await getApplicationDocumentsDirectory();
    String filePath =
        '${appDirectory.path}/${DateTime.now().millisecondsSinceEpoch}.m4a';

    await record.start(
      path: filePath,
      encoder: AudioEncoder.aacEld, // by default
      bitRate: 128000, // by default
      samplingRate: 44100, // by default
    );
  }

  _stopRecording() async {
    await record.stop();

    widget.onSaved();
  }

  Future<void> _recordVoice() async {
    final hasPermission = await record.hasPermission();
    if (hasPermission) {
      await _startRecording();
      _recordingState = RecordingState.Recording;
      _recordIcon = Icons.stop;
      _recordText = 'Recording';
    } else {
      ScaffoldMessenger.of(context).hideCurrentSnackBar();
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text('Please allow recording from settings.'),
      ));
    }
  }
}
