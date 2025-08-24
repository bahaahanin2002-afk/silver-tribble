"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { XAxis, YAxis, CartesianGrid, ResponsiveContainer, AreaChart, Area, BarChart, Bar } from "recharts"
import {
  TrendingUp,
  TrendingDown,
  Activity,
  DollarSign,
  Shield,
  Target,
  BarChart3,
  Clock,
  Zap,
  RefreshCw,
} from "lucide-react"

const performanceMetrics = {
  currentBalance: 52450.75,
  initialCapital: 50000,
  totalReturn: 4.9,
  dailyPnL: 234.5,
  dailyPnLPercent: 0.45,
  weeklyPnL: 1245.3,
  weeklyPnLPercent: 2.43,
  monthlyPnL: 2450.75,
  monthlyPnLPercent: 4.9,
  maxDrawdown: -3.2,
  winRate: 68.5,
  totalTrades: 247,
  winningTrades: 169,
  losingTrades: 78,
  avgWin: 145.3,
  avgLoss: -89.2,
  avgRiskReward: 1.63,
  sharpeRatio: 1.42,
  profitFactor: 2.18,
  activePositions: 3,
  lastUpdated: new Date().toISOString(),
}

const performanceHistory = [
  { date: "2024-01-01", balance: 50000, dailyPnL: 0, drawdown: 0, trades: 0 },
  { date: "2024-01-02", balance: 50210, dailyPnL: 210, drawdown: 0, trades: 3 },
  { date: "2024-01-03", balance: 49890, dailyPnL: -320, drawdown: -0.64, trades: 2 },
  { date: "2024-01-04", balance: 50450, dailyPnL: 560, drawdown: 0, trades: 4 },
  { date: "2024-01-05", balance: 50780, dailyPnL: 330, drawdown: 0, trades: 3 },
  { date: "2024-01-06", balance: 50620, dailyPnL: -160, drawdown: -0.32, trades: 2 },
  { date: "2024-01-07", balance: 51120, dailyPnL: 500, drawdown: 0, trades: 5 },
  { date: "2024-01-08", balance: 51450, dailyPnL: 330, drawdown: 0, trades: 3 },
  { date: "2024-01-09", balance: 51280, dailyPnL: -170, drawdown: -0.33, trades: 2 },
  { date: "2024-01-10", balance: 52450, dailyPnL: 1170, drawdown: 0, trades: 6 },
]

const tradeDistribution = [
  { range: "0-100", count: 45, percentage: 18.2 },
  { range: "100-300", count: 89, percentage: 36.0 },
  { range: "300-500", count: 67, percentage: 27.1 },
  { range: "500-1000", count: 32, percentage: 13.0 },
  { range: "1000+", count: 14, percentage: 5.7 },
]

const riskMetrics = [
  { name: "Daily Risk", current: 1.2, limit: 2.0, status: "safe" },
  { name: "Weekly Risk", current: 4.8, limit: 10.0, status: "safe" },
  { name: "Monthly Risk", current: 8.5, limit: 20.0, status: "warning" },
  { name: "Max Drawdown", current: 3.2, limit: 15.0, status: "safe" },
]

const strategyPerformance = [
  { name: "RSI Strategy", trades: 98, winRate: 72.4, pnl: 1245.3, status: "active" },
  { name: "ATR Breakout", trades: 76, winRate: 65.8, pnl: 890.45, status: "active" },
  { name: "Mean Reversion", trades: 45, winRate: 60.0, pnl: 234.5, status: "paused" },
  { name: "Momentum", trades: 28, winRate: 75.0, pnl: 80.5, status: "active" },
]

interface ComprehensivePerformanceDashboardProps {
  isArabic?: boolean
}

