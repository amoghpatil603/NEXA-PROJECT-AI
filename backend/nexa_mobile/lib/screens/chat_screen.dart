import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:image_picker/image_picker.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:flutter_tts/flutter_tts.dart';
import '../providers/chat_provider.dart';
import '../providers/auth_provider.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final ImagePicker _picker = ImagePicker();
  
  late stt.SpeechToText _speech;
  bool _isListening = false;
  
  late FlutterTts _flutterTts;
  bool _isPlaying = false;
  
  @override
  void initState() {
    super.initState();
    _speech = stt.SpeechToText();
    _flutterTts = FlutterTts();
    _initTts();
  }
  
  Future<void> _initTts() async {
    await _flutterTts.setLanguage("en-US");
    await _flutterTts.setSpeechRate(0.5);
    await _flutterTts.setVolume(1.0);
    await _flutterTts.setPitch(1.0);
    
    _flutterTts.setCompletionHandler(() {
      setState(() => _isPlaying = false);
    });
  }

  void _handleSend() {
    if (_controller.text.trim().isEmpty) return;
    
    final chat = Provider.of<ChatProvider>(context, listen: false);
    final auth = Provider.of<AuthProvider>(context, listen: false);
    chat.sendMessage(_controller.text, auth.token);
    
    _controller.clear();
    _scrollToBottom();
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _pickImage(ImageSource source) async {
    final XFile? image = await _picker.pickImage(source: source);
    if (image != null) {
      // Logic for Vision OCR pipeline integration here
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Vision Upload: \${image.name}')));
      // Real OCR transmission to backend would occur here
    }
  }

  void _listen() async {
    if (!_isListening) {
      bool available = await _speech.initialize(
        onStatus: (val) => print('onStatus: \$val'),
        onError: (val) => print('onError: \$val'),
      );
      if (available) {
        setState(() => _isListening = true);
        _speech.listen(
          onResult: (val) => setState(() {
            _controller.text = val.recognizedWords;
          }),
        );
      }
    } else {
      setState(() => _isListening = false);
      _speech.stop();
    }
  }

  Future<void> _speak(String text) async {
    if (_isPlaying) {
      await _flutterTts.stop();
      setState(() => _isPlaying = false);
    } else {
      setState(() => _isPlaying = true);
      // Clean markdown syntax roughly
      String cleanText = text.replaceAll(RegExp(r'[*#_`]'), '');
      await _flutterTts.speak(cleanText);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('NEXA Core Intelligence'),
        actions: [
          IconButton(
            icon: Icon(_isPlaying ? Icons.volume_off : Icons.volume_up),
            onPressed: () {
              if (_isPlaying) {
                _flutterTts.stop();
                setState(() => _isPlaying = false);
              }
            },
          )
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: Consumer<ChatProvider>(
              builder: (context, chat, child) {
                return ListView.builder(
                  controller: _scrollController,
                  padding: const EdgeInsets.all(16),
                  itemCount: chat.messages.length,
                  itemBuilder: (context, index) {
                    final msg = chat.messages[index];
                    final isUser = msg.role == 'user';
                    return Align(
                      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
                      child: Container(
                        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.8),
                        margin: const EdgeInsets.only(bottom: 12),
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: isUser ? Colors.indigoAccent : const Color(0xFF1E293B),
                          borderRadius: BorderRadius.circular(16),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            MarkdownBody(
                              data: msg.text,
                              styleSheet: MarkdownStyleSheet(
                                p: TextStyle(color: isUser ? Colors.white : Colors.white70),
                              ),
                            ),
                            if (!isUser)
                              Padding(
                                padding: const EdgeInsets.only(top: 8.0),
                                child: InkWell(
                                  onTap: () => _speak(msg.text),
                                  child: Icon(
                                    Icons.play_circle_outline,
                                    size: 20,
                                    color: Colors.grey[400],
                                  ),
                                ),
                              )
                          ],
                        ),
                      ),
                    );
                  },
                );
              },
            ),
          ),
          Consumer<ChatProvider>(
            builder: (context, chat, child) {
              if (chat.isLoading) {
                return const Padding(
                  padding: EdgeInsets.all(8.0),
                  child: LinearProgressIndicator(),
                );
              }
              return const SizedBox.shrink();
            },
          ),
          Container(
            padding: const EdgeInsets.all(8.0),
            color: const Color(0xFF0F172A),
            child: Row(
              children: [
                IconButton(
                  icon: const Icon(Icons.camera_alt, color: Colors.grey),
                  onPressed: () => _pickImage(ImageSource.camera),
                ),
                IconButton(
                  icon: const Icon(Icons.photo, color: Colors.grey),
                  onPressed: () => _pickImage(ImageSource.gallery),
                ),
                IconButton(
                  icon: Icon(_isListening ? Icons.mic : Icons.mic_none, color: _isListening ? Colors.red : Colors.grey),
                  onPressed: _listen,
                ),
                Expanded(
                  child: TextField(
                    controller: _controller,
                    decoration: InputDecoration(
                      hintText: 'Message NEXA...',
                      filled: true,
                      fillColor: const Color(0xFF1E293B),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(24),
                        borderSide: BorderSide.none,
                      ),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    ),
                    onSubmitted: (_) => _handleSend(),
                  ),
                ),
                const SizedBox(width: 8),
                CircleAvatar(
                  backgroundColor: Colors.indigoAccent,
                  child: IconButton(
                    icon: const Icon(Icons.send, color: Colors.white),
                    onPressed: _handleSend,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
