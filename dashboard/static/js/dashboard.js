// Dashboard interactivity and AJAX API helpers

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

// User Creation AJAX
async function handleCreateUser(event) {
    event.preventDefault();
    const discord_id = document.getElementById('userDiscordId').value;
    const username = document.getElementById('username').value;
    const email = document.getElementById('userEmail').value || null;

    try {
        const response = await fetch('/api/v1/users', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ discord_id, username, email })
        });

        if (response.ok) {
            window.location.reload();
        } else {
            const error = await response.json();
            alert('Ошибка регистрации пользователя: ' + (error.detail || 'Неизвестная ошибка'));
        }
    } catch (err) {
        console.error(err);
        alert('Не удалось подключиться к серверу');
    }
}

// Category Creation AJAX
async function handleCreateCategory(event) {
    event.preventDefault();
    const label = document.getElementById('categoryLabel').value;
    const description = document.getElementById('categoryDesc').value;
    const emoji = document.getElementById('categoryEmoji').value || '🎫';

    try {
        const guildId = window.location.pathname.split('/')[2];
        const response = await fetch(`/api/v1/categories?guild_id=${guildId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ label, description, emoji })
        });

        if (response.ok) {
            window.location.reload();
        } else {
            const error = await response.json();
            alert('Ошибка создания категории: ' + (error.detail || 'Неизвестная ошибка'));
        }
    } catch (err) {
        console.error(err);
        alert('Не удалось подключиться к серверу');
    }
}

// Category Deletion AJAX
async function deleteCategory(categoryId) {
    if (!confirm('Вы уверены, что хотите удалить эту категорию?')) {
        return;
    }

    try {
        const guildId = window.location.pathname.split('/')[2];
        const response = await fetch(`/api/v1/categories/${categoryId}?guild_id=${guildId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            window.location.reload();
        } else {
            alert('Ошибка удаления категории');
        }
    } catch (err) {
        console.error(err);
        alert('Не удалось подключиться к серверу');
    }
}

// Panel Settings Save AJAX
async function handleSaveSettings(event) {
    event.preventDefault();
    const title = document.getElementById('panelTitle').value;
    const description = document.getElementById('panelDesc').value;
    const color = document.getElementById('panelColor').value;
    const banner_url = document.getElementById('panelBanner').value;
    const footer_text = document.getElementById('panelFooter').value;

    try {
        const guildId = window.location.pathname.split('/')[2];
        const response = await fetch(`/api/v1/config?guild_id=${guildId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ title, description, color, banner_url, footer_text })
        });

        if (response.ok) {
            alert('✅ Настройки успешно сохранены!');
            window.location.reload();
        } else {
            alert('Ошибка сохранения настроек');
        }
    } catch (err) {
        console.error(err);
        alert('Не удалось подключиться к серверу');
    }
}
