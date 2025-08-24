"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { AuthSystem } from "@/components/auth-system"
import { SplashScreen } from "@/components/splash-screen"
import {
  TrendingUp,
  Activity,
  DollarSign,
  Shield,
  Bot,
  BarChart3,
  Play,
  Pause,
  AlertTriangle,
  CheckCircle,
  Globe,
} from "lucide-react"
import { ComprehensivePerformanceDashboard } from "@/components/comprehensive-performance-dashboard"
import { StrategyOverview } from "@/components/strategy-overview"
import { RecentTrades } from "@/components/recent-trades"
import { RiskManagement } from "@/components/risk-management"
import MultiExchangeDashboard from "@/components/multi-exchange-dashboard"
import BinanceTradingInterface from "@/components/binance-trading-interface"

export default function TradingDashboard() {
  const [isArabic, setIsArabic] = useState(false)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState<any>(null)
  const [showSplash, setShowSplash] = useState(true)
  const [isSystemRunning, setIsSystemRunning] = useState(true)
  const [performanceData, setPerformanceData] = useState({
    totalPnL: 12.45,
    winRate: 68.2,
    totalTrades: 247,
    activePositions: 3,
    dailyPnL: 2.34,
    weeklyPnL: 8.91,
  })

  const text = {
    en: {
      title: "AI Trading Bot Dashboard",
      subtitle: "Real-time performance monitoring and strategy management",
      totalPnL: "Total P&L",
      winRate: "Win Rate",
      totalTrades: "Total Trades",
      activePositions: "Active Positions",
      dailyPnL: "Daily P&L",
      weeklyPnL: "Weekly P&L",
      systemStatus: "System Status",
      running: "Running",
      stopped: "Stopped",
      strategies: "Strategies",
      performance: "Performance",
      trades: "Recent Trades",
      riskManagement: "Risk Management",
      exchanges: "Global Exchanges",
      binanceTrading: "Binance Trading",
      startSystem: "Start System",
      stopSystem: "Stop System",
      language: "العربية",
    },
    ar: {
      title: "لوحة تحكم روبوت التداول الذكي",
      subtitle: "مراقبة الأداء في الوقت الفعلي وإدارة الاستراتيجيات",
      totalPnL: "إجمالي الربح/الخسارة",
      winRate: "معدل الفوز",
      totalTrades: "إجمالي الصفقات",
      activePositions: "المراكز النشطة",
      dailyPnL: "الربح/الخسارة اليومي",
      weeklyPnL: "الربح/الخسارة الأسبوعي",
      systemStatus: "حالة النظام",
      running: "يعمل",
      stopped: "متوقف",
      strategies: "الاستراتيجيات",
      performance: "الأداء",
      trades: "الصفقات الأخيرة",
      riskManagement: "إدارة المخاطر",
      exchanges: "المنصات العالمية",
      binanceTrading: "تداول Binance",
      startSystem: "تشغيل النظام",
      stopSystem: "إيقاف النظام",
      language: "English",
    },
  }

  const t = isArabic ? text.ar : text.en

  const handleAuthSuccess = (userData: any) => {
    console.log("[v0] Authentication successful:", userData)
    setUser(userData)
    setIsAuthenticated(true)
  }

  if (showSplash) {
    return (
      <SplashScreen
        isArabic={isArabic}
        onLogin={() => setShowSplash(false)}
        onRegister={() => setShowSplash(false)}
        onLanguageToggle={() => setIsArabic(!isArabic)}
      />
    )
  }

  // Show auth system if not authenticated
  if (!isAuthenticated) {
    return <AuthSystem isArabic={isArabic} onAuthSuccess={handleAuthSuccess} />
  }

  return (
    <div className={`min-h-screen bg-background ${isArabic ? "rtl" : "ltr"}`}>
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Bot className="h-8 w-8 text-primary" />
              <div>
                <h1 className="text-2xl font-serif font-bold text-foreground">{t.title}</h1>
                <p className="text-sm text-muted-foreground">{t.subtitle}</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {/* Language Toggle */}
              <div className="flex items-center gap-2">
                <Globe className="h-4 w-4 text-muted-foreground" />
                <Button variant="outline" size="sm" onClick={() => setIsArabic(!isArabic)} className="text-xs">
                  {t.language}
                </Button>
              </div>

              {/* System Status */}
              <div className="flex items-center gap-2">
                <Badge variant={isSystemRunning ? "default" : "destructive"} className="gap-1">
                  {isSystemRunning ? <CheckCircle className="h-3 w-3" /> : <AlertTriangle className="h-3 w-3" />}
                  {isSystemRunning ? t.running : t.stopped}
                </Badge>

                <Button
                  variant={isSystemRunning ? "destructive" : "default"}
                  size="sm"
                  onClick={() => setIsSystemRunning(!isSystemRunning)}
                  className="gap-2"
                >
                  {isSystemRunning ? (
                    <>
                      <Pause className="h-4 w-4" />
                      {t.stopSystem}
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4" />
                      {t.startSystem}
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{t.totalPnL}</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-serif font-bold text-primary">+{performanceData.totalPnL}%</div>
              <p className="text-xs text-muted-foreground">
                <TrendingUp className="inline h-3 w-3 mr-1" />
                +2.1% from last month
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{t.winRate}</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-serif font-bold text-accent">{performanceData.winRate}%</div>
              <Progress value={performanceData.winRate} className="mt-2" />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{t.totalTrades}</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-serif font-bold">{performanceData.totalTrades}</div>
              <p className="text-xs text-muted-foreground">+12 this week</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{t.activePositions}</CardTitle>
              <Shield className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-serif font-bold text-chart-2">{performanceData.activePositions}</div>
              <p className="text-xs text-muted-foreground">2 BTC, 1 ETH</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{t.dailyPnL}</CardTitle>
              <TrendingUp className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-serif font-bold text-primary">+{performanceData.dailyPnL}%</div>
              <p className="text-xs text-muted-foreground">Today's performance</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{t.weeklyPnL}</CardTitle>
              <TrendingUp className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-serif font-bold text-primary">+{performanceData.weeklyPnL}%</div>
              <p className="text-xs text-muted-foreground">This week's performance</p>
            </CardContent>
          </Card>
        </div>

        {/* Main Dashboard Tabs */}
        <Tabs defaultValue="performance" className="space-y-6">
          <TabsList className="grid w-full grid-cols-6">
            <TabsTrigger value="performance">{t.performance}</TabsTrigger>
            <TabsTrigger value="strategies">{t.strategies}</TabsTrigger>
            <TabsTrigger value="trades">{t.trades}</TabsTrigger>
            <TabsTrigger value="risk">{t.riskManagement}</TabsTrigger>
            <TabsTrigger value="exchanges">{t.exchanges}</TabsTrigger>
            <TabsTrigger value="binance">{t.binanceTrading}</TabsTrigger>
          </TabsList>

          <TabsContent value="performance" className="space-y-6">
            <ComprehensivePerformanceDashboard isArabic={isArabic} />
          </TabsContent>

          <TabsContent value="strategies" className="space-y-6">
            <StrategyOverview isArabic={isArabic} />
          </TabsContent>

          <TabsContent value="trades" className="space-y-6">
            <RecentTrades isArabic={isArabic} />
          </TabsContent>

          <TabsContent value="risk" className="space-y-6">
            <RiskManagement isArabic={isArabic} />
          </TabsContent>

          <TabsContent value="exchanges" className="space-y-6">
            <MultiExchangeDashboard />
          </TabsContent>

          <TabsContent value="binance" className="space-y-6">
            <BinanceTradingInterface />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
