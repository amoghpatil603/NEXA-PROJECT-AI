import * as fs from 'fs';

let content = fs.readFileSync('server.ts', 'utf8');

const target1 = `            } else {
              // Fallback response over WebSocket
              const fallbackReply = \`NEXA Real-Time Response: Processed request '\${message}' via WebSocket.\`;
              ws.send(JSON.stringify({
                type: "chat_chunk",
                request_id,
                chunk: fallbackReply,
                full: fallbackReply,
                done: true
              }));
              ws.send(JSON.stringify({
                type: "chat_done",
                request_id,
                full: fallbackReply,
                time_taken: 0.12,
                tokens_per_sec: 78.5
              }));
            }`;

const replacement1 = `            } else {
              const errReply = \`Error: Failed to process request on backend API (Status \${response.status})\`;
              ws.send(JSON.stringify({
                type: "chat_error",
                request_id,
                error: errReply
              }));
            }`;

const target2 = `          } catch (err: any) {
            const fallbackReply = \`NEXA WebSocket Service: Handled query '\${message}'. Real-Time Engine Active.\`;
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({
                type: "chat_chunk",
                request_id,
                chunk: fallbackReply,
                full: fallbackReply,
                done: true
              }));
              ws.send(JSON.stringify({
                type: "chat_done",
                request_id,
                full: fallbackReply,
                time_taken: 0.15,
                tokens_per_sec: 75.0
              }));
            }`;

const replacement2 = `          } catch (err: any) {
            console.error("[NEXA WS] FastAPI Chat Error:", err);
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({
                type: "chat_error",
                request_id,
                error: \`Backend connection failed: \${err.message}\`
              }));
            }`;

content = content.replace(target1, replacement1);
content = content.replace(target2, replacement2);

const target3 = `          } catch (e) {
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({
                type: "voice_response",
                request_id,
                transcript: text || "Voice audio input received",
                status: "ok",
                reply_text: \`NEXA Voice Engine: Audio input processed over WebSocket.\`
              }));
            }`;
            
const replacement3 = `          } catch (e: any) {
            console.error("[NEXA WS] Voice Engine Error:", e);
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({
                type: "voice_error",
                request_id,
                error: \`Voice backend connection failed: \${e.message}\`
              }));
            }`;

content = content.replace(target3, replacement3);

fs.writeFileSync('server.ts', content);
