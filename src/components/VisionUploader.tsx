import React, { useState, useRef } from 'react';
import { Paperclip, FileImage, FileText, X, Check, AlertCircle, Loader2 } from 'lucide-react';
import { useNexaStore } from '../store';

export const VisionUploader: React.FC<{ onExtracted: (text: string) => void }> = ({ onExtracted }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<'idle' | 'uploading' | 'processing' | 'success' | 'error'>('idle');
  const [errorMsg, setErrorMsg] = useState('');
  const [extractedText, setExtractedText] = useState('');
  const [previewUrl, setPreviewUrl] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { addUploadedImage, setVisionAnalysis, setIsAnalyzing } = useNexaStore();

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      setFile(selected);
      setStatus('idle');
      setExtractedText('');
      
      if (selected.type.startsWith('image/')) {
        const url = URL.createObjectURL(selected);
        setPreviewUrl(url);
        addUploadedImage({
          id: `img-${Date.now()}`,
          url,
          name: selected.name,
          timestamp: new Date().toLocaleTimeString()
        });
      } else {
        setPreviewUrl('');
      }
      setIsOpen(true);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setStatus('uploading');
    setIsAnalyzing(true);
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });
      
      const data = await res.json();
      
      if (res.ok) {
        setStatus('success');
        const extracted = data.extracted_text || 'No text could be extracted.';
        setExtractedText(extracted);
        setVisionAnalysis(extracted);
      } else {
        setStatus('error');
        setErrorMsg(data.error || 'Failed to process file.');
      }
    } catch (err) {
      setStatus('error');
      setErrorMsg(String(err));
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleInsert = () => {
    if (extractedText) {
      onExtracted(extractedText);
      setIsOpen(false);
      setFile(null);
      setExtractedText('');
    }
  };

  return (
    <div className="relative inline-block">
      <input 
        type="file" 
        className="hidden" 
        ref={fileInputRef} 
        onChange={handleFileSelect} 
        accept="image/*,.pdf" 
      />
      <button 
        type="button"
        onClick={() => fileInputRef.current?.click()}
        className="p-2 text-slate-400 hover:text-indigo-400 hover:bg-slate-800/60 rounded-xl transition-colors"
        title="Upload Image or PDF for OCR"
      >
        <Paperclip size={18} />
      </button>

      {isOpen && (
        <div className="absolute bottom-12 left-0 w-80 sm:w-96 bg-slate-900 border border-slate-700 shadow-2xl rounded-2xl p-4 z-50">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              {file?.type.startsWith('image/') ? <FileImage size={16} className="text-indigo-400"/> : <FileText size={16} className="text-indigo-400"/>}
              Vision & OCR
            </h3>
            <button onClick={() => setIsOpen(false)} className="text-slate-400 hover:text-white">
              <X size={16} />
            </button>
          </div>
          
          <div className="mb-3">
            <p className="text-xs text-slate-400 truncate">Selected: {file?.name}</p>
            {previewUrl && (
              <div className="mt-2 w-full h-32 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-center overflow-hidden">
                <img src={previewUrl} alt="Preview" className="max-h-full max-w-full object-contain" />
              </div>
            )}
          </div>

          {status === 'idle' && (
            <button 
              onClick={handleUpload}
              className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium"
            >
              Process File
            </button>
          )}

          {(status === 'uploading' || status === 'processing') && (
            <div className="flex flex-col items-center justify-center py-4 text-indigo-400 gap-2">
              <Loader2 className="animate-spin" size={24} />
              <span className="text-xs">Extracting text...</span>
            </div>
          )}

          {status === 'success' && (
            <div className="space-y-3">
              <div className="flex items-center gap-1 text-emerald-400 text-xs font-medium">
                <Check size={14} /> Extraction successful
              </div>
              <div className="w-full h-24 bg-slate-950 border border-slate-800 rounded-lg p-2 text-[10px] text-slate-300 overflow-y-auto font-mono whitespace-pre-wrap">
                {extractedText}
              </div>
              <button 
                onClick={handleInsert}
                className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-medium"
              >
                Insert Text into Chat
              </button>
            </div>
          )}

          {status === 'error' && (
            <div className="space-y-2">
              <div className="flex items-center gap-1 text-rose-400 text-xs font-medium">
                <AlertCircle size={14} /> Error
              </div>
              <p className="text-xs text-slate-400">{errorMsg}</p>
              <button 
                onClick={() => setStatus('idle')}
                className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-medium"
              >
                Retry
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
