import React from 'react';
import { BrowserRouter, Routes, Route } from "react-router-dom";

import Login from "./pages/Login/Login.jsx";
import Register from "./pages/Register/Register.jsx";
import Ask from "./pages/Ask/Ask.jsx";

export default function App() { 
    return <Ask />; 
}


// export default function App() {
//   return (
//     <BrowserRouter>
//       <Routes>
//         {}
//         <Route path="/login" element={<Login />} />

//         {}
//         <Route path="/register" element={<Register />} />

//         {}
//         <Route path="/" element={<Login />} />
//       </Routes>
//     </BrowserRouter>
//   );
// }