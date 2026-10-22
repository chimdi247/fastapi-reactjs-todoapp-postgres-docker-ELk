import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { todoService } from '../services/todoService';



export default function EditTodo() {


    const params = useParams();
    const id = Number(params.id);

    const navigate = useNavigate();

    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [isCompleted, setIsCompleted] = useState(false);

    const [error, setError] = useState<string | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);


    useEffect(() => {
        fetchTodo();
    }, [id]);


    const fetchTodo = async () => {
        try {
            setError(null);
            const todo = await todoService.getTodoById(id);

            setTitle(todo.title);
            setDescription(todo.description);
            setIsCompleted(todo.is_completed);

        } catch (err: any) {
            setError(err.message || 'Failed to load task details.');
        }
    };



    const handleSubmit = async (e: React.SubmitEvent) => {
        e.preventDefault();
        if (!title.trim()) return;

        try {
            setError(null);
            setIsSubmitting(true);
            await todoService.updateTodo(id, title.trim(), description.trim(), isCompleted);
            navigate('/todos');
        } catch (err: any) {
            setError(err.message || 'Failed to update task. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };


    return (
        <div className="form-page">
            <div className="form-page__card">
                <h1 className="form-page__title">Update Todo</h1>
                <p className="form-page__desc">Edit the details of your task below.</p>

                {error && <div className="form-page__error">{error}</div>}

                <form onSubmit={handleSubmit} className="form-page__form">
                    <div className="form-page__group">
                        <label htmlFor="title" className="form-page__label">Task Title *</label>
                        <input id="title" type="text" className="form-page__input" value={title} onChange={(e) => setTitle(e.target.value)} required />
                    </div>
                    <div className="form-page__group">
                        <label htmlFor="desc" className="form-page__label">Description</label>
                        <textarea id="desc" className="form-page__textarea" value={description} onChange={(e) => setDescription(e.target.value)} rows={4} />
                    </div>

                    {/* New Completion Checkbox */}
                    <div className="form-page__group form-page__group--checkbox">
                        <label className="form-page__checkbox-label">
                            <input
                                type="checkbox"
                                checked={isCompleted}
                                onChange={(e) => setIsCompleted(e.target.checked)}
                                className="form-page__checkbox"
                            />
                            <span>Mark as completed</span>
                        </label>
                    </div>

                    <div className="form-page__actions">
                        <button type="button" onClick={() => navigate(-1)} className="form-page__btn form-page__btn--secondary">Cancel</button>
                        <button type="submit" disabled={isSubmitting} className="form-page__btn form-page__btn--primary">
                            {isSubmitting ? 'Saving...' : 'Save Changes'}
                        </button>
                    </div>
                </form>
            </div>
        </div>

    )

}