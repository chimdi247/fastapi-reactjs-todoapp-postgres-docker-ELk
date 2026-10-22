import { request } from '../lib/api';

export interface Todo {
    id: number;
    title: string;
    description: string;
    is_completed: boolean;
    created_at: string;
    updated_at: string;
}

export const todoService = {

    getAllTodos(): Promise<Todo[]> {
        return request<Todo[]>('/todos/');
    },

    getTodoById(id: number): Promise<Todo> {
        return request<Todo>(`/todos/${id}`);
    },

    createTodo(title: string, description: string): Promise<Todo> {
        return request<Todo>('/todos/', { method: 'POST', body: { title, description } });
    },

    updateTodo(id: number, title: string, description: string, is_completed: boolean): Promise<Todo> {
        return request<Todo>(`/todos/update/${id}`, {
            method: 'PUT',
            body: { title, description, is_completed },
        });
    },

    async deleteTodo(id: number): Promise<void> {
        await request<null>(`/todos/delete/${id}`, { method: 'DELETE' });
    },
}
