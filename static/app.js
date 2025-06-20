document.addEventListener('DOMContentLoaded', () => {
    const userInput = document.getElementById('user-input');

    if (userInput) {
        userInput.addEventListener('input', () => {
            userInput.style.height = 'auto'; // Сбросить высоту
            // Установить новую высоту на основе содержимого, но не больше max-height из CSS
            userInput.style.height = `${userInput.scrollHeight}px`; 
        });
    }
}); 