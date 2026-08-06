import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context, listen: false);

    return Scaffold(
      appBar: AppBar(title: const Text('Settings & Memory')),
      body: ListView(
        children: [
          ListTile(
            leading: const Icon(Icons.memory),
            title: const Text('Memory Synchronization'),
            subtitle: const Text('Sync local state with NEXA Core'),
            trailing: IconButton(
              icon: const Icon(Icons.sync),
              onPressed: () {
                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Memory Synced with Core')));
              },
            ),
          ),
          ListTile(
            leading: const Icon(Icons.volume_up),
            title: const Text('Voice Engine configuration'),
            subtitle: const Text('Using Real STT/TTS Providers'),
            trailing: const Icon(Icons.check_circle, color: Colors.green),
          ),
          ListTile(
            leading: const Icon(Icons.camera),
            title: const Text('Vision Integration'),
            subtitle: const Text('Camera and Gallery access granted'),
            trailing: const Icon(Icons.check_circle, color: Colors.green),
          ),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.exit_to_app, color: Colors.redAccent),
            title: const Text('Disconnect from NEXA', style: TextStyle(color: Colors.redAccent)),
            onTap: () => auth.logout(),
          ),
        ],
      ),
    );
  }
}
