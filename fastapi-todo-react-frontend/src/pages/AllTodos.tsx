import { useEffect, useState } from "react";
import { todoService, type Todo } from "../services/todoService";
import { Link } from "react-router-dom";


export default function AllTodos() {


    const [todos, setTodos] = useState<Todo[]>([]);
    const [error, setError] = useState<string | null>(null);

    const [isModalOpen, setIsModalOpen] = useState(false);
    const [todoToDelete, setTodoToDelete] = useState<number | null>(null);


    useEffect(() => {
        fetchTodos()
    }, []);


    const fetchTodos = async () => {
        try {
            setError(null);
            const data = await todoService.getAllTodos();
            setTodos(data);
        } catch (err: any) {
            setError(err.message || 'Failed to load todos.');
        }
    };



    const openModal = (id: number) => {
        setTodoToDelete(id);
        setIsModalOpen(true);
    };

    const confirmDelete = async () => {
        if (todoToDelete === null) return;
        try {
            setError(null);
            await todoService.deleteTodo(todoToDelete);
            setTodos(prev => prev.filter(t => t.id !== todoToDelete));
            closeModal();
        } catch (err: any) {
            setError(err.message || 'Failed to delete todo.');
        }
    };


    const closeModal = () => {
        setIsModalOpen(false);
        setTodoToDelete(null);
    };

    return (
        <>
            <div className="todos-page">
                <div className="todos-page__header">
                    <h1 className="todos-page__title">My Todo's</h1>
                    <Link to="/add" className="todos-page__add-btn">+ Add New</Link>
                </div>

                {error && <div className="error-banner">{error}</div>}

                {todos.length === 0 && !error ? (
                    <div className="todos-page__empty">
                        <span className="todos-page__empty-icon">📝</span>
                        <h2>No tasks yet!</h2>
                        <p>Create your first task to get started.</p>
                    </div>
                ) : (
                    <ul className="todos-page__list">
                        {todos.map((todo) => (
                            <li key={todo.id} className={`todos-page__item ${todo.is_completed ? 'todos-page__item--completed' : ''}`}>
                                <div className="todos-page__item-content">

                                    <div>
                                        <h3 className="todos-page__item-title">{todo.title}</h3>
                                        {todo.description && <p className="todos-page__item-desc">{todo.description}</p>}
                                    </div>
                                </div>
                                <div className="todos-page__item-actions">
                                    <Link to={`/todos/${todo.id}/edit`} className="btn-icon btn-icon--edit">Edit</Link>
                                    <button onClick={() => openModal(todo.id)} className="btn-icon btn-icon--delete">Delete</button>
                                </div>
                            </li>
                        ))}
                    </ul>
                )}
            </div>

            {isModalOpen && (
                <div className="modal-overlay" onClick={closeModal}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <h2 className="modal-title">Delete Task?</h2>
                        <p className="modal-desc">Are you sure you want to delete this task? This action cannot be undone.</p>
                        {error && <div className="error-banner error-banner--modal">{error}</div>}
                        <div className="modal-actions">
                            <button onClick={closeModal} className="modal-btn modal-btn--cancel">Cancel</button>
                            <button onClick={confirmDelete} className="modal-btn modal-btn--confirm">Yes, Delete</button>
                        </div>
                    </div>
                </div>
            )}
        </>
    )

}