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

  //edit user
  editUser: ({ id, name, lastname, description }) =>
    api("/user/edit", {
      method: "PUT",
      body: JSON.stringify({ id, name, lastname, description }),
    }),

  //change password
  changePassword: ({ id, oldpass, newpass }) =>
    api("/user/change-password", {
      method: "POST",
      body: JSON.stringify({ id, oldpass, newpass }),
    }),

};

export const Prompts = {
  //Post a prompt
  postPrompt: (id_user, text) =>
    api("/prompt/post", {
      method: "POST",
      body: JSON.stringify({ prompt: { id_user, text } }),
    }),

  //Get prompts to show in the feed
  getMyPrompts: (id_user) =>
    api(`/prompt/myprompts?id_user=${encodeURIComponent(id_user)}`),

  //Get my friends prompts
  getFeed: (id_user) =>
    api(`/prompt/feed?id_user=${encodeURIComponent(id_user)}`),

  //Search prompts using text and user name/lastname
  search: (text) =>
    api(`/prompt/search?text=${encodeURIComponent(text)}`),

  // edit prompt
  editPrompt: (id_prompt, text) =>
    api("/prompt/edit", {
      method: "PUT",
      body: JSON.stringify({ prompt: { id_prompt, text } }),
    }),

  // delete prompt
  deletePrompt: (id_prompt) =>
    api("/prompt/delete", {
      method: "PUT",
      body: JSON.stringify({ id_prompt }),
    }),
  
  //Generate search results for a prompt
  generatePrompt: (text) =>
    api("/prompt/generate", {
      method: "POST",
      body: JSON.stringify({ text }),
    }),

};

export const Likes = {
  //Like
  like: (id_user, id_prompt) =>
    api("/friend/like", {
      method: "POST",
      body: JSON.stringify({ id_user, id_prompt }),
    }),

  //Unlike
  unlike: (id_user, id_prompt) =>
    api("/friend/unlike", {
      method: "PUT",
      body: JSON.stringify({ id_user, id_prompt }),
    }),
};

export const Friends = {
  //Search people with name/lastname
  findFriend: (text) =>
    api(`/friend/find?text=${encodeURIComponent(text)}`),

  //Follow
  follow: (id_user, id_friend) =>
    api("/friend/follow", {
      method: "POST",
      body: JSON.stringify({ id_user, id_friend }),
    }),

  //Unfollow
  unfollow: (id_user, id_friend) =>
    api("/friend/unfollow", {
      method: "PUT",
      body: JSON.stringify({ id_user, id_friend }),
    }),

  //Get people I follow
  getMyFriends: (id_user) =>
    api(`/friend/get_friends?id=${encodeURIComponent(id_user)}`),

};