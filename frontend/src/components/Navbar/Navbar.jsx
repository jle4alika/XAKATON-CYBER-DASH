import {useState, useEffect} from 'react';
import {NavLink, Link, useNavigate} from 'react-router-dom';
import styles from './Navbar.module.css';

export default function Navbar() {
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [isScrolled, setIsScrolled] = useState(false);
    const navigate = useNavigate();

    useEffect(() => {
        // Проверяем наличие токена в localStorage
        const token = localStorage.getItem('token');
        setIsAuthenticated(!!token);

        // Функция для проверки изменений в localStorage
        const checkAuthState = () => {
            const currentToken = localStorage.getItem('token');
            setIsAuthenticated(!!currentToken);
        };

        // Проверяем состояние при монтировании
        checkAuthState();

        // Добавляем слушатель событий для изменения localStorage
        window.addEventListener('storage', checkAuthState);

        // Для отслеживания изменений в том же окне (localStorage события не срабатывают в том же окне)
        const intervalId = setInterval(checkAuthState, 1000);

        const handleResize = () => {
            if (window.innerWidth > 800) {
                setIsSidebarOpen(false);
            }
        };

        // Обработчик скролла для добавления фона navbar
        const handleScroll = () => {
            const scrollPosition = window.scrollY || document.documentElement.scrollTop;
            setIsScrolled(scrollPosition > 20);
        };

        window.addEventListener('resize', handleResize);
        window.addEventListener('scroll', handleScroll);

        // Проверяем начальную позицию скролла
        handleScroll();

        return () => {
            window.removeEventListener('storage', checkAuthState);
            window.removeEventListener('resize', handleResize);
            window.removeEventListener('scroll', handleScroll);
            clearInterval(intervalId);
        };
    }, []);

    const toggleSidebar = () => {
        setIsSidebarOpen(!isSidebarOpen);
    };

    const closeSidebar = () => {
        setIsSidebarOpen(false);
    };

    const handleLogout = () => {
        // Удаляем токен и перенаправляем на страницу входа
        localStorage.removeItem('token');
        setIsAuthenticated(false);
        navigate('/login');
    };

    // Ссылки для навигации в зависимости от состояния аутентификации
    const links = isAuthenticated
        ? [
            {to: '/dashboard', label: 'Дашборд'},
            {to: '/group-chat', label: 'Групповые чаты'},
            {to: '/relations', label: 'Отношения'},
            // {to: '/settings', label: 'Настройки'},
        ]
        : [];

    return (
        <>
            <header className={`${styles.navbar} ${isScrolled ? styles.scrolled : ''}`}>
                <div className={styles.navbarInner}>
                    <div className={styles.brand}>
                        <Link
                            to="/"
                            className={styles.brand}
                            aria-label="На главную"
                        >
                            <span className={styles.logoDot}/>
                            <span className={styles.navTitle}>КИБЕР-РЫВОК</span>
                        </Link>
                    </div>
                    <nav className={styles.navLinks}>
                        {isAuthenticated ? (
                            <>
                                {links.map((link) => (
                                    <NavLink
                                        key={link.to}
                                        to={link.to}
                                        className={({isActive}) =>
                                            isActive ? styles.navLinkActive : styles.navLink
                                        }
                                        end={link.to === '/'}
                                    >
                                        {link.label}
                                    </NavLink>
                                ))}
                                <Link
                                    onClick={handleLogout}
                                    to="/login"
                                    className={styles.exit}
                                    aria-label="Выйти"
                                >
                                    <span className={styles.navLinkExit}>Выйти</span>
                                </Link>
                                <button onClick={toggleSidebar} className={styles.navToggle}>
                                    <svg
                                        className={styles.navOpen}
                                        xmlns="http://www.w3.org/2000/svg"
                                        height="30px"
                                        viewBox="0 -960 960 960"
                                        width="30px"
                                        fill="#e3e3e3"
                                    >
                                        <path d="M120-240v-80h720v80H120Zm0-200v-80h720v80H120Zm0-200v-80h720v80H120Z"/>
                                    </svg>
                                </button>
                            </>
                        ) : (
                            <>
                                <NavLink to="/login" className={styles.navLink}>
                                    Вход
                                </NavLink>
                                <NavLink to="/register" className={styles.navLink}>
                                    Регистрация
                                </NavLink>
                            </>
                        )}
                    </nav>
                </div>
            </header>

            {/* Затемнение фона — закрывает меню при клике */}
            <div
                className={`${styles.sidebarOverlay} ${isSidebarOpen ? styles.active : ''}`}
                onClick={closeSidebar}
            />

            {/* Сайдбар */}
            <aside
                id="sidebar"
                className={`${styles.sidebar} ${isSidebarOpen ? styles.active : ''}`}
            >
                <div className={styles.sideBrand}>
                    <span className={styles.sideLogoDot}/>
                    <span className={styles.title}>КИБЕР-РЫВОК</span>
                    {/* Крестик — закрывает меню */}
                    <button className={styles.closeButton} onClick={closeSidebar}>
                        &times;
                    </button>
                </div>
                <nav className={styles.sideLinks}>
                    {isAuthenticated && links.map((link) => (
                        <NavLink
                            key={link.to}
                            to={link.to}
                            className={({isActive}) =>
                                `${styles.sideItem} ${isActive ? styles.sideItemActive : ''}`
                            }
                            end={link.to === '/'}
                        >
                            {link.label}
                        </NavLink>
                    ))}
                    {isAuthenticated && (
                        <button onClick={handleLogout} className={styles.sideItemExit}>
                            Выйти
                        </button>
                    )}
                </nav>
            </aside>
        </>
    );
}
