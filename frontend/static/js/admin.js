/**
 * Smart3D Admin Page Logic
 */

function initAdminPage() {
    console.log("Initializing Admin Page");
    const list = document.getElementById("ordersList");
    if (!list) return;

    const emailSearch = document.getElementById("emailSearch");
    const sendSearchBtn = document.querySelector(".controls button:nth-child(2)");

    if (sendSearchBtn) {
        sendSearchBtn.onclick = () => loadOrders();
    }

    if (emailSearch) {
        emailSearch.onkeypress = (e) => {
            if (e.key === 'Enter') loadOrders();
        };
    }

    async function loadOrders() {
        const email = emailSearch ? emailSearch.value : "";
        const res = await fetch(`/admin?email=${email}`, { credentials: "include" });
        const data = await res.json();
        const orders = data.orders || [];

        list.innerHTML = "";
        orders.sort((a, b) => b.id - a.id).forEach(o => {
            const li = document.createElement("li");

            let dateStr = o.created_at ? new Date(o.created_at).toLocaleString('uk-UA') : "---";

            const statusMap = {
                "new": "Новий",
                "in progress": "В роботі",
                "done": "Готово",
                "canceled": "Скасовано"
            };
            let statusColor = "status-new";
            if (o.status === "in progress") statusColor = "status-inprogress";
            if (o.status === "done") statusColor = "status-done";
            if (o.status === "canceled") statusColor = "status-canceled";

            let statusTitle = statusMap[o.status] || o.status;

            li.innerHTML = `
                <div class="order-info">
                    <div><strong style="color: #4b8f3f; font-size: 1.25em;">Замовлення #${o.id}</strong> від <span style="color: #666;">${o.user_email}</span></div>
                    <div style="font-size: 1.1em; margin: 8px 0; font-weight: 500;">${o.description}</div>
                    <div class="meta">
                        <span class="status-badge ${statusColor}">${statusTitle}</span>
                        ${o.color ? `<span class="badge">Колір: ${o.color}</span>` : ''}
                        ${o.size ? `<span class="badge">Розмір: ${o.size}</span>` : ''}
                        <span>${dateStr}</span>
                    </div>
                    ${o.file_path ? `<div style="margin-top:10px;"><a href="/${o.file_path}" target="_blank" style="color: #4b8f3f; font-weight: bold; text-decoration: none;">Переглянути файл</a></div>` : ''}
                </div>
                
                <div class="actions" style="margin-top: 15px;">
                    <select id="status-${o.id}" style="padding: 8px; border-radius: 8px; border: 1px solid #ddd;">
                        <option value="new" ${o.status === 'new' ? 'selected' : ''}>Новий</option>
                        <option value="in progress" ${o.status === 'in progress' ? 'selected' : ''}>В роботі</option>
                        <option value="done" ${o.status === 'done' ? 'selected' : ''}>Готово</option>
                        <option value="canceled" ${o.status === 'canceled' ? 'selected' : ''}>Скасовано</option>
                    </select>
                    <button onclick="window.requestUpdate(${o.id})" style="background: #a3d392; color: white; padding: 8px 16px; border-radius: 8px; font-weight: bold; cursor: pointer;">Оновити</button>
                    <button class="delete-btn" onclick="window.requestDelete(${o.id})" style="background: #dc3545; color: white; padding: 8px 16px; border-radius: 8px; font-weight: bold; cursor: pointer;">Видалити</button>
                </div>
            `;
            list.appendChild(li);
        });
    }

    const deleteModal = document.getElementById("deleteModal");
    const updateModal = document.getElementById("updateModal");

    window.requestDelete = function (id) {
        window.currentOrderId = id;
        deleteModal.classList.add("active");
    };

    window.requestUpdate = function (id) {
        window.currentOrderId = id;
        updateModal.classList.add("active");
    };

    function closeModals() {
        window.currentOrderId = null;
        if (deleteModal) deleteModal.classList.remove("active");
        if (updateModal) updateModal.classList.remove("active");
    }

    if (document.getElementById("cancelDeleteBtn")) document.getElementById("cancelDeleteBtn").onclick = closeModals;
    if (document.getElementById("cancelUpdateBtn")) document.getElementById("cancelUpdateBtn").onclick = closeModals;

    if (document.getElementById("confirmDeleteBtn")) {
        document.getElementById("confirmDeleteBtn").onclick = async () => {
            if (!window.currentOrderId) return;
            const res = await fetch(`/admin/delete_order/${window.currentOrderId}`, { method: "DELETE", credentials: "include" });
            if (res.ok) {
                loadOrders();
            } else {
                alert("Помилка видалення");
            }
            closeModals();
        };
    }

    if (document.getElementById("confirmUpdateBtn")) {
        document.getElementById("confirmUpdateBtn").onclick = async () => {
            if (!window.currentOrderId) return;
            const status = document.getElementById(`status-${window.currentOrderId}`).value;
            const formData = new FormData();
            formData.append("status", status);
            const res = await fetch(`/admin/update_status/${window.currentOrderId}`, { method: "POST", body: formData, credentials: "include" });
            if (res.ok) {
                loadOrders();
            } else {
                alert("Не вдалося оновити статус");
            }
            closeModals();
        };
    }

    // Modal background clicks
    [deleteModal, updateModal].forEach(m => {
        if (m) m.onclick = (e) => { if (e.target === m) closeModals(); };
    });

    loadOrders();
}

// Initial run
initAdminPage();
