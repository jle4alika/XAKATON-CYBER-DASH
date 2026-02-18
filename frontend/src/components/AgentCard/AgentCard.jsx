import {useMemo, useState} from 'react'
import {useNavigate} from 'react-router-dom'
import useAgentStore from '../../store/agentStore.js'
import styles from './AgentCard.module.css'

const moodToColor = (mood = 0) => {
    if (mood >= 0.7) return 'var(--accent-green)'
    if (mood >= 0.4) return 'var(--accent-yellow)'
    return 'var(--accent-red)'
}

export default function AgentCard({agent}) {
    const navigate = useNavigate()
    const moodColor = useMemo(() => moodToColor(agent?.mood ?? 0.5), [agent])
    const deleteAgent = useAgentStore((state) => state.deleteAgent)
    const [isDeleting, setIsDeleting] = useState(false)
    const [isCopied, setIsCopied] = useState(false)

    if (!agent) return null

    const goToProfile = () => navigate(`/agent/${agent.id}`)
    const handleKey = (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            goToProfile()
        }
    }

    const handleCopyUUID = async (e) => {
        e.stopPropagation() // Предотвращаем переход на профиль
        try {
            await navigator.clipboard.writeText(agent.id)
            setIsCopied(true)
            setTimeout(() => setIsCopied(false), 2000)
        } catch (err) {
            console.error('Ошибка при копировании UUID:', err)
            // Fallback для старых браузеров
            const textArea = document.createElement('textarea')
            textArea.value = agent.id
            textArea.style.position = 'fixed'
            textArea.style.opacity = '0'
            document.body.appendChild(textArea)
            textArea.select()
            try {
                document.execCommand('copy')
                setIsCopied(true)
                setTimeout(() => setIsCopied(false), 2000)
            } catch (fallbackErr) {
                console.error('Fallback копирование не удалось:', fallbackErr)
                alert('Не удалось скопировать UUID')
            }
            document.body.removeChild(textArea)
        }
    }

    const handleDelete = async (e) => {
        e.stopPropagation() // Предотвращаем переход на профиль
        if (!window.confirm(`Вы уверены, что хотите удалить агента "${agent.name}"? Это действие нельзя отменить.`)) {
            return
        }
        setIsDeleting(true)
        try {
            await deleteAgent(agent.id)
        } catch (err) {
            console.error('Ошибка при удалении агента:', err)
            alert('Не удалось удалить агента. Попробуйте еще раз.')
        } finally {
            setIsDeleting(false)
        }
    }

    return (
        <div
            className={styles.card}
            onClick={goToProfile}
            onKeyDown={handleKey}
            role="button"
            tabIndex={0}
            aria-label={`Agent ${agent.name}`}
        >
            <div className={styles.flexBetween}>
                <div>
                    <h3 style={{margin: 0, color: "#fff"}}>{agent.name || 'Agent'}</h3>
                    <div className={styles.muted}>ID: {agent.id}</div>
                </div>
                <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
                    <span className={styles.moodIndicator} style={{background: moodColor}} aria-label="mood-indicator"/>
                    <button
                        onClick={handleCopyUUID}
                        className={styles.copyButton}
                        aria-label="Копировать UUID"
                        title={isCopied ? 'UUID скопирован!' : 'Копировать UUID'}
                    >
                        {isCopied ? (
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                                 strokeWidth="2">
                                <path d="M20 6L9 17l-5-5"/>
                            </svg>
                        ) : (
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                                 strokeWidth="2">
                                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                            </svg>
                        )}
                    </button>
                    <button
                        onClick={handleDelete}
                        disabled={isDeleting}
                        className={styles.deleteButton}
                        aria-label="Удалить агента"
                        title="Удалить агента"
                    >
                        {isDeleting ? '...' : '×'}
                    </button>
                </div>
            </div>

            <div className={styles.flex}>
                <span className={styles.chip}>Настроение: {(agent.mood ?? 0).toFixed(2)}</span>
                <span className={styles.chip}>Энергия: {Math.round(agent.energy ?? 0)}</span>
            </div>

            <div className={styles.stack}>
                <div className={styles.energyBar} aria-hidden>
                    <div
                        className={styles.energyFill}
                        style={{width: `${Math.min(100, Math.max(0, agent.energy ?? 0))}%`}}
                    />
                </div>
                <div className={styles.muted} style={{fontSize: 13}}>
                    {agent.status || agent.currentTask || 'Готов к действию'}
                </div>
            </div>
        </div>
    )
}


