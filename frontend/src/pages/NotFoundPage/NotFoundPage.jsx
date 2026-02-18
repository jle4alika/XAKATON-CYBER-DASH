import {Link} from 'react-router-dom'
import styles from './NotFoundPage.module.css'

export default function NotFoundPage() {
    return (
        <div className={`${styles.container} panel stack page-container`}>
            <h2>404</h2>
            <div className="muted">Страница не найдена</div>
            <Link className="btn" to="/">
                Вернуться на дашборд
            </Link>
        </div>
    )
}

