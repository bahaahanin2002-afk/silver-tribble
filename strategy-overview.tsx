"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Switch } from "@/components/ui/switch"
import { Button } from "@/components/ui/button"
import { TrendingUp, TrendingDown, Settings, Activity } from "lucide-react"

interface StrategyOverviewProps {
  isArabic: boolean
}

export function StrategyOverview({ isArabic }: StrategyOverviewProps) {
  const text = {
    en: {
      title: "Active Strategies",
      description: "Monitor and manage your trading strategies",
      rsiStrategy: "RSI Momentum",
      breakoutStrategy: "ATR Breakout",
      active: "Active",
      inactive: "Inactive",
      winRate: "Win Rate",
      totalTrades: "Total Trades",
      avgReturn: "Avg Return",
      configure: "Configure",
    },
    ar: {
      title: "الاستراتيجيات النشطة",
      description: "مراقبة وإدارة استراتيجيات التداول الخاصة بك",
      rsiStrategy: "استراتيجية RSI",
      breakoutStrategy: "استراتيجية الكسر ATR",
      active: "نشط",
      inactive: "غير نشط",
      winRate: "معدل الفوز",
      totalTrades: "إجمالي الصفقات",
      avgReturn: "متوسط العائد",
      configure: "تكوين",
    },
  }

  const t = isArabic ? text.ar : text.en

  const strategies = [
    {
      id: "rsi",
      name: t.rsiStrategy,
      active: true,
      winRate: 72.5,
      totalTrades: 156,
      avgReturn: 2.3,
      performance: "positive",
    },
    {
      id: "breakout",
      name: t.breakoutStrategy,
      active: true,
      winRate: 64.8,
      totalTrades: 91,
      avgReturn: 1.8,
      performance: "positive",
    },
  ]

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {strategies.map((strategy) => (
        <Card key={strategy.id}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="font-serif flex items-center gap-2">
                  <Activity className="h-5 w-5 text-primary" />
                  {strategy.name}
                </CardTitle>
                <CardDescription>
                  {strategy.performance === "positive" ? (
                    <span className="flex items-center gap-1 text-primary">
                      <TrendingUp className="h-3 w-3" />
                      Performing well
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-destructive">
                      <TrendingDown className="h-3 w-3" />
                      Needs attention
                    </span>
                  )}
                </CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={strategy.active ? "default" : "secondary"}>
                  {strategy.active ? t.active : t.inactive}
                </Badge>
                <Switch checked={strategy.active} />
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">{t.winRate}</p>
                <p className="text-lg font-serif font-bold text-accent">{strategy.winRate}%</p>
                <Progress value={strategy.winRate} className="mt-1" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">{t.totalTrades}</p>
                <p className="text-lg font-serif font-bold">{strategy.totalTrades}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">{t.avgReturn}</p>
                <p className="text-lg font-serif font-bold text-primary">+{strategy.avgReturn}%</p>
              </div>
            </div>

            <Button variant="outline" size="sm" className="w-full gap-2 bg-transparent">
              <Settings className="h-4 w-4" />
              {t.configure}
            </Button>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
