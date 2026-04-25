import { highlightConflict } from './renderer.js';

const WS_URL = "ws://localhost:8000/ws/threejs-observer";

export function connect(onConflict) {
  const status = document.getElementById("status");

  function open() {
    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      status.textContent = "Connected";
      status.style.color = "#4caf50";
    };

    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data);
        if (!msg.conflict_id) return;
        // Flash conflicting elements in the 3D scene.
        if (msg.elements?.length) highlightConflict(msg.elements);
        onConflict(msg);
      } catch (_) {}
    };

    ws.onclose = () => {
      status.textContent = "Disconnected — reconnecting…";
      status.style.color = "#ff7043";
      setTimeout(open, 3000);
    };

    ws.onerror = () => ws.close();
  }

  open();
}
