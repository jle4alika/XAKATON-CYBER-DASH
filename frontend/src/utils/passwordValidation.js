/**
 * Валидация пароля с проверкой критериев безопасности
 * @param {string} password - Пароль для проверки
 * @returns {Object} Объект с результатами валидации
 */
export function validatePassword(password) {
    const criteria = {
        minLength: password.length >= 8,
        hasUpperCase: /[A-ZА-ЯЁ]/.test(password),
        hasLowerCase: /[a-zа-яё]/.test(password),
        hasNumber: /\d/.test(password),
        hasSpecialChar: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password),
    };

    const isValid = Object.values(criteria).every(Boolean);

    const messages = {
        minLength: 'Минимум 8 символов',
        hasUpperCase: 'Хотя бы одна заглавная буква',
        hasLowerCase: 'Хотя бы одна строчная буква',
        hasNumber: 'Хотя бы одна цифра',
        hasSpecialChar: 'Хотя бы один специальный символ (!@#$%^&*...)',
    };

    const failedCriteria = Object.entries(criteria)
        .filter(([_, passed]) => !passed)
        .map(([key]) => messages[key]);

    return {
        isValid,
        criteria,
        failedCriteria,
        messages,
    };
}

