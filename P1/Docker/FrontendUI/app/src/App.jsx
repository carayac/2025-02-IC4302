import React from 'react';
import { BrowserRouter, Routes, Route } from "react-router-dom";

import Index from "./pages/Login/Index.jsx";
import Register from "./pages/Register/Register.jsx";
import Ask from "./pages/Ask/Ask.jsx";
import Prompt from "./pages/Prompt/Prompt.jsx";
import Friends from "./pages/Friends/Friends.jsx";
import Feed from "./pages/Feed/Feed.jsx";
import Me from "./pages/Me/Me.jsx";
import MyFriends from "./pages/MyFriends/MyFriends.jsx";

/* export default function App() { 
    return <Friends />; 
} */



export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Index />} />
        <Route path="/feed" element={<Feed />} />
        <Route path="/register" element={<Register />} />
        <Route path="/ask" element={<Ask />} />
        <Route path="/prompt" element={<Prompt />} />
        <Route path="/friends" element={<Friends />} />
        <Route path="/myFriends" element={<MyFriends />} />
        <Route path="/me" element={<Me />} />
      </Routes>
    </BrowserRouter>
  );
}
