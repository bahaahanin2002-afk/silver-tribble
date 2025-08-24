"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { TrendingUp, Activity, DollarSign, BarChart3, RefreshCw, AlertTriangle, CheckCircle, Globe } from "lucide-react"

interface ExchangeBalance {
  currency: string
  available: number
  locked: number
  total: number
}

interface ExchangeData {
  name: string
  status: "connected" | "disconnected" | "error"
  balances: ExchangeBalance[]
  totalValue: number
  lastUpdate: string
}

interface ArbitrageOpportunity {
  symbol: string
  buyExchange: string
  sellExchange: string
  buyPrice: number
  sellPrice: number
  profit: number
  profitPercent: number
}

export default function MultiExchangeDashboard() {
  const [exchanges, setExchanges] = useState<ExchangeData[]>([
    {
      name: "Binance",
      status: "connected",
      balances: [
        { currency: "BTC", available: 0.5, locked: 0.0, total: 0.5 },
        { currency: "ETH", available: 2.0, locked: 0.0, total: 2.0 },
        { currency: "USDT", available: 5000, locked: 0.0, total: 5000 },
      ],
      totalValue: 31500,
      lastUpdate: "2 دقائق مضت",
    },
    {
      name: "Coinbase Pro",
      status: "connected",
      balances: [
        { currency: "BTC", available: 0.3, locked: 0.0, total: 0.3 },
        { currency: "ETH", available: 1.5, locked: 0.0, total: 1.5 },
        { currency: "USD", available: 3000, locked: 0.0, total: 3000 },
      ],
      totalValue: 21000,
      lastUpdate: "1 دقيقة مضت",
    },
    {
      name: "Kraken",
      status: "connected",
      balances: [
        { currency: "BTC", available: 0.2, locked: 0.0, total: 0.2 },
        { currency: "ETH", available: 1.0, locked: 0.0, total: 1.0 },
        { currency: "USD", available: 2000, locked: 0.0, total: 2000 },
      ],
      totalValue: 14000,
      lastUpdate: "3 دقائق مضت",
    },
    {
      name: "Bybit",
      status: "connected",
      balances: [
        { currency: "BTC", available: 0.1, locked: 0.0, total: 0.1 },
        { currency: "ETH", available: 0.5, locked: 0.0, total: 0.5 },
        { currency: "USDT", available: 1000, locked: 0.0, total: 1000 },
      ],
      totalValue: 7000,
      lastUpdate: "1 دقيقة مضت",
    },
    {
      name: "OKX",
      status: "connected",
      balances: [
        { currency: "BTC", available: 0.15, locked: 0.0, total: 0.15 },
        { currency: "ETH", available: 0.8, locked: 0.0, total: 0.8 },
        { currency: "USDT", available: 2500, locked: 0.0, total: 2500 },
      ],
      totalValue: 12650,
      lastUpdate: "2 دقائق مضت",
    },
    {
      name: "KuCoin",
      status: "connected",
      balances: [
        { currency: "BTC", available: 0.08, locked: 0.0, total: 0.08 },
        { currency: "ETH", available: 0.6, locked: 0.0, total: 0.6 },
        { currency: "USDT", available: 1500, locked: 0.0, total: 1500 },
      ],
      totalValue: 7100,
      lastUpdate: "4 دقائق مضت",
    },
  ])

  const [arbitrageOpportunities] = useState<ArbitrageOpportunity[]>([
    {
      symbol: "BTC/USDT",
      buyExchange: "Binance",
      sellExchange: "Bybit",
      buyPrice: 44950,
      sellPrice: 45100,
      profit: 150,
      profitPercent: 0.33,
    },
    {
      symbol: "ETH/USDT",
      buyExchange: "Kraken",
      sellExchange: "Coinbase Pro",
      buyPrice: 2980,
      sellPrice: 3020,
      profit: 40,
      profitPercent: 1.34,
    },
    {
      symbol: "BTC/USDT",
      buyExchange: "KuCoin",
      sellExchange: "OKX",
      buyPrice: 44920,
      sellPrice: 45050,
      profit: 130,
      profitPercent: 0.29,
    },
  ])

  const totalPortfolioValue = exchanges.reduce((sum, exchange) => sum + exchange.totalValue, 0)
  const connectedExchanges = exchanges.filter((ex) => ex.status === "connected").length

  const getStatusColor = (status: string) => {
    switch (status) {
      case "connected":
        return "bg-green-500"
      case "disconnected":
        return "bg-gray-500"
      case "error":
        return "bg-red-500"
      default:
        return "bg-gray-500"
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "connected":
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case "disconnected":
        return <AlertTriangle className="h-4 w-4 text-gray-500" />
      case "error":
        return <AlertTriangle className="h-4 w-4 text-red-500" />
      default:
        return <AlertTriangle className="h-4 w-4 text-gray-500" />
    }
  }

  return (
    <div className="space-y-6" dir="rtl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">لوحة التداول متعددة المنصات</h1>
          <p className="text-gray-400 mt-2">إدارة موحدة لأكثر من 6 منصات تداول عالمية</p>
        </div>
        <Button className="bg-cyan-600 hover:bg-cyan-700">
          <RefreshCw className="h-4 w-4 ml-2" />
          تحديث البيانات
        </Button>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="bg-gray-800 border-gray-700">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-300">إجمالي المحفظة</CardTitle>
            <DollarSign className="h-4 w-4 text-cyan-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">${totalPortfolioValue.toLocaleString()}</div>
            <p className="text-xs text-green-400 flex items-center mt-1">
              <TrendingUp className="h-3 w-3 ml-1" />
              +2.4% اليوم
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gray-800 border-gray-700">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-300">المنصات المتصلة</CardTitle>
            <Globe className="h-4 w-4 text-indigo-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{connectedExchanges}/6</div>
            <p className="text-xs text-gray-400 mt-1">منصات نشطة</p>
          </CardContent>
        </Card>

        <Card className="bg-gray-800 border-gray-700">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-300">فرص المراجحة</CardTitle>
            <Activity className="h-4 w-4 text-green-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{arbitrageOpportunities.length}</div>
            <p className="text-xs text-green-400 mt-1">فرص متاحة</p>
          </CardContent>
        </Card>

        <Card className="bg-gray-800 border-gray-700">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-300">الربح المتوقع</CardTitle>
            <BarChart3 className="h-4 w-4 text-yellow-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">$320</div>
            <p className="text-xs text-yellow-400 mt-1">من المراجحة</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="exchanges" className="space-y-6">
        <TabsList className="bg-gray-800 border-gray-700">
          <TabsTrigger value="exchanges" className="data-[state=active]:bg-cyan-600">
            المنصات
          </TabsTrigger>
          <TabsTrigger value="arbitrage" className="data-[state=active]:bg-cyan-600">
            المراجحة
          </TabsTrigger>
          <TabsTrigger value="portfolio" className="data-[state=active]:bg-cyan-600">
            توزيع المحفظة
          </TabsTrigger>
        </TabsList>

        <TabsContent value="exchanges" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {exchanges.map((exchange) => (
              <Card key={exchange.name} className="bg-gray-800 border-gray-700">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg text-white">{exchange.name}</CardTitle>
                    <div className="flex items-center gap-2">
                      {getStatusIcon(exchange.status)}
                      <Badge variant="outline" className={`${getStatusColor(exchange.status)} text-white border-0`}>
                        {exchange.status === "connected" ? "متصل" : "غير متصل"}
                      </Badge>
                    </div>
                  </div>
                  <CardDescription className="text-gray-400">آخر تحديث: {exchange.lastUpdate}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="text-right">
                    <div className="text-2xl font-bold text-white">${exchange.totalValue.toLocaleString()}</div>
                    <div className="text-sm text-gray-400">القيمة الإجمالية</div>
                  </div>

                  <div className="space-y-2">
                    {exchange.balances.slice(0, 3).map((balance) => (
                      <div key={balance.currency} className="flex justify-between items-center">
                        <div className="text-sm text-gray-300">
                          {balance.total.toFixed(balance.currency === "BTC" ? 4 : 2)} {balance.currency}
                        </div>
                        <div className="text-sm text-gray-400">
                          متاح: {balance.available.toFixed(balance.currency === "BTC" ? 4 : 2)}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="arbitrage" className="space-y-6">
          <Card className="bg-gray-800 border-gray-700">
            <CardHeader>
              <CardTitle className="text-white">فرص المراجحة المتاحة</CardTitle>
              <CardDescription className="text-gray-400">الفرص المربحة للتداول بين المنصات المختلفة</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {arbitrageOpportunities.map((opportunity, index) => (
                  <div key={index} className="flex items-center justify-between p-4 bg-gray-700 rounded-lg">
                    <div className="flex-1">
                      <div className="font-semibold text-white">{opportunity.symbol}</div>
                      <div className="text-sm text-gray-400">
                        شراء من {opportunity.buyExchange} - بيع في {opportunity.sellExchange}
                      </div>
                    </div>

                    <div className="text-center mx-4">
                      <div className="text-sm text-gray-400">سعر الشراء</div>
                      <div className="font-semibold text-white">${opportunity.buyPrice.toLocaleString()}</div>
                    </div>

                    <div className="text-center mx-4">
                      <div className="text-sm text-gray-400">سعر البيع</div>
                      <div className="font-semibold text-white">${opportunity.sellPrice.toLocaleString()}</div>
                    </div>

                    <div className="text-center mx-4">
                      <div className="text-sm text-gray-400">الربح</div>
                      <div className="font-semibold text-green-400">
                        ${opportunity.profit} ({opportunity.profitPercent}%)
                      </div>
                    </div>

                    <Button size="sm" className="bg-green-600 hover:bg-green-700">
                      تنفيذ
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="portfolio" className="space-y-6">
          <Card className="bg-gray-800 border-gray-700">
            <CardHeader>
              <CardTitle className="text-white">توزيع المحفظة عبر المنصات</CardTitle>
              <CardDescription className="text-gray-400">نسبة توزيع الأصول على المنصات المختلفة</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {exchanges.map((exchange) => {
                const percentage = (exchange.totalValue / totalPortfolioValue) * 100
                return (
                  <div key={exchange.name} className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-white font-medium">{exchange.name}</span>
                      <span className="text-gray-400">
                        ${exchange.totalValue.toLocaleString()} ({percentage.toFixed(1)}%)
                      </span>
                    </div>
                    <Progress value={percentage} className="h-2" />
                  </div>
                )
              })}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
