import {useEffect, useState} from 'react';
import {useNavigate} from 'react-router-dom';
import {API_BASE} from '../services/api.js';

export default function AuthWrapper({children}) {
    const [isAuthenticated, setIsAuthenticated] = useState(null);
    const navigate = useNavigate();

    useEffect(() => {
        // Проверяем наличие токена в localStorage
        const token = localStorage.getItem('token');

        if (!token) {
            // Если токена нет, перенаправляем на страницу входа
            navigate('/login');
            return;
        }

        // Проверяем действительность токена с помощью API
        const verifyToken = async () => {
            try {
                const response = await fetch(`${API_BASE}/api/users/me`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.ok) {
                    setIsAuthenticated(true);
                } else {
                    // Токен недействителен, удаляем его и перенаправляем на вход
                    localStorage.removeItem('token');
                    navigate('/login');
                }
            } catch (error) {
                console.error('Ошибка проверки токена:', error);
                localStorage.removeItem('token');
                navigate('/login');
            }
        };

        verifyToken();
    }, [navigate]);

    // Пока проверяется аутентификация, ничего не показываем
    if (isAuthenticated === null) {
        return <div className="loading">Проверка аутентификации...</div>;
    }

    // Если пользователь аутентифицирован, отображаем содержимое
    return isAuthenticated ? children : null;
}
