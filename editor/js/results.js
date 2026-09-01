export function renderTrace(container, trace, nodeStatus, waiting, waitInfo) {
  if (!trace?.length && !waiting) {
    container.innerHTML = '<p class="run-meta">No trace yet. Run the program to see steps here.</p>';
    return;
  }

  let html = "";
  if (waiting) {
    html += `<p class="run-wait">Execution paused (${escapeHtml(waitInfo?.reason || "WAITING")}).`;
    if (waitInfo?.question) html += ` ${escapeHtml(waitInfo.question)}`;
    if (waitInfo?.options?.length) {
      html += ` Options: ${escapeHtml(waitInfo.options.join(", "))}.`;
    }
    html += "</p>";
  }
  html += '<ol class="trace-list">';
  for (const item of trace || []) {
    html += `<li><span class="trace-type trace-${item.type.toLowerCase()}">${escapeHtml(item.type)}</span> `;
    html += `<span class="trace-step">${escapeHtml(item.step)}</span> `;
    html += `<span class="trace-detail">${escapeHtml(item.detail)}</span></li>`;
  }
  html += "</ol>";
  if (nodeStatus?.length) {
    html += '<div class="node-status"><strong>Nodes</strong><ul>';
    for (const node of nodeStatus) {
      html += `<li><code>${escapeHtml(node.id)}</code> ${escapeHtml(node.operation)} — ${escapeHtml(node.status)}</li>`;
    }
    html += "</ul></div>";
  }
  container.innerHTML = html;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}
