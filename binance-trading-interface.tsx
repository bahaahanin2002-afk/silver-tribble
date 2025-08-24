"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Wallet } from "lucide-react"

interface Balance {
  asset: string
  free: string
  locked: string
}

interface OrderData {
  symbol: string
  side: "BUY" | "SELL"
  type: "MARKET" | "LIMIT"
  quantity: number
}

export default function BinanceTradingInterface() {
  const [isConnected, setIsConnected] = useState(false)
  const [balances, setBalances] = useState<Balance[]>([])
  const [apiKey, setApiKey] = useState("")
  const [apiSecret, setApiSecret] = useState("")
  const [loading, setLoading] = useState(false)
  const [orderData, setOrderData] = useState<OrderData>({
    symbol: "BTCUSDT",
    side: "BUY",
    type: "MARKET",
    quantity: 0.001,
  })

  const connectBinance = async () => {
    setLoading(true)
    try {
      const response = await fetch("/api/binance/connect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_key: apiKey, api_secret: apiSecret, user_id: "default" }),
      })

      if (response.ok) {
        setIsConnected(true)
        fetchBalances()
      }
    } catch (error) {
      console.error("Connection failed:", error)
    }
    setLoading(false)
  }

  const fetchBalances = async () => {
    try {
      const response = await fetch("/api/binance/balances?user_id=default")
      const data = await response.json()
      if (data.balances) {
        setBalances(data.balances)
      }
    } catch (error) {
      console.error("Failed to fetch balances:", error)
    }
  }

  const placeOrder = async () => {
    setLoading(true)
    try {
      const response = await fetch("/api/binance/order", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...orderData, user_id: "default" }),
      })

      if (response.ok) {
        const result = await response.json()
        console.log("Order placed:", result)
        fetchBalances() // Refresh balances after order
      }
    } catch (error) {
      console.error("Order failed:", error)
    }
    setLoading(false)
  }

  return (
    <div className="space-y-6">
      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <CardTitle className="font-montserrat text-cyan-400 flex items-center gap-2">
            <Wallet className="h-5 w-5" />
            ربط حساب Binance
          </CardTitle>
          <CardDescription className="text-gray-400">اربط حسابك في Binance لبدء التداول المباشر</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {!isConnected ? (
            <>
              <div className="space-y-2">
                <Label htmlFor="api-key" className="text-gray-300">
                  مفتاح API
                </Label>
                <Input
                  id="api-key"
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="bg-gray-800 border-gray-700 text-white"
                  placeholder="أدخل مفتاح API الخاص بك"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="api-secret" className="text-gray-300">
                  المفتاح السري
                </Label>
                <Input
                  id="api-secret"
                  type="password"
                  value={apiSecret}
                  onChange={(e) => setApiSecret(e.target.value)}
                  className="bg-gray-800 border-gray-700 text-white"
                  placeholder="أدخل المفتاح السري"
                />
              </div>
              <Button
                onClick={connectBinance}
                disabled={loading || !apiKey || !apiSecret}
                className="w-full bg-cyan-600 hover:bg-cyan-700"
              >
                {loading ? "جاري الربط..." : "ربط الحساب"}
              </Button>
            </>
          ) : (
            <div className="space-y-4">
              <Badge className="bg-green-600 text-white">متصل بنجاح ✓</Badge>

              <Tabs defaultValue="balances" className="w-full">
                <TabsList className="grid w-full grid-cols-2 bg-gray-800">
                  <TabsTrigger value="balances" className="text-gray-300">
                    الأرصدة
                  </TabsTrigger>
                  <TabsTrigger value="trading" className="text-gray-300">
                    التداول
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="balances" className="space-y-4">
                  <div className="grid gap-4">
                    {balances.map((balance) => (
                      <div key={balance.asset} className="flex justify-between items-center p-3 bg-gray-800 rounded-lg">
                        <div>
                          <span className="font-semibold text-white">{balance.asset}</span>
                        </div>
                        <div className="text-right">
                          <div className="text-green-400">{Number.parseFloat(balance.free).toFixed(8)}</div>
                          {Number.parseFloat(balance.locked) > 0 && (
                            <div className="text-yellow-400 text-sm">
                              مقفل: {Number.parseFloat(balance.locked).toFixed(8)}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                  <Button onClick={fetchBalances} variant="outline" className="w-full bg-transparent">
                    تحديث الأرصدة
                  </Button>
                </TabsContent>

                <TabsContent value="trading" className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label className="text-gray-300">الرمز</Label>
                      <Select
                        value={orderData.symbol}
                        onValueChange={(value) => setOrderData({ ...orderData, symbol: value })}
                      >
                        <SelectTrigger className="bg-gray-800 border-gray-700">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-gray-800 border-gray-700">
                          <SelectItem value="BTCUSDT">BTC/USDT</SelectItem>
                          <SelectItem value="ETHUSDT">ETH/USDT</SelectItem>
                          <SelectItem value="BNBUSDT">BNB/USDT</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label className="text-gray-300">النوع</Label>
                      <Select
                        value={orderData.side}
                        onValueChange={(value: "BUY" | "SELL") => setOrderData({ ...orderData, side: value })}
                      >
                        <SelectTrigger className="bg-gray-800 border-gray-700">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-gray-800 border-gray-700">
                          <SelectItem value="BUY">شراء</SelectItem>
                          <SelectItem value="SELL">بيع</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-gray-300">الكمية</Label>
                    <Input
                      type="number"
                      step="0.001"
                      value={orderData.quantity}
                      onChange={(e) => setOrderData({ ...orderData, quantity: Number.parseFloat(e.target.value) })}
                      className="bg-gray-800 border-gray-700 text-white"
                    />
                  </div>

                  <Button
                    onClick={placeOrder}
                    disabled={loading}
                    className={`w-full ${orderData.side === "BUY" ? "bg-green-600 hover:bg-green-700" : "bg-red-600 hover:bg-red-700"}`}
                  >
                    {loading ? "جاري التنفيذ..." : `${orderData.side === "BUY" ? "شراء" : "بيع"} ${orderData.symbol}`}
                  </Button>
                </TabsContent>
              </Tabs>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
