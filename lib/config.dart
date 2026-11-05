/// Address of the emotion detection server.
///
/// Change it when you run the app, for example:
///   flutter run --dart-define=API_URL=http://192.168.1.20:5000
///
/// The default, 10.0.2.2, is how the Android emulator reaches the computer it runs on.
const String apiBaseUrl =
    String.fromEnvironment('API_URL', defaultValue: 'http://10.0.2.2:5000');
