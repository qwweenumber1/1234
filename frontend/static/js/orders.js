const form = document.getElementById("orderForm");

// Check user role
async function checkRole() {
    try {
        const res = await fetch("/me", { credentials: "include" });
        if (res.ok) {
            const user = await res.json();

            // Verification check
            const vMsg = document.getElementById("verificationMessage");
            if (vMsg && !user.is_verified) {
                vMsg.innerHTML = `
                    <div style="background: #fff3cd; color: #856404; padding: 15px; border-radius: 8px; border: 1px solid #ffeeba; margin-bottom: 20px;">
                        <strong>Email не підтверджено!</strong> Будь ласка, перевірте пошту (або розділ сповіщень) для підтвердження акаунту. 
                        Ви не зможете створювати замовлення до підтвердження.
                    </div>
                `;
                if (form) {
                    const btn = form.querySelector("button[type='submit']");
                    if (btn) {
                        btn.disabled = true;
                        btn.style.opacity = "0.5";
                        btn.title = "Будь ласка, спочатку підтвердіть Email";
                    }
                }
            }

            if (user.role === "admin") {
                const btn = document.createElement("button");
                btn.textContent = "Перейти до адмін-панелі";
                btn.style.cssText = "background: #343a40; margin-bottom: 20px; width: 100%;";
                btn.onclick = () => window.location.href = "/admin_page";
                document.querySelector(".orders-content").insertBefore(btn, document.querySelector(".orders-content").firstChild);
            }
        }
    } catch (e) { console.error(e); }
}
checkRole();

form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(form);
    const res = await fetch("/create_order", { method: "POST", body: formData, credentials: "include" });
    const data = await res.json();
    if (res.ok) {
        form.reset();
        loadOrders();
    }
    else alert("Помилка: " + JSON.stringify(data));
});

async function loadOrders() {
    const res = await fetch("/orders", { credentials: "include" });
    const data = await res.json();
    const orders = data.orders || [];
    const list = document.getElementById("ordersList");
    list.innerHTML = "";
    orders.forEach(o => {
        const li = document.createElement("li");

        let metaHtml = "";
        if (o.color) metaHtml += `<span class="badge">Колір: ${o.color}</span>`;
        if (o.size) metaHtml += `<span class="badge">Розмір: ${o.size}</span>`;

        // Status Badge
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

        metaHtml += `<span class="status-badge ${statusColor}">${statusTitle}</span>`;

        // Better date formatting
        let dateStr = "Невідома дата";
        if (o.created_at) {
            const d = new Date(o.created_at);
            const day = String(d.getDate()).padStart(2, '0');
            const month = String(d.getMonth() + 1).padStart(2, '0');
            const year = d.getFullYear();
            const hours = String(d.getHours()).padStart(2, '0');
            const mins = String(d.getMinutes()).padStart(2, '0');
            dateStr = `${day}.${month}.${year} ${hours}:${mins}`;
        }

        li.innerHTML = `
            <div class="order-info">
                <div><strong>Замовлення #${o.id}</strong></div>
                <div style="font-size: 1.1em; margin: 5px 0;">${o.description}</div>
                <div class="meta">
                    ${metaHtml}
                    <span>${dateStr}</span>
                </div>
            </div>
            <div style="display: flex; gap: 10px; align-items: center;">
                ${o.file_path ? `<a href="/${o.file_path}" target="_blank">Файл</a>` : ''}
                <button onclick="deleteOrder(${o.id})" style="background: #dc3545; color: white; border: none; padding: 5px 10px; font-size: 0.9em; cursor: pointer; border-radius: 4px;">Видалити</button>
            </div>
        `;
        list.appendChild(li);
    });
}

let orderIdToDelete = null;
const modal = document.getElementById("deleteModal");
const confirmBtn = document.getElementById("confirmBtn");
const cancelBtn = document.getElementById("cancelBtn");

// Modal Event Listeners
cancelBtn.onclick = () => closeModal();
confirmBtn.onclick = async () => {
    if (orderIdToDelete) {
        await executeDelete(orderIdToDelete);
    }
    closeModal();
};

// Close on click outside
modal.onclick = (e) => {
    if (e.target === modal) closeModal();
};

function openModal(id) {
    orderIdToDelete = id;
    modal.classList.add("active");
}

function closeModal() {
    orderIdToDelete = null;
    modal.classList.remove("active");
}

async function deleteOrder(id) {
    openModal(id);
}

async function executeDelete(id) {
    const res = await fetch(`/orders/${id}`, { method: "DELETE", credentials: "include" });
    if (res.ok) {
        loadOrders();
    } else {
        const data = await res.json();
        alert("Помилка видалення: " + (data.detail || JSON.stringify(data)));
    }
}

loadOrders();
