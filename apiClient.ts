
export const nexaApiClient = {
    healthCheck: async () => (await fetch('http://localhost:5000/health')).json(),
    chat: async (msg: string) => (await fetch('http://localhost:5000/chat', { 
        method: 'POST', 
        body: JSON.stringify({message: msg}) 
    })).json()
};
