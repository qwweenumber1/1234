async function loadOrders() {
    const email = document.getElementById("emailSearch").value;
    const res = await fetch(`/admin?email=${email}`, { credentials: "include" });
    const data = await res.json();
    const orders = data.orders || [];
    const list = document.getElementById("ordersList");
    list.innerHTML = "";
    orders.forEach(o => {
        const li = document.createElement("li");

        let dateStr = "Unknown date";
        if (o.created_at) {
            const d = new Date(o.created_at);
            const day = String(d.getDate()).padStart(2, '0');
            const month = String(d.getMonth() + 1).padStart(2, '0');
            const year = d.getFullYear();
            const hours = String(d.getHours()).padStart(2, '0');
            const mins = String(d.getMinutes()).padStart(2, '0');
            dateStr = `${day}.${month}.${year} ${hours}:${mins}`;
        }

        let statusColor = "status-new";
        if (o.status === "in progress") statusColor = "status-inprogress";
        if (o.status === "done") statusColor = "status-done";

        li.innerHTML = `
                    <div class="order-info">
                        <div><strong>Order #${o.id}</strong> by ${o.user_email}</div>
                        <div style="font-size: 1.1em; margin: 5px 0;">${o.description}</div>
                        <div class="meta">
                            <span class="status-Badge ${statusColor}">${o.status}</span>
                            ${o.color ? `<span class="badge">Color: ${o.color}</span>` : ''}
                            ${o.size ? `<span class="badge">Size: ${o.size}</span>` : ''}
                            <span>${dateStr}</span>
                        </div>
                        ${o.file_path ? `<div style="margin-top:5px;"><a href="/${o.file_path}" target="_blank">View File</a></div>` : ''}
                    </div>
                    
                    <div class="actions">
                        <select id="status-${o.id}">
                            <option value="new" ${o.status === 'new' ? 'selected' : ''}>New</option>
                            <option value="in progress" ${o.status === 'in progress' ? 'selected' : ''}>In Progress</option>
                            <option value="done" ${o.status === 'done' ? 'selected' : ''}>Done</option>
                        </select>
                        <button onclick="updateStatus(${o.id})">Update</button>
                        <button class="delete-btn" onclick="deleteOrder(${o.id})">Delete</button>
                    </div>
                `;
        list.appendChild(li);
    });
}

async function updateStatus(id) {
    const status = document.getElementById(`status-${id}`).value;
    const formData = new FormData();
    formData.append("status", status);
    const res = await fetch(`/admin/update_status/${id}`, { method: "POST", body: formData, credentials: "include" });
    if (res.ok) {
        alert("Status updated");
        loadOrders();
    } else {
        alert("Failed to update status");
    }
}

async function deleteOrder(id) {
    if (!confirm("Delete this order?")) return;
    const res = await fetch(`/admin/delete_order/${id}`, { method: "DELETE", credentials: "include" });
    if (res.ok) {
        loadOrders();
    } else {
        alert("Failed to delete");
    }
}

loadOrders();
