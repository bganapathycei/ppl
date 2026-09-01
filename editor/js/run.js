export async function runProgram(source, options = {}) {
  const body = {
    source,
    trace: options.trace !== false,
  };
  if (options.input != null) body.input = options.input;
  if (options.executionId) body.execution_id = options.executionId;
  if (options.humanDecision) body.human_decision = options.humanDecision;

  try {
    const response = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await response.json();
    if (data && typeof data === "object") {
      return { fromServer: true, status: response.status, ...data };
    }
    return { fromServer: true, ok: false, error: "Invalid server response" };
  } catch (err) {
    return { fromServer: false, ok: false, error: String(err.message || err) };
  }
}

export function formatResult(result) {
  if (result == null) return "null";
  if (typeof result === "string") return JSON.stringify(result);
  return JSON.stringify(result, null, 2);
}
