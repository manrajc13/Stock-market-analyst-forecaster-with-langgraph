import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

import API from "../api/axios";


const SlidingAuth = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [loginForm, setLoginForm] = useState({ email: "", password: "" });
  const [signupForm, setSignupForm] = useState({ email: "", name: "", password: "" });
  const [loginError, setLoginError] = useState("");
  const [signupMessage, setSignupMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();


  const handleLoginChange = (e) => {
    setLoginForm({ ...loginForm, [e.target.name]: e.target.value });
    setLoginError("");
  };

  const handleSignupChange = (e) => {
    setSignupForm({ ...signupForm, [e.target.name]: e.target.value });
    setSignupMessage("");
  };

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
        const res = await API.post("/login", loginForm);
        console.log(res.data.access_token);
        localStorage.setItem("token", res.data.access_token);
        alert("Login successful! Token saved.");
        navigate("/");
    } catch (err) {
      setLoginError(err.response?.data?.detail || "Login failed.");
    }
    setLoading(false);
  };

  const handleSignupSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await API.post("/register", signupForm);
      setSignupMessage("Signup successful! Please log in.");
      // Auto-switch to login after successful signup
      setTimeout(() => {
        setIsLogin(true);
        setSignupMessage("");
      }, 2000);
    } catch (err) {
      setSignupMessage(err.response?.data?.detail || "Signup failed.");
    }
    setLoading(false);
  };

  const toggleForm = () => {
    setIsLogin(!isLogin);
    setLoginError("");
    setSignupMessage("");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-green-900 to-black flex items-center justify-center p-4">
      <div className="relative w-full max-w-md">
        {/* Container with sliding panels */}
        <div className="relative bg-gray-900 rounded-2xl shadow-2xl overflow-hidden border border-green-800">
          {/* Toggle buttons */}
          <div className="flex relative z-10">
            <button
              onClick={() => setIsLogin(true)}
              className={`flex-1 py-3 px-6 text-sm font-medium transition-all duration-300 ${
                isLogin 
                  ? 'text-white bg-gradient-to-r from-green-600 to-green-800' 
                  : 'text-gray-400 bg-gray-800 hover:bg-gray-700'
              }`}
            >
              Login
            </button>
            <button
              onClick={() => setIsLogin(false)}
              className={`flex-1 py-3 px-6 text-sm font-medium transition-all duration-300 ${
                !isLogin 
                  ? 'text-white bg-gradient-to-r from-green-600 to-green-800' 
                  : 'text-gray-400 bg-gray-800 hover:bg-gray-700'
              }`}
            >
              Sign Up
            </button>
          </div>

          {/* Sliding forms container */}
          <div className="relative overflow-hidden">
            <div 
              className={`flex transition-transform duration-500 ease-in-out ${
                isLogin ? 'translate-x-0' : '-translate-x-1/2'
              }`}
              style={{ width: '200%' }}
            >
              {/* Login Form */}
              <div className="w-1/2 p-8">
                <div className="text-center mb-8">
                  <h2 className="text-2xl font-bold text-white mb-2">Welcome Back!</h2>
                  <p className="text-gray-400">Sign in to your account</p>
                </div>
                
                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Email Address
                    </label>
                    <input
                      name="email"
                      type="email"
                      value={loginForm.email}
                      onChange={handleLoginChange}
                      className="w-full px-4 py-3 border border-gray-700 bg-gray-800 text-white rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200"
                      placeholder="Enter your email"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Password
                    </label>
                    <input
                      name="password"
                      type="password"
                      value={loginForm.password}
                      onChange={handleLoginChange}
                      className="w-full px-4 py-3 border border-gray-700 bg-gray-800 text-white rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200"
                      placeholder="Enter your password"
                      required
                    />
                  </div>
                  
                  {loginError && (
                    <div className="bg-red-900 border border-red-700 text-red-300 px-4 py-3 rounded-lg">
                      {loginError}
                    </div>
                  )}
                  
                  <button
                    type="submit"
                    onClick={(e) => {
                      e.preventDefault();
                      handleLoginSubmit(e);
                    }}
                    disabled={loading}
                    className="w-full bg-gradient-to-r from-green-600 to-green-800 text-white py-3 px-4 rounded-lg font-medium hover:from-green-700 hover:to-green-900 transform hover:scale-105 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                  >
                    {loading ? (
                      <div className="flex items-center justify-center">
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                        Signing in...
                      </div>
                    ) : (
                      'Sign In'
                    )}
                  </button>
                </div>
                
                <div className="mt-6 text-center">
                  <p className="text-gray-400">
                    Don't have an account?{' '}
                    <button
                      onClick={toggleForm}
                      className="text-green-400 hover:text-green-300 font-medium transition-colors duration-200"
                    >
                      Sign up here
                    </button>
                  </p>
                </div>
              </div>

              {/* Signup Form */}
              <div className="w-1/2 p-8">
                <div className="text-center mb-8">
                  <h2 className="text-2xl font-bold text-white mb-2">Create Account</h2>
                  <p className="text-gray-400">Join us today</p>
                </div>
                
                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Full Name
                    </label>
                    <input
                      name="name"
                      type="text"
                      value={signupForm.name}
                      onChange={handleSignupChange}
                      className="w-full px-4 py-3 border border-gray-700 bg-gray-800 text-white rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200"
                      placeholder="Enter your full name"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Email Address
                    </label>
                    <input
                      name="email"
                      type="email"
                      value={signupForm.email}
                      onChange={handleSignupChange}
                      className="w-full px-4 py-3 border border-gray-700 bg-gray-800 text-white rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200"
                      placeholder="Enter your email"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Password
                    </label>
                    <input
                      name="password"
                      type="password"
                      value={signupForm.password}
                      onChange={handleSignupChange}
                      className="w-full px-4 py-3 border border-gray-700 bg-gray-800 text-white rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200"
                      placeholder="Create a password"
                      required
                    />
                  </div>
                  
                  {signupMessage && (
                    <div className={`px-4 py-3 rounded-lg ${
                      signupMessage.includes('successful') 
                        ? 'bg-green-900 border border-green-700 text-green-300'
                        : 'bg-red-900 border border-red-700 text-red-300'
                    }`}>
                      {signupMessage}
                    </div>
                  )}
                  
                  <button
                    type="submit"
                    onClick={(e) => {
                      e.preventDefault();
                      handleSignupSubmit(e);
                    }}
                    disabled={loading}
                    className="w-full bg-gradient-to-r from-green-600 to-green-800 text-white py-3 px-4 rounded-lg font-medium hover:from-green-700 hover:to-green-900 transform hover:scale-105 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                  >
                    {loading ? (
                      <div className="flex items-center justify-center">
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                        Creating account...
                      </div>
                    ) : (
                      'Create Account'
                    )}
                  </button>
                </div>
                
                <div className="mt-6 text-center">
                  <p className="text-gray-400">
                    Already have an account?{' '}
                    <button
                      onClick={toggleForm}
                      className="text-green-400 hover:text-green-300 font-medium transition-colors duration-200"
                    >
                      Sign in here
                    </button>
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Decorative elements */}
        <div className="absolute -top-4 -left-4 w-8 h-8 bg-green-500 rounded-full opacity-70"></div>
        <div className="absolute -bottom-4 -right-4 w-12 h-12 bg-green-600 rounded-full opacity-70"></div>
        <div className="absolute top-1/2 -right-6 w-6 h-6 bg-green-400 rounded-full opacity-70"></div>
      </div>
    </div>
  );
};

export default SlidingAuth;