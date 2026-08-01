import React, { useState } from 'react';

export const VoiceSettings = () => {
    const [sttProvider, setSttProvider] = useState('local');
    const [ttsProvider, setTtsProvider] = useState('local');
    const [speechSpeed, setSpeechSpeed] = useState(1.0);

    return (
        <div className="voice-settings p-4 bg-gray-50 rounded-lg">
            <h2 className="text-lg font-bold mb-4">Voice & Multimodal Settings</h2>
            
            <div className="space-y-4">
                <div>
                    <label className="block text-sm font-medium">STT Provider</label>
                    <select value={sttProvider} onChange={e => setSttProvider(e.target.value)} className="mt-1 p-2 border rounded">
                        <option value="local">Local (Whisper)</option>
                        <option value="remote">Remote API</option>
                    </select>
                </div>

                <div>
                    <label className="block text-sm font-medium">TTS Provider</label>
                    <select value={ttsProvider} onChange={e => setTtsProvider(e.target.value)} className="mt-1 p-2 border rounded">
                        <option value="local">Local (System Voice)</option>
                        <option value="remote">Remote API</option>
                    </select>
                </div>

                <div>
                    <label className="block text-sm font-medium">Speech Speed ({speechSpeed}x)</label>
                    <input 
                        type="range" 
                        min="0.5" max="2.0" step="0.1" 
                        value={speechSpeed} 
                        onChange={e => setSpeechSpeed(parseFloat(e.target.value))}
                        className="mt-1 w-full"
                    />
                </div>
            </div>
        </div>
    );
};
