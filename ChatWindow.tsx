
// NEXA Desktop Chat Window Component
import React, { useState, useEffect } from 'react';

export const ChatWindow = () => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');

    const sendMessage = async () => {
        const newMsg = { role: 'user', content: input };
        setMessages([...messages, newMsg]);
        setInput('');

        const response = await fetch('http://localhost:5000/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: input, stream: true })
        });

        const reader = response.body.getReader();
        let aiMsg = { role: 'assistant', content: '' };
        setMessages(prev => [...prev, aiMsg]);

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = new TextDecoder().decode(value);
            const data = JSON.parse(chunk);
            aiMsg.content += data.token;
            setMessages(prev => [...prev.slice(0, -1), { ...aiMsg }]);
        }
    };

    return <div className='chat-container'>/* UI Render Logic */</div>;
};
