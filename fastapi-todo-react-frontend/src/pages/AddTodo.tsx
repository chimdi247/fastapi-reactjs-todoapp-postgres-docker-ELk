import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { todoService } from '../services/todoService';



export default function AddTodo() {

    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');

    const [error, setError] = useState<string | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const navigate = useNavigate();



    const handleSubmit = async (e: React.SubmitEvent) => {
        e.preventDefault();
        if (!title.trim()) return;

        try {
            setError(null);
            setIsSubmitting(true);
            await todoService.createTodo(title.trim(), description.trim());
            navigate('/todos');
        } catch (err: any) {
            setError(err.message || 'Failed to create todo. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="form-page">
            <div className="form-page__card">
                <h1 className="form-page__title">Add New Todo</h1>
                <p className="form-page__desc">Fill in the details below to create a new task.</p>

                {error && <div className="form-page__error">{error}</div>}

                <form onSubmit={handleSubmit} className="form-page__form">
                    <div className="form-page__group">
                        <label htmlFor="title" className="form-page__label">Task Title *</label>
                        <input id="title" type="text" className="form-page__input" placeholder="e.g., Buy groceries" value={title} onChange={(e) => setTitle(e.target.value)} required />
                    </div>
                    <div className="form-page__group">
                        <label htmlFor="desc" className="form-page__label">Description</label>
                        <textarea id="desc" className="form-page__textarea" placeholder="Add some details..." value={description} onChange={(e) => setDescription(e.target.value)} rows={4} />
                    </div>
                    <div className="form-page__actions">
                        <button type="button" onClick={() => navigate(-1)} className="form-page__btn form-page__btn--secondary">Cancel</button>
                        <button type="submit" disabled={isSubmitting} className="form-page__btn form-page__btn--primary">
                            {isSubmitting ? 'Creating...' : 'Create Todo'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )


}

