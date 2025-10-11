import { API_BASE_URL } from "./config";  //Dirección URL base


export async function api(path, opts = {}) {
  const headers = {
    "Content-Type": "application/json", //JSON body format
    ...(opts.headers || {}),
  };

  const res = await fetch(`${API_BASE_URL}${path}`, {   
    ...opts,    
    headers,
  });

  const isJson = res.headers.get("content-type")?.includes("application/json"); //Verificación de datos json
  const data = isJson ? await res.json() : null;    //lectura de jsons

  if (!res.ok) {
    const msg = data?.error || data?.message || `Error ${res.status}`;
    throw new Error(msg);
  }
  return data;
}
