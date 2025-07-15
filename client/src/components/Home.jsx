import React from "react";
import { useNavigate } from "react-router-dom";


"use client"

import { LogOut, TrendingUp, BarChart3, Brain, DollarSign, AlertTriangle, Target } from "lucide-react"
import { Button } from "./UI/button"
import { Card, CardContent, CardHeader, CardTitle } from "./UI/card"

export default function Home() {

  const navigate = useNavigate();
  const handleLogout = () => {
    // Add logout logic here
    console.log("Logging out...");
    setTimeout(()=>{
        alert("Logging out");
        navigate("/auth");
    }, 1000)
  }

  const handleStartAnalysis = () => {
    // Add start analysis logic here
    console.log("Starting market analysis...");
    setTimeout(()=>{navigate('/bot')}, 1000);
  }

  const features = [
    {
      icon: <TrendingUp className="w-6 h-6" />,
      title: "Real-time Market Data",
      description: "Access live stock prices and market trends",
    },
    {
      icon: <Brain className="w-6 h-6" />,
      title: "AI-Powered Predictions",
      description: "Advanced machine learning algorithms for forecasting",
    },
    {
      icon: <BarChart3 className="w-6 h-6" />,
      title: "Technical Analysis",
      description: "Comprehensive chart analysis and indicators",
    },
    {
      icon: <DollarSign className="w-6 h-6" />,
      title: "Portfolio Optimization",
      description: "Smart recommendations for portfolio management",
    },
    {
      icon: <AlertTriangle className="w-6 h-6" />,
      title: "Risk Assessment",
      description: "Intelligent risk analysis and management tools",
    },
    {
      icon: <Target className="w-6 h-6" />,
      title: "Sentiment Analysis",
      description: "Market sentiment tracking from news and social media",
    },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-green-900 to-black overflow-hidden relative">
  {/* Header with Logout Button */}
  <header className="flex justify-end p-6">
    <Button
      onClick={handleLogout}
      variant="outline"
      className="bg-gray-800 border-green-800 text-white hover:bg-gray-700 hover:border-green-700 transition-all duration-200"
    >
      <LogOut className="w-4 h-4 mr-2" />
      Logout
    </Button>
  </header>

  {/* Main Content */}
  <div className="flex flex-col items-center justify-center px-4 pb-12 relative z-10">
    {/* Title Section */}
    <div className="text-center mb-12">
      <h1 className="text-5xl md:text-6xl font-bold text-white mb-4 tracking-tight">Trading Bot</h1>
      <p className="text-xl md:text-2xl text-gray-300 font-medium">
        Stock Market Forecasting and Sentiment Analysis
      </p>
    </div>

    {/* Features Card */}
    <div className="w-full max-w-4xl">
      <Card className="bg-gray-900 border-green-800 shadow-2xl">
        <CardHeader className="text-center pb-6">
          <CardTitle className="text-2xl font-bold text-white mb-2">Trading Bot Features</CardTitle>
          <p className="text-gray-400">Powerful tools for intelligent market analysis and trading decisions</p>
        </CardHeader>
        <CardContent className="p-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {features.map((feature, index) => (
              <div
                key={index}
                className="bg-gray-800 border border-gray-700 rounded-lg p-6 hover:border-green-600 transition-all duration-300 hover:transform hover:scale-105"
              >
                <div className="flex items-center mb-3">
                  <div className="text-green-400 mr-3">{feature.icon}</div>
                  <h3 className="text-white font-semibold text-lg">{feature.title}</h3>
                </div>
                <p className="text-gray-400 text-sm leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>

          {/* Start Analysis Button */}
          <div className="text-center">
            <Button
              onClick={handleStartAnalysis}
              className="bg-gradient-to-r from-green-600 to-green-800 text-white py-4 px-8 text-lg font-medium hover:from-green-700 hover:to-green-900 transform hover:scale-105 transition-all duration-200 shadow-lg"
              size="lg"
            >
              <BarChart3 className="w-5 h-5 mr-2" />
              Start Market Analysis
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>

  {/* Decorative elements */}
  <div className="absolute top-20 left-10 w-8 h-8 bg-green-500 rounded-full opacity-70"></div>
  <div className="absolute bottom-20 right-10 w-12 h-12 bg-green-600 rounded-full opacity-70"></div>
  <div className="absolute top-1/2 left-6 w-6 h-6 bg-green-400 rounded-full opacity-70"></div>
  <div className="absolute top-1/3 right-20 w-4 h-4 bg-green-300 rounded-full opacity-60"></div>
</div>

  );
}
