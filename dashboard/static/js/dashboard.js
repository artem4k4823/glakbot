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
    
    // Сбор значений из чекбоксов
    let admin_role_ids = [];
    const checkboxes = document.querySelectorAll('input[name="admin_role_ids"]:checked');
    checkboxes.forEach((cb) => {
        admin_role_ids.push(cb.value);
    });

    try {
        const guildId = window.location.pathname.split('/')[2];
        const response = await fetch(`/api/v1/config?guild_id=${guildId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ title, description, color, banner_url, footer_text, admin_role_ids })
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

// ===================== Анкеты =====================

function currentGuildId() {
    return window.location.pathname.split('/')[2];
}

async function readError(response) {
    try {
        const data = await response.json();
        if (Array.isArray(data.detail)) {
            return data.detail.map((d) => d.msg).join('\n');
        }
        return data.detail || response.statusText;
    } catch (e) {
        return response.statusText;
    }
}

function dmNote(result) {
    if (result.dm_sent === false) {
        return '\n\n⚠️ Не удалось написать пользователю в ЛС (скорее всего, они закрыты).';
    }
    return '';
}

async function approveApplication(appId, btn) {
    if (!confirm('Одобрить анкету и выдать роль?')) return;
    btn.disabled = true;
    try {
        const response = await fetch(`/api/v1/applications/${appId}/approve?guild_id=${currentGuildId()}`, {
            method: 'POST'
        });
        if (!response.ok) {
            alert('Ошибка: ' + await readError(response));
            btn.disabled = false;
            return;
        }
        const result = await response.json();
        const note = dmNote(result);
        if (note) alert('✅ Роль выдана.' + note);
        window.location.reload();
    } catch (err) {
        console.error(err);
        alert('Не удалось подключиться к серверу');
        btn.disabled = false;
    }
}

function openRejectModal(appId, userName) {
    document.getElementById('rejectAppId').value = appId;
    document.getElementById('rejectUserName').textContent = userName;
    document.getElementById('rejectReason').value = '';
    openModal('rejectModal');
}

async function handleRejectApplication(event) {
    event.preventDefault();
    const appId = document.getElementById('rejectAppId').value;
    const reason = document.getElementById('rejectReason').value;
    const submitBtn = event.submitter;
    if (submitBtn) submitBtn.disabled = true;

    try {
        const response = await fetch(`/api/v1/applications/${appId}/reject?guild_id=${currentGuildId()}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reason })
        });
        if (!response.ok) {
            alert('Ошибка: ' + await readError(response));
            if (submitBtn) submitBtn.disabled = false;
            return;
        }
        const result = await response.json();
        const note = dmNote(result);
        if (note) alert('Анкета отклонена.' + note);
        window.location.reload();
    } catch (err) {
        console.error(err);
        alert('Не удалось подключиться к серверу');
        if (submitBtn) submitBtn.disabled = false;
    }
}

// --- Редактор вопросов анкеты ---

const MAX_QUESTIONS = 5;

function questionRowTemplate() {
    const row = document.createElement('div');
    row.className = 'question-row';
    row.innerHTML = `
        <div class="question-row-head">
            <span class="question-num"></span>
            <button type="button" class="action-btn delete" title="Удалить вопрос"><i class="fa-solid fa-trash"></i></button>
        </div>
        <div class="form-group">
            <label class="form-label">Вопрос (до 45 символов)</label>
            <input type="text" class="form-control q-label" maxlength="45" required>
        </div>
        <div class="form-group">
            <label class="form-label">Подсказка в поле (до 100 символов)</label>
            <input type="text" class="form-control q-placeholder" maxlength="100">
        </div>
        <div class="question-grid">
            <div class="form-group">
                <label class="form-label">Тип поля</label>
                <select class="form-control q-style">
                    <option value="short">Короткий ответ</option>
                    <option value="paragraph">Развёрнутый ответ</option>
                </select>
            </div>
            <div class="form-group">
                <label class="form-label">Мин. длина</label>
                <input type="number" class="form-control q-min" min="0" max="4000">
            </div>
            <div class="form-group">
                <label class="form-label">Макс. длина</label>
                <input type="number" class="form-control q-max" min="1" max="4000" required>
            </div>
        </div>
        <label class="custom-checkbox" style="display: inline-flex;">
            <input type="checkbox" class="q-required">
            <span class="checkmark"></span>
            <span class="role-name">Обязательный</span>
        </label>`;
    row.querySelector('.delete').addEventListener('click', () => {
        row.remove();
        refreshQuestionNumbers();
    });
    return row;
}

function refreshQuestionNumbers() {
    const rows = document.querySelectorAll('#questionsList .question-row');
    rows.forEach((row, i) => {
        row.querySelector('.question-num').textContent = `Вопрос ${i + 1}`;
        row.querySelector('.delete').disabled = rows.length <= 1;
    });
    const addBtn = document.getElementById('addQuestionBtn');
    if (addBtn) addBtn.disabled = rows.length >= MAX_QUESTIONS;
}

function addQuestion(q) {
    const list = document.getElementById('questionsList');
    if (list.children.length >= MAX_QUESTIONS) return;
    q = q || { label: '', placeholder: '', style: 'short', required: true, min_length: 0, max_length: 200 };

    const row = questionRowTemplate();
    row.querySelector('.q-label').value = q.label;
    row.querySelector('.q-placeholder').value = q.placeholder || '';
    row.querySelector('.q-style').value = q.style;
    row.querySelector('.q-min').value = q.min_length;
    row.querySelector('.q-max').value = q.max_length;
    row.querySelector('.q-required').checked = q.required;
    list.appendChild(row);
    refreshQuestionNumbers();
}

function collectQuestions() {
    return Array.from(document.querySelectorAll('#questionsList .question-row')).map((row) => ({
        label: row.querySelector('.q-label').value.trim(),
        placeholder: row.querySelector('.q-placeholder').value.trim(),
        style: row.querySelector('.q-style').value,
        required: row.querySelector('.q-required').checked,
        min_length: parseInt(row.querySelector('.q-min').value || '0', 10),
        max_length: parseInt(row.querySelector('.q-max').value || '1000', 10)
    }));
}

async function handleSaveApplicationSettings(event) {
    event.preventDefault();
    const payload = {
        enabled: document.getElementById('appEnabled').checked,
        approved_role_id: document.getElementById('appRole').value || null,
        review_channel_id: document.getElementById('appReviewChannel').value || null,
        title: document.getElementById('appTitle').value,
        description: document.getElementById('appDesc').value,
        button_label: document.getElementById('appButton').value,
        color: document.getElementById('appColor').value,
        banner_url: document.getElementById('appBanner').value || null,
        questions: collectQuestions(),
        dm_on_decision: document.getElementById('appDm').checked,
        approve_message: document.getElementById('appApproveMsg').value,
        reject_message: document.getElementById('appRejectMsg').value
    };

    try {
        const response = await fetch(`/api/v1/application-config?guild_id=${currentGuildId()}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (response.ok) {
            alert('✅ Настройки анкеты сохранены!');
            window.location.reload();
        } else {
            alert('Ошибка сохранения:\n' + await readError(response));
        }
    } catch (err) {
        console.error(err);
        alert('Не удалось подключиться к серверу');
    }
}

if (document.getElementById('questionsList') && Array.isArray(window.APP_QUESTIONS)) {
    window.APP_QUESTIONS.forEach((q) => addQuestion(q));
}
