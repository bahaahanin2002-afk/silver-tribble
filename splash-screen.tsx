"use client"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Bot, Zap, Globe, Mail, Facebook, Apple } from "lucide-react"

interface SplashScreenProps {
  isArabic: boolean
  onLogin: () => void
  onRegister: () => void
  onLanguageToggle: () => void
}

export function SplashScreen({ isArabic, onLogin, onRegister, onLanguageToggle }: SplashScreenProps) {
  const text = {
    en: {
      welcome: "Welcome to",
      appName: "CryptoAI Pro",
      tagline: "Advanced AI-Powered Cryptocurrency Trading",
      subtitle: "Experience the future of automated trading with cutting-edge artificial intelligence",
      login: "Sign In",
      register: "Create Account",
      orContinueWith: "Or continue with",
      language: "العربية",
    },
    ar: {
      welcome: "مرحباً بك في",
      appName: "كريبتو AI برو",
      tagline: "تداول العملات المشفرة بالذكاء الاصطناعي المتقدم",
      subtitle: "اختبر مستقبل التداول الآلي مع الذكاء الاصطناعي المتطور",
      login: "تسجيل الدخول",
      register: "إنشاء حساب",
      orContinueWith: "أو تابع مع",
      language: "English",
    },
  }

  const t = isArabic ? text.ar : text.en

  return (
    <div className={`min-h-screen gradient-bg flex items-center justify-center p-4 ${isArabic ? "rtl" : "ltr"}`}>
      {/* Language Toggle */}
      <div className="absolute top-6 right-6">
        <Button
          variant="ghost"
          size="sm"
          onClick={onLanguageToggle}
          className="glassmorphism text-white hover:bg-white/20 gap-2"
        >
          <Globe className="h-4 w-4" />
          {t.language}
        </Button>
      </div>

      {/* Main Content */}
      <div className="max-w-md w-full space-y-8 text-center">
        {/* 3D Logo */}
        <div className="float-animation">
          <div className="relative mx-auto w-24 h-24 mb-6">
            <div className="absolute inset-0 glow-effect rounded-full bg-gradient-to-r from-primary to-accent"></div>
            <div className="relative z-10 w-full h-full rounded-full glassmorphism flex items-center justify-center">
              <div className="relative">
                <Bot className="h-12 w-12 text-white" />
                <Zap className="absolute -top-1 -right-1 h-6 w-6 text-accent" />
              </div>
            </div>
          </div>
        </div>

        {/* Welcome Text */}
        <div className="space-y-4">
          <div>
            <p className="text-lg text-white/80 font-sans">{t.welcome}</p>
            <h1 className="text-4xl font-serif font-black text-white mb-2">{t.appName}</h1>
            <p className="text-xl text-primary font-medium">{t.tagline}</p>
          </div>
          <p className="text-white/70 text-sm leading-relaxed max-w-sm mx-auto">{t.subtitle}</p>
        </div>

        {/* Main Action Buttons */}
        <Card className="glassmorphism border-white/20">
          <CardContent className="p-6 space-y-4">
            <Button
              onClick={onLogin}
              className="w-full bg-primary hover:bg-primary/90 text-white font-medium py-3 text-lg glow-effect"
              size="lg"
            >
              {t.login}
            </Button>

            <Button
              onClick={onRegister}
              variant="outline"
              className="w-full glassmorphism border-white/30 text-white hover:bg-white/10 font-medium py-3 bg-transparent"
              size="lg"
            >
              {t.register}
            </Button>

            {/* Social Login Options */}
            <div className="pt-4">
              <p className="text-white/60 text-sm mb-4">{t.orContinueWith}</p>
              <div className="flex justify-center gap-4">
                <Button variant="ghost" size="sm" className="glassmorphism w-12 h-12 p-0 hover:bg-white/10">
                  <Facebook className="h-5 w-5 text-white" />
                </Button>
                <Button variant="ghost" size="sm" className="glassmorphism w-12 h-12 p-0 hover:bg-white/10">
                  <Mail className="h-5 w-5 text-white" />
                </Button>
                <Button variant="ghost" size="sm" className="glassmorphism w-12 h-12 p-0 hover:bg-white/10">
                  <Apple className="h-5 w-5 text-white" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Floating Elements */}
        <div className="absolute top-20 left-10 opacity-20">
          <div className="w-16 h-16 rounded-full glassmorphism float-animation" style={{ animationDelay: "1s" }}></div>
        </div>
        <div className="absolute bottom-20 right-10 opacity-20">
          <div className="w-12 h-12 rounded-full glassmorphism float-animation" style={{ animationDelay: "2s" }}></div>
        </div>
        <div className="absolute top-1/2 left-4 opacity-20">
          <div className="w-8 h-8 rounded-full glassmorphism float-animation" style={{ animationDelay: "0.5s" }}></div>
        </div>
      </div>
    </div>
  )
}
