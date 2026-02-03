/**
 * Smart3D Orders Page Logic
 */

// We use a function to initialize the page logic, making it re-runnable for SPA
function initOrdersPage() {
    console.log("Initializing Orders Page");
    const form = document.getElementById("orderForm");
    if (!form) return;

    // Check user role & verification
    async function checkRole() {
        try {
            const res = await fetch("/me", { credentials: "include" });
            if (res.ok) {
                const user = await res.json();
                const vMsg = document.getElementById("verificationMessage");

                if (vMsg && !user.is_verified) {
                    vMsg.innerHTML = `
                        <div style="background: #fff3cd; color: #856404; padding: 20px; border-radius: 12px; border: 1px solid #ffeeba; margin-bottom: 20px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
                                <div>
                                    <strong>Email не підтверджено!</strong> Будь ласка, підтвердіть Email для створення замовлень.
                                </div>
                                <button id="resendBtn" onclick="resendEmail('${user.email}')" style="background: #856404; color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: bold; cursor: pointer;">
                                    Надіслати знову
                                </button>
                            </div>
                            <div id="resendStatus" style="font-size: 0.9em; margin-top: 10px;"></div>
                        </div>
                    `;
                    const pBtn = document.getElementById("previewBtn");
                    if (pBtn) {
                        pBtn.disabled = true;
                        pBtn.style.opacity = "0.5";
                        pBtn.title = "Підтвердіть Email";
                    }
                }

                if (user.role === "admin" && !document.getElementById("adminBtn")) {
                    const btn = document.createElement("button");
                    btn.id = "adminBtn";
                    btn.textContent = "⚙️ Адмін-панель";
                    btn.className = "primary-btn";
                    btn.style.cssText = "background: #334155; margin-bottom: 30px; border-radius: 12px;";
                    btn.onclick = () => {
                        if (window.appRouter) window.appRouter.navigateTo("/admin_page");
                        else window.location.href = "/admin_page";
                    };
                    document.querySelector(".orders-content").insertBefore(btn, document.querySelector(".orders-content").firstChild);
                }
            }
        } catch (e) { console.error(e); }
    }
    checkRole();

    // Confirmation Logic
    const previewBtn = document.getElementById("previewBtn");
    const confirmModal = document.getElementById("confirmModal");
    const closeConfirmBtn = document.getElementById("closeConfirmBtn");
    const finalSubmitBtn = document.getElementById("finalSubmitBtn");
    const predictedPriceElem = document.getElementById("predictedPrice");
    const orderSummaryElem = document.getElementById("orderSummary");

    if (previewBtn) {
        previewBtn.onclick = async () => {
            if (!form.checkValidity()) {
                form.reportValidity();
                return;
            }

            const formData = new FormData(form);
            const params = new URLSearchParams();
            for (const pair of formData.entries()) {
                if (typeof pair[1] === 'string' && pair[1].trim() !== '') {
                    params.append(pair[0], pair[1]);
                }
            }

            try {
                previewBtn.disabled = true;
                previewBtn.textContent = "⏳ Рахуємо...";

                const res = await fetch(`/calculate_price?${params.toString()}`);
                const data = await res.json();

                if (res.ok) {
                    predictedPriceElem.textContent = data.price;

                    const selectedInput = form.querySelector('input[name="material"]:checked');
                    const material = form.querySelector(`label[for="${selectedInput.id}"]`).childNodes[0].textContent.trim();
                    const colorLabel = form.querySelector('input[name="color"]:checked + label').textContent.trim();

                    orderSummaryElem.innerHTML = `
                        <div class="summary-item"><span>Опис:</span> <strong>${formData.get('description')}</strong></div>
                        <div class="summary-item"><span>Матеріал:</span> <strong>${material}</strong></div>
                        <div class="summary-item"><span>Колір:</span> <strong>${colorLabel}</strong></div>
                        <div class="summary-item"><span>Розміри:</span> <strong>${formData.get('width')}x${formData.get('length')}x${formData.get('height')} мм</strong></div>
                        <div class="summary-item"><span>Заповнення:</span> <strong>${formData.get('infill')}%</strong></div>
                        ${formData.get('real_weight') ? `<div class="summary-item"><span>Вага:</span> <strong>${formData.get('real_weight')} г</strong></div>` : ''}
                    `;

                    confirmModal.classList.add("active");
                } else {
                    alert("Помилка: " + (data.detail || "Невідома помилка"));
                }
            } catch (e) {
                alert("Помилка з'єднання");
            } finally {
                previewBtn.disabled = false;
                previewBtn.textContent = "Розрахувати та створити замовлення";
            }
        };
    }

    if (closeConfirmBtn) closeConfirmBtn.onclick = () => confirmModal.classList.remove("active");

    if (finalSubmitBtn) {
        finalSubmitBtn.onclick = async () => {
            finalSubmitBtn.disabled = true;
            finalSubmitBtn.textContent = "⌛ Оформлюємо...";

            const formData = new FormData(form);
            try {
                const res = await fetch("/create_order", { method: "POST", body: formData, credentials: "include" });
                if (res.ok) {
                    form.reset();
                    confirmModal.classList.remove("active");
                    loadOrders();
                } else {
                    const data = await res.json();
                    alert("Помилка: " + (data.detail || "Не вдалося створити замовлення"));
                }
            } catch (e) {
                alert("Помилка мережі");
            } finally {
                finalSubmitBtn.disabled = false;
                finalSubmitBtn.textContent = "Підтвердити замовлення";
            }
        };
    }

    // Orders List Logic
    async function loadOrders() {
        const res = await fetch("/orders", { credentials: "include" });
        const data = await res.json();
        const orders = data.orders || [];
        const list = document.getElementById("ordersList");
        if (!list) return;
        list.innerHTML = "";
        orders.sort((a, b) => b.id - a.id).forEach(o => {
            const li = document.createElement("li");

            let metaHtml = "";
            if (o.material) metaHtml += `<span class="badge material-badge">${o.material}</span>`;
            if (o.price) metaHtml += `<span class="badge price-badge">${o.price} грн</span>`;

            const statusMap = { "new": "Новий", "pending": "Очікує", "in progress": "В роботі", "done": "Готово", "canceled": "Скасовано" };
            const statusColors = { "new": "status-new", "pending": "status-pending", "in progress": "status-inprogress", "done": "status-done", "canceled": "status-canceled" };

            metaHtml += `<span class="status-badge ${statusColors[o.status] || 'status-new'}">${statusMap[o.status] || o.status}</span>`;

            let dateStr = o.created_at ? new Date(o.created_at).toLocaleString('uk-UA') : "---";

            li.innerHTML = `
                <div class="order-info">
                    <div><strong style="font-size: 1.1em;">Замовлення #${o.id}</strong></div>
                    <div style="margin: 3px 0;">${o.description}</div>
                    <div class="meta">${metaHtml} <span>${dateStr}</span></div>
                </div>
                <div style="display: flex; gap: 10px; align-items: center;">
                    ${o.file_path ? `<a href="/${o.file_path}" target="_blank" style="color: #4b8f3f; text-decoration: none; font-weight: bold; font-size: 0.9em;">📄 Файл</a>` : ''}
                    <button onclick="window.deleteOrder(${o.id})" style="background: #fee2e2; color: #dc2626; border: none; padding: 8px 12px; cursor: pointer; border-radius: 8px; font-weight: bold; font-size: 0.85em;">Видалити</button>
                </div>
            `;
            list.appendChild(li);
        });
    }

    // Delete Modal Logic
    const delModal = document.getElementById("deleteModal");
    function openDeleteModal(id) {
        window.orderIdToDelete = id;
        delModal.classList.add("active");
    }
    function closeDeleteModal() {
        window.orderIdToDelete = null;
        delModal.classList.remove("active");
    }

    document.getElementById("cancelBtn").onclick = closeDeleteModal;
    document.getElementById("confirmBtn").onclick = async () => {
        if (window.orderIdToDelete) {
            const res = await fetch(`/orders/${window.orderIdToDelete}`, { method: "DELETE", credentials: "include" });
            if (res.ok) loadOrders();
            closeDeleteModal();
        }
    };

    window.deleteOrder = openDeleteModal;
    loadOrders();
}

// Initial run
initOrdersPage();
