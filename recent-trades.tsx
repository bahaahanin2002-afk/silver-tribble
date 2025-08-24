"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { TrendingUp, TrendingDown } from "lucide-react"

interface RecentTradesProps {
  isArabic: boolean
}

export function RecentTrades({ isArabic }: RecentTradesProps) {
  const text = {
    en: {
      title: "Recent Trades",
      description: "Latest trading activity and results",
      symbol: "Symbol",
      action: "Action",
      price: "Price",
      quantity: "Quantity",
      pnl: "P&L",
      time: "Time",
      buy: "Buy",
      sell: "Sell",
    },
    ar: {
      title: "الصفقات الأخيرة",
      description: "أحدث أنشطة التداول والنتائج",
      symbol: "الرمز",
      action: "الإجراء",
      price: "السعر",
      quantity: "الكمية",
      pnl: "الربح/الخسارة",
      time: "الوقت",
      buy: "شراء",
      sell: "بيع",
    },
  }

  const t = isArabic ? text.ar : text.en

  const trades = [
    {
      id: 1,
      symbol: "BTC/USDT",
      action: "buy",
      price: 43250.5,
      quantity: 0.025,
      pnl: 2.34,
      time: "10:30 AM",
      strategy: "RSI",
    },
    {
      id: 2,
      symbol: "ETH/USDT",
      action: "sell",
      price: 2680.75,
      quantity: 0.5,
      pnl: -0.87,
      time: "09:45 AM",
      strategy: "Breakout",
    },
    {
      id: 3,
      symbol: "BNB/USDT",
      action: "buy",
      price: 315.2,
      quantity: 2.0,
      pnl: 1.56,
      time: "09:15 AM",
      strategy: "RSI",
    },
    {
      id: 4,
      symbol: "ADA/USDT",
      action: "sell",
      price: 0.485,
      quantity: 1000,
      pnl: 0.92,
      time: "08:30 AM",
      strategy: "Breakout",
    },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle className="font-serif">{t.title}</CardTitle>
        <CardDescription>{t.description}</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t.symbol}</TableHead>
              <TableHead>{t.action}</TableHead>
              <TableHead>{t.price}</TableHead>
              <TableHead>{t.quantity}</TableHead>
              <TableHead>{t.pnl}</TableHead>
              <TableHead>{t.time}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {trades.map((trade) => (
              <TableRow key={trade.id}>
                <TableCell className="font-medium">{trade.symbol}</TableCell>
                <TableCell>
                  <Badge variant={trade.action === "buy" ? "default" : "secondary"}>
                    {trade.action === "buy" ? t.buy : t.sell}
                  </Badge>
                </TableCell>
                <TableCell>${trade.price.toLocaleString()}</TableCell>
                <TableCell>{trade.quantity}</TableCell>
                <TableCell>
                  <span className={`flex items-center gap-1 ${trade.pnl > 0 ? "text-primary" : "text-destructive"}`}>
                    {trade.pnl > 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                    {trade.pnl > 0 ? "+" : ""}
                    {trade.pnl}%
                  </span>
                </TableCell>
                <TableCell className="text-muted-foreground">{trade.time}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
