import {useState} from 'react';
import {useNavigate, Link} from 'react-router-dom';
import {registerUser} from '../../services/api.js';
import {validatePassword} from '../../utils/passwordValidation.js';
import styles from './RegisterPage.module.css';

export default function RegisterPage() {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [passwordValidation, setPasswordValidation] = useState(null);
    const navigate = useNavigate();

    const handlePasswordChange = (e) => {
        const newPassword = e.target.value;
        setPassword(newPassword);

        if (newPassword.length > 0) {
            const validation = validatePassword(newPassword);
            setPasswordValidation(validation);
        } else {
            setPasswordValidation(null);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        // Валидация пароля
        const validation = validatePassword(password);
        if (!validation.isValid) {
            setError('Пароль не соответствует требованиям безопасности');
            return;
        }

        // Проверка совпадения паролей
        if (password !== confirmPassword) {
            setError('Пароли не совпадают');
            return;
        }

        setIsLoading(true);
        setError('');

        try {
            await registerUser({username, email, password});

            // После успешной регистрации перенаправляем на страницу входа
            navigate('/login');
        } catch (err) {
            setError(err.message || 'Ошибка регистрации');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className={styles.page}>
            <div className={styles.container}>
                <div className={styles.formContainer}>
                    <h1 className={styles.title}>Регистрация</h1>
                    <form onSubmit={handleSubmit} className={styles.form}>
                        <div className={styles.inputGroup}>
                            <label htmlFor="username" className={styles.label}>
                                Имя пользователя
                            </label>
                            <input
                                id="username"
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                className={styles.input}
                                required
                            />
                        </div>
                        <div className={styles.inputGroup}>
                            <label htmlFor="email" className={styles.label}>
                                Email
                            </label>
                            <input
                                id="email"
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className={styles.input}
                                required
                            />
                        </div>
                        <div className={styles.inputGroup}>
                            <label htmlFor="password" className={styles.label}>
                                Пароль
                            </label>
                            <input
                                id="password"
                                type="password"
                                value={password}
                                onChange={handlePasswordChange}
                                className={`${styles.input} ${passwordValidation && !passwordValidation.isValid ? styles.inputError : ''}`}
                                required
                            />
                            {passwordValidation && (
                                <div className={styles.passwordCriteria}>
                                    <div className={styles.criteriaTitle}>
                                        Требования к паролю:
                                    </div>
                                    <ul className={styles.criteriaList}>
                                        <li className={passwordValidation.criteria.minLength ? styles.criteriaMet : styles.criteriaFailed}>
                                            {passwordValidation.criteria.minLength ? '✓' : '✗'} {passwordValidation.messages.minLength}
                                        </li>
                                        <li className={passwordValidation.criteria.hasUpperCase ? styles.criteriaMet : styles.criteriaFailed}>
                                            {passwordValidation.criteria.hasUpperCase ? '✓' : '✗'} {passwordValidation.messages.hasUpperCase}
                                        </li>
                                        <li className={passwordValidation.criteria.hasLowerCase ? styles.criteriaMet : styles.criteriaFailed}>
                                            {passwordValidation.criteria.hasLowerCase ? '✓' : '✗'} {passwordValidation.messages.hasLowerCase}
                                        </li>
                                        <li className={passwordValidation.criteria.hasNumber ? styles.criteriaMet : styles.criteriaFailed}>
                                            {passwordValidation.criteria.hasNumber ? '✓' : '✗'} {passwordValidation.messages.hasNumber}
                                        </li>
                                        <li className={passwordValidation.criteria.hasSpecialChar ? styles.criteriaMet : styles.criteriaFailed}>
                                            {passwordValidation.criteria.hasSpecialChar ? '✓' : '✗'} {passwordValidation.messages.hasSpecialChar}
                                        </li>
                                    </ul>
                                </div>
                            )}
                        </div>
                        <div className={styles.inputGroup}>
                            <label htmlFor="confirmPassword" className={styles.label}>
                                Подтвердите пароль
                            </label>
                            <input
                                id="confirmPassword"
                                type="password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                className={styles.input}
                                required
                            />
                        </div>
                        {error && <div className={styles.error}>{error}</div>}
                        <button
                            type="submit"
                            disabled={isLoading}
                            className={styles.button}
                        >
                            {isLoading ? 'Регистрация...' : 'Зарегистрироваться'}
                        </button>
                    </form>
                    <p className={styles.switchForm}>
                        Уже есть аккаунт?{' '}
                        <Link to="/login" className={styles.link}>
                            Войдите
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
}

