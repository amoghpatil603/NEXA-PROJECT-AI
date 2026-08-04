import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Settings2, Activity, Play, Square, Loader2 } from 'lucide-react';

export const VoiceManager: React.FC = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [interimResult, setInterimResult] = useState('');
  const [transcripts, setTranscripts] = useState<string[]>([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speechSpeed, setSpeechSpeed] = useState(1.0);
  const [ttsProvider, setTtsProvider] = useState('local_webkit');
  const [sttProvider, setSttProvider] = useState('local_webkit');
  
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    if (typeof window !== 'undefined' && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;
      
      recognitionRef.current.onresult = (event: any) => {
        let finalTranscript = '';
        let interim = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          } else {
            interim += event.results[i][0].transcript;
          }
        }
        setInterimResult(interim);
        if (finalTranscript) {
          setTranscripts(prev => [...prev, finalTranscript.trim()]);
        }
      };

      recognitionRef.current.onerror = (event: any) => {
        console.error('Speech recognition error', event.error);
        setIsRecording(false);
      };

      recognitionRef.current.onend = () => {
        setIsRecording(false);
        setInterimResult('');
      };
    }
    
    return () => {
        window.speechSynthesis?.cancel();
    }
  }, []);

  const toggleRecording = () => {
    if (isRecording) {
      recognitionRef.current?.stop();
      setIsRecording(false);
    } else {
      setInterimResult('');
      recognitionRef.current?.start();
      setIsRecording(true);
    }
  };

  const testTTS = () => {
    if (isPlaying) {
      window.speechSynthesis.cancel();
      setIsPlaying(false);
    } else {
      const utterance = new SpeechSynthesisUtterance("Hello, I am the NEXA Voice Engine. All systems are operating normally.");
      utterance.rate = speechSpeed;
      utterance.onend = () => setIsPlaying(false);
      utterance.onerror = () => setIsPlaying(false);
      setIsPlaying(true);
      window.speechSynthesis.speak(utterance);
    }
  };

  return (
    <div className="p-8 h-full bg-slate-950 text-white overflow-y-auto">
      <h2 className="text-xl font-bold flex items-center gap-2 mb-4"><Mic /> Voice Manager</h2>
      <p className="text-slate-400 mb-6">Configure STT/TTS engine parameters and monitor active streaming state.</p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Voice Configuration */}
        <div className="p-4 border border-slate-800 rounded-lg bg-slate-900">
          <h3 className="text-lg font-semibold flex items-center gap-2 mb-4">
            <Settings2 size={18} />
            Voice Configuration
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">STT Provider (Speech-to-Text)</label>
              <select value={sttProvider} onChange={e => setSttProvider(e.target.value)} className="w-full bg-slate-950 border border-slate-700 rounded-md p-2 text-sm">
                <option value="local_webkit">Local WebSpeech API (Streaming)</option>
                <option value="remote_whisper">Remote Whisper API</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">TTS Provider (Text-to-Speech)</label>
              <select value={ttsProvider} onChange={e => setTtsProvider(e.target.value)} className="w-full bg-slate-950 border border-slate-700 rounded-md p-2 text-sm">
                <option value="local_webkit">Local Synthesis (Streaming)</option>
                <option value="remote_elevenlabs">Remote ElevenLabs API</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Playback Speed ({speechSpeed.toFixed(1)}x)</label>
              <input 
                type="range" 
                min="0.5" max="2.0" step="0.1" 
                value={speechSpeed} 
                onChange={e => setSpeechSpeed(parseFloat(e.target.value))}
                className="w-full accent-indigo-500"
              />
            </div>
            <div className="pt-2 border-t border-slate-800 flex justify-between items-center">
              <span className="text-xs text-slate-400">Test TTS Engine:</span>
              <button 
                onClick={testTTS}
                className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 rounded text-xs font-medium flex items-center gap-1"
              >
                {isPlaying ? <><Square size={14} /> Stop</> : <><Play size={14} /> Play Test</>}
              </button>
            </div>
          </div>
        </div>

        {/* Live Streaming State */}
        <div className="p-4 border border-slate-800 rounded-lg bg-slate-900 flex flex-col">
          <h3 className="text-lg font-semibold flex items-center gap-2 mb-4">
            <Activity size={18} />
            Live Streaming State
          </h3>
          
          <div className="flex items-center justify-between mb-4 bg-slate-950 p-3 rounded border border-slate-800">
            <div className="flex items-center gap-2">
              <div className={`w-2.5 h-2.5 rounded-full ${isRecording ? 'bg-rose-500 animate-pulse' : 'bg-slate-600'}`}></div>
              <span className="text-sm font-medium">{isRecording ? 'Active Microphone (Streaming)' : 'Microphone Idle'}</span>
            </div>
            <button 
              onClick={toggleRecording}
              className={`p-2 rounded-full transition-colors ${isRecording ? 'bg-rose-500/20 text-rose-400 hover:bg-rose-500/30' : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-indigo-400'}`}
              title={isRecording ? "Stop Recording" : "Start Recording"}
            >
              {isRecording ? <MicOff size={16} /> : <Mic size={16} />}
            </button>
          </div>

          <div className="flex-1 min-h-[150px] bg-slate-950 border border-slate-800 rounded p-3 text-xs font-mono text-slate-300 overflow-y-auto flex flex-col gap-2">
            {transcripts.length === 0 && !interimResult && (
              <span className="text-slate-500 italic">No active transcription stream...</span>
            )}
            {transcripts.map((t, i) => (
              <div key={i} className="text-emerald-400">
                <span className="text-slate-600 mr-2">[{new Date().toLocaleTimeString()}]</span>
                {t}
              </div>
            ))}
            {interimResult && (
              <div className="text-slate-400 flex items-start gap-2">
                <Loader2 size={12} className="animate-spin mt-0.5 shrink-0" />
                {interimResult}
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
};
