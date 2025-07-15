"use client"

import { useState } from "react"
import { Home, LogOut, TrendingUp, BarChart3, MessageSquare, RotateCcw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useNavigate } from "react-router-dom"
import API from "../api/axios";
import Plot from 'react-plotly.js'; 

export default function Bot() {
  const [currentView, setCurrentView] = useState("initial") // 'initial', 'trending', 'analysis'
  const [selectedTicker, setSelectedTicker] = useState("")
  const [analysisData, setAnalysisData] = useState(null)

  // Mock data for trending stocks
  const trendingStocks = [
    { ticker: "AAPL", name: "Apple Inc.", change: +2.45, changePercent: +1.23 },
    { ticker: "GOOGL", name: "Alphabet Inc.", change: -1.87, changePercent: -0.65 },
    { ticker: "MSFT", name: "Microsoft Corp.", change: +3.21, changePercent: +0.89 },
    { ticker: "TSLA", name: "Tesla Inc.", change: +8.92, changePercent: +2.14 },
    { ticker: "AMZN", name: "Amazon.com Inc.", change: -2.33, changePercent: -1.45 },
  ]

  // Mock data for ticker options
  const tickerOptions = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA", "META", "NFLX", "AMD", "INTC"]
  

  const navigate = useNavigate();

  const handleHome = () => {
    // Navigate to Home component
    console.log("Navigating to Home...");
    setTimeout(navigate('/') ,1000);
  }

  const handleLogout = () => {
    // Handle logout
    console.log("Logging out...")
    alert("Logging out");
    setTimeout(navigate('/auth', 1000));
  }

  const handleGetTrending = () => {
    setCurrentView("trending")
  }

  const handleStartAnalysis = async () => {
    if (selectedTicker) {
        try {
            const requestBody = {
                query: "Should I buy this stock",
                ticker: selectedTicker
            };

            const response = await API.post("/query", requestBody);
            const backendData = response.data;
            console.log(backendData);

            // Reformat news data from object to array
            const formattedNews = Object.entries(backendData.sentiment.news_rating).map(
                ([title, [rating, url]]) => ({
                    title,
                    sentiment: rating,
                    url: url
                })
            );

            // Reconstruct the analysis data with formatted news
            // Note: The 'charts' key is gone. The figures and analysis_summary are now top-level.
            const analysisData = {
                ...backendData,
                sentiment: {
                    ...backendData.sentiment,
                    news: formattedNews,
                    overallSentiment: backendData.sentiment.investment_recommendation,
                    sentimentScore: backendData.sentiment.sentiment_score,
                    summary: backendData.sentiment.overall_news_summary
                }
            };

            setAnalysisData(analysisData);
            setCurrentView("analysis");

        } catch (error) {
            console.error("Error fetching analysis data:", error);
            setAnalysisData(null);
            alert("Failed to fetch analysis data. Please try again.");
        }
    }
};

  const handleNewAnalysis = () => {
    setCurrentView("initial")
    setSelectedTicker("")
    setAnalysisData(null)
  }

  const getSentimentColor = (sentiment) => {
    switch (sentiment.toLowerCase()) {
      case "positive":
        return "text-green-400"
      case "negative":
        return "text-red-400"
      case "neutral":
        return "text-yellow-400"
      default:
        return "text-gray-400"
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-green-900 to-black">
      {/* Header */}
      <header className="flex justify-end gap-3 p-6">
        <Button
          onClick={handleHome}
          variant="outline"
          className="bg-gray-800 border-green-800 text-white hover:bg-gray-700 hover:border-green-700 transition-all duration-200"
        >
          <Home className="w-4 h-4 mr-2" />
          Home
        </Button>
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
      <div className="flex flex-col items-center px-4 pb-12">
        <div className="w-full max-w-6xl">
          <Card className="bg-gray-900 border-green-800 shadow-2xl min-h-[600px]">
            <CardHeader className="text-center border-b border-gray-700">
              <CardTitle className="text-2xl font-bold text-white mb-2 flex items-center justify-center">
                <MessageSquare className="w-6 h-6 mr-2 text-green-400" />
                Trading Bot Analysis
              </CardTitle>
              <div className="flex justify-center">
                <Button
                  onClick={handleNewAnalysis}
                  variant="outline"
                  size="sm"
                  className="bg-gray-800 border-gray-600 text-gray-300 hover:bg-gray-700 hover:border-green-600"
                >
                  <RotateCcw className="w-4 h-4 mr-2" />
                  Refresh
                </Button>
              </div>
            </CardHeader>

            <CardContent className="p-8">
              {/* Initial View */}
              {currentView === "initial" && (
                <div className="space-y-8">
                  <div className="text-center">
                    <h3 className="text-xl font-semibold text-white mb-6">Choose an analysis option:</h3>
                  </div>

                  {/* Option 1: Get Trending Stocks */}
                  <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
                    <h4 className="text-lg font-medium text-white mb-3 flex items-center">
                      <TrendingUp className="w-5 h-5 mr-2 text-green-400" />
                      Get Trending Stock Tickers
                    </h4>
                    <p className="text-gray-400 mb-4">View the top 5 trending stocks with their current performance</p>
                    <Button
                      onClick={handleGetTrending}
                      className="bg-gradient-to-r from-green-600 to-green-800 text-white hover:from-green-700 hover:to-green-900 transition-all duration-200"
                    >
                      Get Trending Stocks
                    </Button>
                  </div>

                  {/* Option 2: Detailed Analysis */}
                  <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
                    <h4 className="text-lg font-medium text-white mb-3 flex items-center">
                      <BarChart3 className="w-5 h-5 mr-2 text-green-400" />
                      Detailed Stock Analysis
                    </h4>
                    <p className="text-gray-400 mb-4">
                      Select a ticker for comprehensive AI insights, charts, and finance news sentiment analysis
                    </p>
                    <div className="flex gap-4 items-end">
                      <div className="flex-1">
                        <label className="block text-sm font-medium text-gray-300 mb-2">Select Ticker</label>
                        <Select value={selectedTicker} onValueChange={setSelectedTicker}>
                          <SelectTrigger className="bg-gray-700 border-gray-600 text-white">
                            <SelectValue placeholder="Choose a stock ticker" />
                          </SelectTrigger>
                          <SelectContent className="bg-gray-800 border-gray-600">
                            {tickerOptions.map((ticker) => (
                              <SelectItem key={ticker} value={ticker} className="text-white hover:bg-gray-700">
                                {ticker}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <Button
                        onClick={handleStartAnalysis}
                        disabled={!selectedTicker}
                        className="bg-gradient-to-r from-green-600 to-green-800 text-white hover:from-green-700 hover:to-green-900 transition-all duration-200 disabled:opacity-50"
                      >
                        Start Analysis
                      </Button>
                    </div>
                  </div>
                </div>
              )}

              {/* Trending Stocks View */}
              {currentView === "trending" && (
                <div className="space-y-6">
                  <h3 className="text-xl font-semibold text-white text-center mb-6">Top 5 Trending Stocks</h3>
                  <div className="grid gap-4">
                    {trendingStocks.map((stock, index) => (
                      <div
                        key={stock.ticker}
                        className="bg-gray-800 border border-gray-700 rounded-lg p-4 hover:border-green-600 transition-all duration-200"
                      >
                        <div className="flex justify-between items-center">
                          <div>
                            <h4 className="text-lg font-semibold text-white">{stock.ticker}</h4>
                            <p className="text-gray-400 text-sm">{stock.name}</p>
                          </div>
                          <div className="text-right">
                            <p className={`text-lg font-bold ${stock.change >= 0 ? "text-green-400" : "text-red-400"}`}>
                              {stock.change >= 0 ? "+" : ""}
                              {stock.change.toFixed(2)}
                            </p>
                            <p className={`text-sm ${stock.changePercent >= 0 ? "text-green-400" : "text-red-400"}`}>
                              ({stock.changePercent >= 0 ? "+" : ""}
                              {stock.changePercent.toFixed(2)}%)
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Analysis Results View */}
              {currentView === "analysis" && analysisData && (
                <div className="space-y-6">
                  <h3 className="text-xl font-semibold text-white text-center mb-6">
                    Analysis Results for {selectedTicker}
                  </h3>

                  <Tabs defaultValue="insights" className="w-full">
                    <TabsList className="grid w-full grid-cols-3 bg-gray-800 border border-gray-700">
                      <TabsTrigger
                        value="insights"
                        className="data-[state=active]:bg-green-700 data-[state=active]:text-white"
                      >
                        AI Insights
                      </TabsTrigger>
                      <TabsTrigger
                        value="charts"
                        className="data-[state=active]:bg-green-700 data-[state=active]:text-white"
                      >
                        Charts
                      </TabsTrigger>
                      <TabsTrigger
                        value="sentiment"
                        className="data-[state=active]:bg-green-700 data-[state=active]:text-white"
                      >
                        Sentiment Analysis
                      </TabsTrigger>
                    </TabsList>

                    {/* AI Insights Tab */}
                    <TabsContent value="insights" className="mt-6">
                      <div className="grid lg:grid-cols-3 gap-6">
                        {/* Left Column - Analysis Fields */}
                        <div className="lg:col-span-2 space-y-6">
                          {/* Price Summary */}
                          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
                            <h4 className="text-lg font-semibold text-white mb-4 flex items-center">
                              <span className="mr-2">📈</span>
                              Price Summary
                            </h4>
                            <p className="text-gray-300 leading-relaxed">{analysisData.aiInsights.price_summary}</p>
                          </div>

                          {/* Trend Detection */}
                          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
                            <h4 className="text-lg font-semibold text-white mb-4 flex items-center">
                              <span className="mr-2">📈</span>
                              Trend Detection
                            </h4>
                            <p className="text-gray-300 leading-relaxed">{analysisData.aiInsights.trend_detection}</p>
                          </div>

                          {/* Technical Indicators */}
                          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
                            <h4 className="text-lg font-semibold text-white mb-4 flex items-center">
                              <span className="mr-2">📊</span>
                              Technical Indicators
                            </h4>
                            <p className="text-gray-300 leading-relaxed">
                              {analysisData.aiInsights.technical_indicators}
                            </p>
                          </div>

                          {/* Financial Metrics */}
                          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
                            <h4 className="text-lg font-semibold text-white mb-4 flex items-center">
                              <span className="mr-2">📉</span>
                              Financial Metrics
                            </h4>
                            <p className="text-gray-300 leading-relaxed">{analysisData.aiInsights.financial_metrics}</p>
                          </div>

                          {/* News Sentiment */}
                          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
                            <h4 className="text-lg font-semibold text-white mb-4 flex items-center">
                              <span className="mr-2">📰</span>
                              News Sentiment
                            </h4>
                            <p className="text-gray-300 leading-relaxed">{analysisData.aiInsights.news_sentiment}</p>
                          </div>
                        </div>

                        {/* Right Column - Investment Recommendation (Sticky) */}
                        <div className="lg:col-span-1">
                          <div className="sticky top-6">
                            <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
                              <h4 className="text-lg font-semibold text-white mb-4">Investment Recommendation</h4>

                              {/* Recommendation */}
                              <div className="bg-gray-700 rounded-lg p-4 mb-4">
                                <p className="text-sm text-gray-400 mb-2">Recommendation</p>
                                <p
                                  className={`text-2xl font-bold mb-3 ${
                                    analysisData.aiInsights.investment_recommendation.verdict === "BUY"
                                      ? "text-green-400"
                                      : analysisData.aiInsights.investment_recommendation.verdict === "SELL"
                                      ? "text-red-400"
                                      : "text-yellow-400"
                                  }`}
                                >
                                  {analysisData.aiInsights.investment_recommendation.verdict}
                                </p>
                                <p className="text-gray-300 text-sm leading-relaxed">
                                  {analysisData.aiInsights.investment_recommendation.reasoning}
                                </p>
                              </div>

                              {/* Target Price */}
                              <div className="bg-gray-700 rounded-lg p-4 mb-4">
                                <p className="text-sm text-gray-400 mb-2">Target Price</p>
                                <p className="text-xl font-bold text-white">{analysisData.aiInsights.targetPrice}</p>
                              </div>

                              {/* Stop Loss */}
                              <div className="bg-gray-700 rounded-lg p-4">
                                <p className="text-sm text-gray-400 mb-2">Stop Loss</p>
                                <p className="text-xl font-bold text-red-400">{analysisData.aiInsights.stopLoss}</p>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </TabsContent>

                    {/* Charts Tab
                    <TabsContent value="charts" className="mt-6">
                      <div className="space-y-6">
                        {analysisData.charts.map((chart) => (
                          <div key={chart.id} className="bg-gray-800 border border-gray-700 rounded-lg p-6">
                            <h4 className="text-lg font-semibold text-white mb-4">{chart.title}</h4>
                            <div className="bg-gray-700 rounded-lg p-4 min-h-[300px] flex items-center justify-center">
                              <div className="text-center">
                                <BarChart3 className="w-16 h-16 text-green-400 mx-auto mb-4" />
                                <p className="text-gray-400">Chart visualization would render here</p>
                                <p className="text-sm text-gray-500 mt-2">
                                  Plotly JSON: {JSON.stringify(chart.data).substring(0, 100)}...
                                </p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </TabsContent> */}


                                    {/* Charts Tab */}
                <TabsContent value="charts" className="mt-6">
                  <div className="space-y-6">
                    {/* Loop through the figures object and render each chart */}
                    {Object.keys(analysisData.figures).map((figKey) => {
                      const chartData = analysisData.figures[figKey];
                      return (
                        <div key={figKey} className="bg-gray-800 border border-gray-700 rounded-lg p-6">
                          <h4 className="text-lg font-semibold text-white mb-4">
                            {/* You can add a more user-friendly title here if needed */}
                            {figKey.replace(/_/g, ' ').toUpperCase()} Chart
                          </h4>
                          <div className="bg-gray-700 rounded-lg">
                            <Plot
                              data={chartData.data}
                              layout={{
                                ...chartData.layout,
                                plot_bgcolor: '#1f2937', // Tailwind gray-800
                                paper_bgcolor: '#1f2937', // Tailwind gray-800
                                font: {
                                  color: '#e5e7eb', // Tailwind gray-200
                                },
                                xaxis: {
                                  ...chartData.layout.xaxis,
                                  gridcolor: '#4b5563', // gray-600 for grid lines
                                },
                                yaxis: {
                                  ...chartData.layout.yaxis,
                                  gridcolor: '#4b5563',
                                },
                              }}
                              style={{ width: '100%', height: '100%' }}
                              useResizeHandler={true} // Makes the chart responsive
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </TabsContent>

                    {/* Sentiment Analysis Tab */}
                    <TabsContent value="sentiment" className="mt-6">
                      <div className="space-y-6">
                        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
                          <h4 className="text-lg font-semibold text-white mb-4">Overall Sentiment</h4>
                          <div className="grid md:grid-cols-2 gap-6">
                            <div>
                              <p className="text-sm text-gray-400 mb-2">Sentiment Score</p>
                              <p
                                className={`text-2xl font-bold ${analysisData.sentiment.sentimentScore >= 30 ? "text-green-400" : "text-red-400"}`}
                              >
                                {analysisData.sentiment.sentimentScore.toFixed(2)}
                              </p>
                            </div>
                            <div>
                              <p className="text-sm text-gray-400 mb-2">Overall Sentiment</p>
                              <p
                                className={`text-xl font-semibold ${getSentimentColor(analysisData.sentiment.overallSentiment)}`}
                              >
                                {analysisData.sentiment.overallSentiment}
                              </p>
                            </div>
                          </div>
                          <p className="text-gray-300 mt-4 leading-relaxed">{analysisData.sentiment.summary}</p>
                        </div>

                        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
                          <h4 className="text-lg font-semibold text-white mb-4">Recent News Analysis</h4>
                          <div className="space-y-3">
                            {analysisData.sentiment.news.map((item, index) => (
                              <div key={index} className="bg-gray-700 rounded-lg p-4 flex justify-between items-center">
                                <div className="flex-1">
                                  <p className="text-white font-medium">{item.title}</p>
                                </div>
                                <div className="text-right ml-4">
                                  <p className={`font-semibold ${getSentimentColor(item.sentiment)}`}>
                                    {item.sentiment}
                                  </p>
                                  {/* <p className="text-sm text-gray-400">Score: {item.score.toFixed(2)}</p> */}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    </TabsContent>
                  </Tabs>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}