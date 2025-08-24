"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Slider } from "@/components/ui/slider"
import { Label } from "@/components/ui/label"
import { Shield, AlertTriangle, CheckCircle } from "lucide-react"

interface RiskManagementProps {
  isArabic: boolean
}

export function RiskManagement({ isArabic }: RiskManagementProps) {
  const text = {
    en: {
      title: "Risk Management",
      description: "Monitor and control your trading risk parameters",
      portfolioRisk: "Portfolio Risk",
      maxDrawdown: "Max Drawdown",
      dailyLoss: "Daily Loss Limit",
      positionSize: "Position Size",
      riskLevel: "Risk Level",
      low: "Low",
      medium: "Medium",
      high: "High",
      currentExposure: "Current Exposure",
      riskLimits: "Risk Limits",
      maxPositions: "Max Positions",
      correlationLimit: "Correlation Limit",
    },
    ar: {
      title: "إدارة المخاطر",
      description: "مراقبة والتحكم في معايير مخاطر التداول",
      portfolioRisk: "مخاطر المحفظة",
      maxDrawdown: "أقصى انخفاض",
      dailyLoss: "حد الخسارة اليومي",
      positionSize: "حجم المركز",
      riskLevel: "مستوى المخاطر",
      low: "منخفض",
      medium: "متوسط",
      high: "عالي",
      currentExposure: "التعرض الحالي",
      riskLimits: "حدود المخاطر",
      maxPositions: "أقصى عدد مراكز",
      correlationLimit: "حد الارتباط",
    },
  }

  const t = isArabic ? text.ar : text.en

  const riskMetrics = {
    portfolioRisk: 1.8,
    maxDrawdown: 8.5,
    dailyLoss: 2.1,
    currentExposure: 45.2,
    maxPositions: 5,
    currentPositions: 3,
    correlationLimit: 70,
  }

  const getRiskLevel = (value: number, max: number) => {
    const percentage = (value / max) * 100
    if (percentage < 30) return { level: t.low, color: "default" }
    if (percentage < 70) return { level: t.medium, color: "secondary" }
    return { level: t.high, color: "destructive" }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle className="font-serif flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary" />
            {t.currentExposure}
          </CardTitle>
          <CardDescription>{t.description}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-4">
            <div>
              <div className="flex justify-between items-center mb-2">
                <Label>{t.portfolioRisk}</Label>
                <Badge variant={getRiskLevel(riskMetrics.portfolioRisk, 5).color as any}>
                  {riskMetrics.portfolioRisk}%
                </Badge>
              </div>
              <Progress value={(riskMetrics.portfolioRisk / 5) * 100} />
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <Label>{t.maxDrawdown}</Label>
                <Badge variant={getRiskLevel(riskMetrics.maxDrawdown, 15).color as any}>
                  {riskMetrics.maxDrawdown}%
                </Badge>
              </div>
              <Progress value={(riskMetrics.maxDrawdown / 15) * 100} />
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <Label>{t.dailyLoss}</Label>
                <Badge variant={getRiskLevel(riskMetrics.dailyLoss, 5).color as any}>{riskMetrics.dailyLoss}%</Badge>
              </div>
              <Progress value={(riskMetrics.dailyLoss / 5) * 100} />
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <Label>{t.maxPositions}</Label>
                <span className="text-sm">
                  {riskMetrics.currentPositions}/{riskMetrics.maxPositions}
                </span>
              </div>
              <Progress value={(riskMetrics.currentPositions / riskMetrics.maxPositions) * 100} />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="font-serif flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-accent" />
            {t.riskLimits}
          </CardTitle>
          <CardDescription>Adjust your risk parameters</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-4">
            <div>
              <Label className="text-sm font-medium">{t.portfolioRisk} (2%)</Label>
              <Slider defaultValue={[2]} max={5} step={0.1} className="mt-2" />
            </div>

            <div>
              <Label className="text-sm font-medium">{t.maxDrawdown} (15%)</Label>
              <Slider defaultValue={[15]} max={25} step={1} className="mt-2" />
            </div>

            <div>
              <Label className="text-sm font-medium">{t.dailyLoss} (5%)</Label>
              <Slider defaultValue={[5]} max={10} step={0.5} className="mt-2" />
            </div>

            <div>
              <Label className="text-sm font-medium">{t.correlationLimit} (70%)</Label>
              <Slider defaultValue={[70]} max={100} step={5} className="mt-2" />
            </div>
          </div>

          <div className="pt-4 border-t border-border">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <CheckCircle className="h-4 w-4 text-primary" />
              All risk parameters within safe limits
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
