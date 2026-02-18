import useSimulationStore from '../../store/simulationStore.js'
import styles from './TimeControlPanel.module.css'

export default function TimeControlPanel() {
    const speed = useSimulationStore((state) => state.speed)
    const isPaused = useSimulationStore((state) => state.isPaused)
    const status = useSimulationStore((state) => state.status)
    const updating = useSimulationStore((state) => state.updating)
    const setSpeed = useSimulationStore((state) => state.setSpeed)
    const pause = useSimulationStore((state) => state.pause)
    const resume = useSimulationStore((state) => state.resume)

    return (
        <section className={`${styles.panel} ${styles.stack}`}>
            <div className={styles.panelHeader}>
                <h3 className={styles.panelTitle}>Панель времени</h3>
            </div>
            <div className={styles.stack}>
                <div className={styles.sliderWrapper}>
                    <div className={styles.progressTrack} style={{width: `${((speed - 0.5) / 4.5) * 100}%`}}/>
                    <input
                        type="range"
                        min="0.5"
                        max="5"
                        step="0.5"
                        value={speed}
                        onChange={(e) => setSpeed(Number(e.target.value))}
                        aria-label="Скорость воспроизведения"
                        aria-valuetext={`${speed}x`}
                        className={styles.input}
                    />
                    <div className={styles.labels}>
                        <span>0.5x</span>
                        <span>2.75x</span>
                        <span>5x</span>
                    </div>
                    <div className={styles.valueBadge} aria-hidden="true">
                        {speed}x
                    </div>
                </div>
                <div className={styles.flex}>
                    <button className={`${styles.btn} ${styles.btnDanger}`} onClick={pause}
                            disabled={isPaused || updating}>
                        Пауза
                    </button>
                    <button className={`${styles.btn} ${styles.btnPrimary}`} onClick={resume}
                            disabled={!isPaused || updating}>
                        Продолжить
                    </button>
                </div>
                <div className={styles.muted}>{status || (isPaused ? 'На паузе' : 'Идёт симуляция')}</div>
            </div>
        </section>
    )
}

