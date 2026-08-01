import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Copy, Check, Code, Terminal } from 'lucide-react';

interface CodeBlockProps {
  language?: string;
  value: string;
}

const CodeBlock: React.FC<CodeBlockProps> = ({ language, value }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const lines = value.split('\n');

  return (
    <div className="my-3 rounded-xl border border-slate-700/80 bg-slate-950 overflow-hidden shadow-lg font-mono text-xs">
      {/* Code Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-slate-900 border-b border-slate-800 text-slate-400">
        <div className="flex items-center gap-2">
          <Terminal className="w-3.5 h-3.5 text-indigo-400" />
          <span className="font-semibold text-slate-300 uppercase tracking-wider text-[10px]">
            {language || 'code'}
          </span>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors text-[11px]"
          title="Copy code to clipboard"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      {/* Code Body with Line Numbers */}
      <div className="p-4 overflow-x-auto text-slate-200 leading-relaxed font-mono">
        <table className="border-collapse w-full">
          <tbody>
            {lines.map((line, i) => (
              <tr key={i} className="hover:bg-slate-900/40">
                <td className="pr-4 text-slate-600 select-none text-right w-8 text-[11px]">
                  {i + 1}
                </td>
                <td className="whitespace-pre">{line}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

interface MarkdownMessageProps {
  content: string;
}

export const MarkdownMessage: React.FC<MarkdownMessageProps> = ({ content }) => {
  return (
    <div className="markdown-body space-y-2">
      <ReactMarkdown
        components={{
          code({ node, inline, className, children, ...props }: any) {
            const match = /language-(\w+)/.exec(className || '');
            const codeString = String(children).replace(/\n$/, '');

            if (!inline) {
              return (
                <CodeBlock
                  language={match ? match[1] : undefined}
                  value={codeString}
                />
              );
            }

            return (
              <code
                className="bg-slate-900 text-indigo-300 px-1.5 py-0.5 rounded font-mono text-xs border border-slate-800"
                {...props}
              >
                {children}
              </code>
            );
          },
          p({ children }) {
            return <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>;
          },
          ul({ children }) {
            return <ul className="list-disc pl-5 my-2 space-y-1">{children}</ul>;
          },
          ol({ children }) {
            return <ol className="list-decimal pl-5 my-2 space-y-1">{children}</ol>;
          },
          li({ children }) {
            return <li className="leading-relaxed">{children}</li>;
          },
          h1({ children }) {
            return <h1 className="text-lg font-bold text-white my-3 border-b border-slate-800 pb-1">{children}</h1>;
          },
          h2({ children }) {
            return <h2 className="text-base font-bold text-slate-100 my-2">{children}</h2>;
          },
          h3({ children }) {
            return <h3 className="text-sm font-semibold text-slate-200 my-1">{children}</h3>;
          },
          blockquote({ children }) {
            return (
              <blockquote className="border-l-4 border-indigo-500 pl-3 py-1 my-2 text-slate-400 italic bg-slate-900/40 rounded-r">
                {children}
              </blockquote>
            );
          }
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};
