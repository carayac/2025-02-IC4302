import { api } from "../https";  

//Objeto que reune las funciones relacionadas a autenticación
export const AuthApi = {
  //User login
  login: (email, password) =>
    api("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),    //Body para el endpoint
    }),
  //User register
  register: ({ name, lastname, description = "", email, password }) =>
      api("/auth/register", {
        method: "POST",
        body: JSON.stringify({ name, lastname, description, email, password }),
      }),
  //Get registered user
  me: (id) => api(`/user/me?id=${encodeURIComponent(id)}`),

};

export const Prompts = {
  //Post a prompt
  postPrompt: (id_user, text ) =>
    api("/prompt/post", {
      method: "POST",
      body: JSON.stringify({ prompt: {id_user, text }}),
    }),

  //Get prompts to show in the feed
  getMyPrompts: (id_user) =>
    api(`/prompt/myprompts?id_user=${encodeURIComponent(id_user)}`)
};