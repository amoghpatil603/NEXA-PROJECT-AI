import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Loader2 } from 'lucide-react';
import { wsClient } from '../utils/websocketClient';
import { useNexaStore } from '../store';

export const VoiceRecorder: React.FC<{ onTranscript: (text: string) => void }> = ({ onTranscript }) => {
  const { isRecording, setIsRecording, interimTranscript: interimResult, setInterimTranscript: setInterimResult, wsStatus } = useNexaStore();
  const [isSupported, setIsSupported] = useState(false);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    if (typeof window !== 'undefined' && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      setIsSupported(true);
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
          const trimmed = finalTranscript.trim();
          if (wsStatus === 'connected') {
            const reqId = `vreq-${Date.now()}`;
            wsClient.sendVoiceStream({ request_id: reqId, text: trimmed }, (res) => {
              console.log('[NEXA WS Voice Stream Response]', res);
            });
          }
          onTranscript(trimmed);
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
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, [setIsRecording, setInterimResult]);

  const toggleRecording = async () => {
    if (isRecording) {
      recognitionRef.current?.stop();
      setIsRecording(false);
    } else {
      try {
        await navigator.mediaDevices.getUserMedia({ audio: true });
      } catch (err) {
        console.error('Microphone permission denied', err);
        return;
      }
      setInterimResult('');
      try {
        recognitionRef.current?.start();
        setIsRecording(true);
      } catch (e) {
        console.error('Speech recognition error', e);
      }
    }
  };

  if (!recognitionRef.current) {
    return (
      <button disabled className="p-2 text-slate-600 rounded-xl" title="Voice Not Supported">
        <MicOff size={18} />
      </button>
    );
  }

  return (
    <div className="relative flex items-center">
      <button 
        type="button"
        onClick={toggleRecording}
        className={`p-2 rounded-xl transition-colors ${isRecording ? 'text-rose-400 bg-rose-400/10 animate-pulse' : 'text-slate-400 hover:text-indigo-400 hover:bg-slate-800/60'}`}
        title={isRecording ? "Stop Recording" : "Start Voice Dictation"}
      >
        {isRecording ? <Mic size={18} className="animate-pulse" /> : <Mic size={18} />}
      </button>
      {isRecording && interimResult && (
        <div className="absolute bottom-full mb-2 left-0 w-64 p-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-300 shadow-xl z-50">
          <div className="flex items-center gap-2 mb-1 text-[10px] text-rose-400 font-bold uppercase tracking-wider">
            <Loader2 size={10} className="animate-spin" /> Listening...
          </div>
          {interimResult}
        </div>
      )}
    </div>
  );
};
