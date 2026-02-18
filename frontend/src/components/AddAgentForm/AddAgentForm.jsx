import {useState, useEffect} from 'react'
import {createPortal} from 'react-dom'
import useAgentStore from '../../store/agentStore.js'
import {createAgent} from '../../services/api.js'
import styles from './AddAgentForm.module.css'

export default function AddAgentForm() {
    const [isOpen, setIsOpen] = useState(false)
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [formData, setFormData] = useState({
        name: '',
        mood: 0.5,
        energy: 80,
        traits: '',
        persona: '',
        currentTask: ''
    })

    const fetchAgents = useAgentStore((state) => state.fetchAgents)

    // Блокировка скролла страницы при открытом модальном окне
    useEffect(() => {
        if (isOpen) {
            document.body.style.overflow = 'hidden'
        } else {
            document.body.style.overflow = 'unset'
        }
        return () => {
            document.body.style.overflow = 'unset'
        }
    }, [isOpen])

    // Закрытие по Esc
    useEffect(() => {
        const handleEsc = (e) => {
            if (e.key === 'Escape') setIsOpen(false)
        }
        window.addEventListener('keydown', handleEsc)
        return () => window.removeEventListener('keydown', handleEsc)
    }, [])

    const handleChange = (e) => {
        const {name, value} = e.target
        setFormData(prev => ({
            ...prev,
            [name]: name === 'mood' || name === 'energy' ? parseFloat(value) || 0 : value
        }))
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setIsSubmitting(true)

        try {
            const traitsArray = formData.traits
                .split(',')
                .map(t => t.trim())
                .filter(t => t)

            const agentData = {
                name: formData.name,
                mood: formData.mood,
                energy: formData.energy,
                traits: traitsArray,
                // Теперь персона передаётся как простой текст, без JSON
                persona: formData.persona || null,
                current_task: formData.currentTask
            }

            await createAgent(agentData)
            fetchAgents()

            setFormData({
                name: '',
                mood: 0.5,
                energy: 80,
                traits: '',
                persona: '',
                currentTask: ''
            })

            setIsOpen(false)
        } catch (err) {
            console.error('Ошибка при создании агента:', err)
            alert('Ошибка при создании агента: ' + (err.message || 'Проверьте данные формы'))
        } finally {
            setIsSubmitting(false)
        }
    }

    // Обработчик клика по оверлею (закрытие при клике вне формы)
    const handleOverlayClick = (e) => {
        if (e.target === e.currentTarget) {
            setIsOpen(false)
        }
    }

    return (
        <>
            {/* Кнопка вызова модального окна */}
            <button className={`${styles.btn} ${styles.btnPrimary}`} onClick={() => setIsOpen(true)}>
                Добавить агента
            </button>

            {/* Модальное окно (через портал в document.body, чтобы оно стояло поверх всей разметки) */}
            {isOpen &&
                createPortal(
                    <div className={styles.overlay} onClick={handleOverlayClick}>
                        <div className={styles.modal}>
                            <div className={styles.panel}>
                                <div className={styles.panelHeader}>
                                    <h3 className={styles.panelTitle}>Добавить нового агента</h3>
                                    <button className={styles.btnIcon} onClick={() => setIsOpen(false)}
                                            aria-label="Закрыть">
                                        ×
                                    </button>
                                </div>

                                <form onSubmit={handleSubmit} className={styles.stack}>
                                    <div className={styles.formGroup}>
                                        <label htmlFor="name" className={styles.label}>Имя *</label>
                                        <input
                                            id="name"
                                            name="name"
                                            className={styles.input}
                                            value={formData.name}
                                            onChange={handleChange}
                                            required
                                            autoFocus // Автофокус при открытии
                                        />
                                    </div>

                                    <div className={styles.formRow}>
                                        <div className={styles.formGroup}>
                                            <label htmlFor="mood" className={styles.label}>Настроение (0-1)</label>
                                            <input
                                                id="mood"
                                                name="mood"
                                                type="number"
                                                min="0"
                                                max="1"
                                                step="0.1"
                                                className={styles.input}
                                                value={formData.mood}
                                                onChange={handleChange}
                                            />
                                        </div>

                                        <div className={styles.formGroup}>
                                            <label htmlFor="energy" className={styles.label}>Энергия (0-100)</label>
                                            <input
                                                id="energy"
                                                name="energy"
                                                type="number"
                                                min="0"
                                                max="100"
                                                className={styles.input}
                                                value={formData.energy}
                                                onChange={handleChange}
                                            />
                                        </div>
                                    </div>

                                    <div className={styles.formGroup}>
                                        <label htmlFor="traits" className={styles.label}>Черты характера (через
                                            запятую)</label>
                                        <input
                                            id="traits"
                                            name="traits"
                                            className={styles.input}
                                            value={formData.traits}
                                            onChange={handleChange}
                                            placeholder="дружелюбный, активный, любопытный"
                                        />
                                    </div>

                                    <div className={styles.formGroup}>
                                        <label htmlFor="persona" className={styles.label}>Описание персонажа</label>
                                        <textarea
                                            id="persona"
                                            name="persona"
                                            className={styles.textarea}
                                            value={formData.persona}
                                            onChange={handleChange}
                                            placeholder="Краткое описание характера, роли и прошлого персонажа"
                                            rows="3"
                                        />
                                    </div>

                                    <div className={styles.formGroup}>
                                        <label htmlFor="currentTask" className={styles.label}>Текущая задача</label>
                                        <input
                                            id="currentTask"
                                            name="currentTask"
                                            className={styles.input}
                                            value={formData.currentTask}
                                            onChange={handleChange}
                                            placeholder="Что делает сейчас"
                                        />
                                    </div>

                                    <div className={styles.flexEnd}>
                                        <button
                                            type="button"
                                            className={`${styles.btn} ${styles.btnSecondary}`}
                                            onClick={() => setIsOpen(false)}
                                            disabled={isSubmitting}
                                        >
                                            Отмена
                                        </button>
                                        <button
                                            className={`${styles.btn} ${styles.btnPrimary}`}
                                            type="submit"
                                            disabled={isSubmitting || !formData.name.trim()}
                                        >
                                            {isSubmitting ? 'Создание...' : 'Создать агента'}
                                        </button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>,
                    document.body,
                )}
        </>
    )
}