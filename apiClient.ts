
export const nexaApiClient = {
    healthCheck: async () => (await fetch('/api/health')).json(),
    telemetry: async () => (await fetch('/api/telemetry')).json(),
    chat: async (msg: string) => (await fetch('/api/chat', { 
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg }) 
    })).json()
};
