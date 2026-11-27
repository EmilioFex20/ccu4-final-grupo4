const API = window.API_URL;
const $ = (id) => document.getElementById(id);
const money = (n) => `$${n.toFixed(2)} MXN`;
const STATUS = { pending: "Pendiente", preparing: "En preparación", ready: "Listo" };
let menu = [];

// Calls the API. Throws an Error with a readable message if something fails.
async function api(path, options) {
  let response;
  try {
    response = await fetch(API + path, options);
  } catch {
    throw new Error("No se pudo conectar con la API");
  }
  const data = await response.json().catch(() => null);
  if (!response.ok || data === null) {
    throw new Error(data?.message || `Error ${response.status}`);
  }
  return data;
}

// textContent (never innerHTML), so user text can't inject HTML.
function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function selectedItems() {
  return [...document.querySelectorAll("#menu input")]
    .map((input) => ({ item_id: Number(input.dataset.id), quantity: Number(input.value) }))
    .filter((item) => item.quantity > 0);
}

// Only a preview: the real total is always calculated by the API.
function updateEstimate() {
  const total = selectedItems().reduce(
    (sum, item) => sum + menu.find((m) => m.id === item.item_id).price * item.quantity, 0);
  $("estimate").textContent = money(total);
}

async function loadMenu() {
  try {
    menu = await api("/menu");
    $("menu").replaceChildren(...menu.map((item) => {
      const row = element("label", undefined, item.available ? "item" : "item unavailable");
      row.append(element("span", item.name), element("span", item.available ? money(item.price) : "Agotado"));
      const input = element("input");
      Object.assign(input, { type: "number", min: 0, max: 100, step: 1, defaultValue: 0, disabled: !item.available });
      input.dataset.id = item.id;
      input.addEventListener("input", updateEstimate);
      row.append(input);
      return row;
    }));
  } catch (error) {
    $("menu").textContent = `No se pudo cargar el menú: ${error.message}`;
  }
}

function showOrder(order) {
  const names = (id) => menu.find((m) => m.id === id)?.name || `Producto ${id}`;
  const list = element("ul");
  order.items.forEach((i) => list.append(element("li", `${i.quantity} × ${names(i.item_id)}`)));
  const parts = [
    element("h3", `Pedido #${order.id} de ${order.customer_name}`),
    list,
    element("p", `Total: ${money(order.total)}`),
    element("p", `Estado: ${STATUS[order.status] || order.status}`),
    element("p", `Recibo: ${order.receipt_status === "generated" ? "Generado" : "Pendiente"}`),
  ];
  if (order.receipt_url?.startsWith("https://")) {
    const link = element("a", "Ver recibo");
    Object.assign(link, { href: order.receipt_url, target: "_blank", rel: "noopener" });
    parts.push(link);
  }
  $("order-result").replaceChildren(...parts);
}

$("order-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = $("order-message");
  const items = selectedItems();
  if (items.length === 0) {
    message.textContent = "Elige al menos un producto.";
    return;
  }
  $("send").disabled = true; // avoids duplicate orders from double clicks
  message.textContent = "Enviando…";
  try {
    const order = await api("/orders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ customer_name: $("customer").value, items }),
    });
    message.textContent = `¡Pedido creado! Tu número es ${order.id}. Total: ${money(order.total)}`;
    $("order-id").value = order.id;
    event.target.reset();
    updateEstimate();
    showOrder(order);
  } catch (error) {
    message.textContent = error.message;
  } finally {
    $("send").disabled = false;
  }
});

$("status-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    showOrder(await api(`/orders/${encodeURIComponent($("order-id").value)}`));
  } catch (error) {
    $("order-result").textContent = error.message;
  }
});

loadMenu();
