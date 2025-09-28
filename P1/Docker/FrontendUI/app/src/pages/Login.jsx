import React from 'react'; 

export default function Login() {
  return (
    <div style={{maxWidth: 360, margin: "80px auto", padding: 24, border: "1px solid #ddd", borderRadius: 12}}>
      <h2 style={{marginBottom: 16}}>Login</h2>
      <form style={{display: "grid", gap: 12}}>
        <input placeholder="Username" />
        <input type="password" placeholder="Password" />
        <button type="button">Login</button>
      </form>
      <hr style={{margin: "16px 0"}} />
      <button type="button">Create new account</button>
    </div>
  );
}
