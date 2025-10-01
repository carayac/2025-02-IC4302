import { API_BASE_URL } from "./config";


export async function api(path, opts = {}) {
  const headers = {
    "Content-Type": "application/json", //JSON body format
    ...(opts.headers || {}),
  };

  const res = await fetch(`${API_BASE_URL}${path}`, {   
    ...opts,    //metodos y body
    headers,
  });

  const isJson = res.headers.get("content-type")?.includes("application/json");
  const data = isJson ? await res.json() : null;    //Parsear jsons

  if (!res.ok) {
    const msg = data?.error || data?.message || `Error ${res.status}`;
    throw new Error(msg);
  }
  return data;
}
