import React from "react";
import {BrowserRouter as Router, Routes, Route, Navigate} from "react-router-dom";
import Auth from "./components/Auth";
import Home from "./components/Home";
import Bot from "./components/Bot";


const isAuthenticated = () => {
  return !!localStorage.getItem("token");
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={isAuthenticated() ? <Home /> : <Navigate to="/auth" />} />
        <Route path="/auth" element={<Auth />} />
        <Route path="/signup" element={<Auth/>} />
        <Route path="/login" element={<Auth/>} />
        <Route path="/bot" element = {<Bot/>} />
      </Routes>
    </Router>
  );
}

export default App