export function ComprehensivePerformanceDashboard({ isArabic = false }: ComprehensivePerformanceDashboardProps) {
  const [selectedTimeframe, setSelectedTimeframe] = useState("1M")
  const [isLiveMode, setIsLiveMode] = useState(true)
  const [lastUpdate, setLastUpdate] = useState(new Date())

  useEffect(() => {
    if (isLiveMode) {
      const interval = setInterval(() => {
        setLastUpdate(new Date())
      }, 30000) // Update every 30 seconds

      return () => clearInterval(interval)
    }
  }, [isLiveMode])

  const text = {
    en: {
      title: "Performance Analytics",
      subtitle: "Comprehensive trading performance metrics and analysis",
      currentBalance: "Current Balance",
      totalReturn: "Total Return",
      dailyPnL: "Daily P&L",
      weeklyPnL: "Weekly P&L",
      monthlyPnL: "Monthly P&L",
      maxDrawdown: "Max Drawdown",
      winRate: "Win Rate",
      totalTrades: "Total Trades",
      avgWin: "Avg Win",
      avgLoss: "Avg Loss",
      riskReward: "Risk/Reward",
      sharpeRatio: "Sharpe Ratio",
      profitFactor: "Profit Factor",
      overview: "Overview",
      detailed: "Detailed Analysis",
      risk: "Risk Analysis",
      strategies: "Strategy Performance",
      liveMode: "Live Mode",
      lastUpdate: "Last Update",
      refresh: "Refresh",
    },
    ar: {
      title: "تحليل الأداء",
      subtitle: "مقاييس وتحليل شامل لأداء التداول",
      currentBalance: "الرصيد الحالي",
      totalReturn: "إجمالي العائد",
      dailyPnL: "الربح/الخسارة اليومي",
      weeklyPnL: "الربح/الخسارة الأسبوعي",
      monthlyPnL: "الربح/الخسارة الشهري",
      maxDrawdown: "أقصى تراجع",
      winRate: "معدل الفوز",
      totalTrades: "إجمالي الصفقات",
      avgWin: "متوسط الربح",
      avgLoss: "متوسط الخسارة",
      riskReward: "المخاطرة/العائد",
      sharpeRatio: "نسبة شارب",
      profitFactor: "عامل الربح",
      overview: "نظرة عامة",
      detailed: "تحليل مفصل",
      risk: "تحليل المخاطر",
      strategies: "أداء الاستراتيجيات",
      liveMode: "الوضع المباشر",
      lastUpdate: "آخر تحديث",
      refresh: "تحديث",
    },
  }

  const t = isArabic ? text.ar : text.en

  return (
    <div className="space-y-6">
      {/* Header Controls */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-serif font-bold text-foreground">{t.title}</h2>
          <p className="text-muted-foreground">{t.subtitle}</p>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">
              {t.lastUpdate}: {lastUpdate.toLocaleTimeString()}
            </span>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsLiveMode(!isLiveMode)}
            className={`gap-2 ${isLiveMode ? "text-green-600" : ""}`}
          >
            <Zap className="h-4 w-4" />
            {t.liveMode}
          </Button>

          <Button variant="outline" size="sm" onClick={() => setLastUpdate(new Date())} className="gap-2">
            <RefreshCw className="h-4 w-4" />
            {t.refresh}
          </Button>
        </div>
      </div>

      {/* Key Performance Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-4">
        <Card className="bg-gradient-to-br from-primary/10 to-primary/5">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t.currentBalance}</CardTitle>
            <DollarSign className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-serif font-bold text-primary">
              ${performanceMetrics.currentBalance.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              <TrendingUp className="inline h-3 w-3 mr-1" />
              +${(performanceMetrics.currentBalance - performanceMetrics.initialCapital).toLocaleString()}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t.totalReturn}</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-serif font-bold text-accent">+{performanceMetrics.totalReturn}%</div>
            <Progress value={performanceMetrics.totalReturn * 2} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t.winRate}</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-serif font-bold text-chart-2">{performanceMetrics.winRate}%</div>
            <p className="text-xs text-muted-foreground">
              {performanceMetrics.winningTrades}W / {performanceMetrics.losingTrades}L
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t.maxDrawdown}</CardTitle>
            <TrendingDown className="h-4 w-4 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-serif font-bold text-destructive">{performanceMetrics.maxDrawdown}%</div>
            <p className="text-xs text-muted-foreground">Peak to trough</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t.sharpeRatio}</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-serif font-bold text-chart-3">{performanceMetrics.sharpeRatio}</div>
            <p className="text-xs text-muted-foreground">Risk-adjusted return</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t.profitFactor}</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-serif font-bold text-chart-4">{performanceMetrics.profitFactor}</div>
            <p className="text-xs text-muted-foreground">Gross profit / loss</p>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Analytics Tabs */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">{t.overview}</TabsTrigger>
          <TabsTrigger value="detailed">{t.detailed}</TabsTrigger>
          <TabsTrigger value="risk">{t.risk}</TabsTrigger>
          <TabsTrigger value="strategies">{t.strategies}</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Balance Evolution Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="font-serif">Balance Evolution</CardTitle>
                <CardDescription>Account balance over time</CardDescription>
              </CardHeader>
              <CardContent>
                <ChartContainer
                  config={{
                    balance: {
                      label: "Balance",
                      color: "hsl(var(--chart-1))",
                    },
                  }}
                  className="h-[300px]"
                >
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={performanceHistory}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis
                        dataKey="date"
                        stroke="hsl(var(--muted-foreground))"
                        fontSize={12}
                        tickFormatter={(value) => new Date(value).toLocaleDateString()}
                      />
                      <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                      <ChartTooltip content={<ChartTooltipContent />} />
                      <Area
                        type="monotone"
                        dataKey="balance"
                        stroke="hsl(var(--chart-1))"
                        fill="hsl(var(--chart-1))"
                        fillOpacity={0.2}
                        strokeWidth={2}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </ChartContainer>
              </CardContent>
            </Card>

            {/* Daily P&L Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="font-serif">Daily P&L</CardTitle>
                <CardDescription>Daily profit and loss breakdown</CardDescription>
              </CardHeader>
              <CardContent>
                <ChartContainer
                  config={{
                    dailyPnL: {
                      label: "Daily P&L",
                      color: "hsl(var(--chart-2))",
                    },
                  }}
                  className="h-[300px]"
                >
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={performanceHistory}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis
                        dataKey="date"
                        stroke="hsl(var(--muted-foreground))"
                        fontSize={12}
                        tickFormatter={(value) => new Date(value).toLocaleDateString()}
                      />
                      <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                      <ChartTooltip content={<ChartTooltipContent />} />
                      <Bar dataKey="dailyPnL" fill="hsl(var(--chart-2))" radius={[2, 2, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </ChartContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="detailed" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Trade Distribution */}
            <Card>
              <CardHeader>
                <CardTitle className="font-serif">Trade Size Distribution</CardTitle>
                <CardDescription>Distribution of trade sizes by profit range</CardDescription>
              </CardHeader>
              <CardContent>
                <ChartContainer
                  config={{
                    count: {
                      label: "Trades",
                      color: "hsl(var(--chart-3))",
                    },
                  }}
                  className="h-[300px]"
                >
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={tradeDistribution}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis dataKey="range" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                      <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                      <ChartTooltip content={<ChartTooltipContent />} />
                      <Bar dataKey="count" fill="hsl(var(--chart-3))" radius={[2, 2, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </ChartContainer>
              </CardContent>
            </Card>

            {/* Drawdown Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="font-serif">Drawdown Analysis</CardTitle>
                <CardDescription>Peak-to-trough drawdown over time</CardDescription>
              </CardHeader>
              <CardContent>
                <ChartContainer
                  config={{
                    drawdown: {
                      label: "Drawdown %",
                      color: "hsl(var(--destructive))",
                    },
                  }}
                  className="h-[300px]"
                >
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={performanceHistory}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis
                        dataKey="date"
                        stroke="hsl(var(--muted-foreground))"
                        fontSize={12}
                        tickFormatter={(value) => new Date(value).toLocaleDateString()}
                      />
                      <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                      <ChartTooltip content={<ChartTooltipContent />} />
                      <Area
                        type="monotone"
                        dataKey="drawdown"
                        stroke="hsl(var(--destructive))"
                        fill="hsl(var(--destructive))"
                        fillOpacity={0.2}
                        strokeWidth={2}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </ChartContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="risk" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Risk Metrics */}
            <Card>
              <CardHeader>
                <CardTitle className="font-serif">Risk Metrics</CardTitle>
                <CardDescription>Current risk levels vs limits</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {riskMetrics.map((metric, index) => (
                  <div key={index} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">{metric.name}</span>
                      <Badge variant={metric.status === "safe" ? "default" : "destructive"}>
                        {metric.current}% / {metric.limit}%
                      </Badge>
                    </div>
                    <Progress
                      value={(metric.current / metric.limit) * 100}
                      className={`h-2 ${metric.status === "warning" ? "bg-yellow-100" : ""}`}
                    />
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Performance Metrics Summary */}
            <Card>
              <CardHeader>
                <CardTitle className="font-serif">Performance Summary</CardTitle>
                <CardDescription>Key performance indicators</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-4 bg-muted/50 rounded-lg">
                    <div className="text-2xl font-bold text-primary">${performanceMetrics.avgWin}</div>
                    <div className="text-sm text-muted-foreground">Average Win</div>
                  </div>
                  <div className="text-center p-4 bg-muted/50 rounded-lg">
                    <div className="text-2xl font-bold text-destructive">${Math.abs(performanceMetrics.avgLoss)}</div>
                    <div className="text-sm text-muted-foreground">Average Loss</div>
                  </div>
                  <div className="text-center p-4 bg-muted/50 rounded-lg">
                    <div className="text-2xl font-bold text-accent">1:{performanceMetrics.avgRiskReward}</div>
                    <div className="text-sm text-muted-foreground">Risk/Reward</div>
                  </div>
                  <div className="text-center p-4 bg-muted/50 rounded-lg">
                    <div className="text-2xl font-bold text-chart-2">{performanceMetrics.totalTrades}</div>
                    <div className="text-sm text-muted-foreground">Total Trades</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="strategies" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {strategyPerformance.map((strategy, index) => (
              <Card key={index}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="font-serif">{strategy.name}</CardTitle>
                    <Badge variant={strategy.status === "active" ? "default" : "secondary"}>{strategy.status}</Badge>
                  </div>
                  <CardDescription>{strategy.trades} trades executed</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <div className="text-lg font-bold text-primary">{strategy.winRate}%</div>
                      <div className="text-xs text-muted-foreground">Win Rate</div>
                    </div>
                    <div>
                      <div className="text-lg font-bold text-accent">${strategy.pnl}</div>
                      <div className="text-xs text-muted-foreground">Total P&L</div>
                    </div>
                    <div>
                      <div className="text-lg font-bold text-chart-2">{strategy.trades}</div>
                      <div className="text-xs text-muted-foreground">Trades</div>
                    </div>
                  </div>
                  <Progress value={strategy.winRate} className="h-2" />
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
