export interface Memory {
    id: number;
    type: string;
    content: string;
    metadata: string;
    is_pinned: boolean;
    is_archived: boolean;
    created_at: string;
    updated_at: string;
}

export class MemoryService {
    async createMemory(type: string, content: string, metadata: any = {}): Promise<number> {
        // Mock API call to Python engine
        console.log('Creating memory:', type, content);
        return 1;
    }

    async getMemory(id: number): Promise<Memory | null> {
        return null;
    }

    async updateMemory(id: number, content: string, metadata: any = {}): Promise<boolean> {
        return true;
    }

    async deleteMemory(id: number): Promise<boolean> {
        return true;
    }

    async searchMemory(query: string): Promise<Memory[]> {
        // Calls semantic search (currently keyword fallback)
        return [];
    }

    async pinMemory(id: number, isPinned: boolean = true): Promise<boolean> {
        return true;
    }

    async archiveMemory(id: number, isArchived: boolean = true): Promise<boolean> {
        return true;
    }
}
