import React, { useState, useEffect } from 'react';
import { Volume2, Square } from 'lucide-react';

export const VoicePlayer: React.FC<{ text: string }> = ({ text }) => {
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    return () => {
      window.speechSynthesis?.cancel();
    };
  }, []);

  const togglePlay = () => {
    if (isPlaying) {
      window.speechSynthesis.cancel();
      setIsPlaying(false);
    } else {
      // Strip markdown syntax roughly for better speech
      const plainText = text.replace(/[#*`_]/g, '');
      const utterance = new SpeechSynthesisUtterance(plainText);
      utterance.onend = () => setIsPlaying(false);
      utterance.onerror = () => setIsPlaying(false);
      setIsPlaying(true);
      window.speechSynthesis.speak(utterance);
    }
  };

  if (typeof window === 'undefined' || !('speechSynthesis' in window)) return null;

  return (
    <button 
      onClick={togglePlay}
      className={`p-1.5 rounded-md transition-colors ${isPlaying ? 'bg-indigo-500/20 text-indigo-400' : 'text-slate-500 hover:text-indigo-400 hover:bg-slate-800'}`}
      title={isPlaying ? "Stop Voice" : "Read Aloud"}
    >
      {isPlaying ? <Square size={14} /> : <Volume2 size={14} />}
    </button>
  );
};
