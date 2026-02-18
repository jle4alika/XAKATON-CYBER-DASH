import useErrorStore from '../../store/errorStore'
import styles from './SettingsPage.module.css'

export default function SettingsPage() {
    const errors = useErrorStore((s) => s.errors)
    const clearErrors = useErrorStore((s) => s.clearErrors)

    return (
        <div className={`${styles.stack} ${styles.container}`}>
            <div className={styles.panelTitle}>
                <h2>Настройки и диагностика</h2>
                <button className="btn" type="button" onClick={clearErrors}>
                    Очистить ошибки
                </button>
            </div>
            <div className={`${styles.panel} ${styles.stack}`}>
                <h3 style={{margin: 0}}>Ошибки API/WS</h3>
                {errors.length === 0 && <div className={styles.empty}>Ошибок нет</div>}
                {errors.map((err) => (
                    <div key={err.id} className="event-item">
                        <div className="flex-between">
                            <div className="muted">{new Date(err.timestamp).toLocaleString()}</div>
                            <span className="badge">{err.source}</span>
                        </div>
                        <div>{err.message}</div>
                        {err.context && <div className="muted">{JSON.stringify(err.context)}</div>}
                    </div>
                ))}
            </div>
        </div>
    )
}

