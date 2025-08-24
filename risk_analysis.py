"""
Risk Analysis Tools for AI Trading Bot
Demonstrates advanced risk management calculations
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

class AdvancedRiskAnalyzer:
    def __init__(self):
        self.risk_free_rate = 0.02  # 2% annual risk-free rate
        
    def calculate_sharpe_ratio(self, returns, risk_free_rate=None):
        """Calculate Sharpe ratio"""
        if risk_free_rate is None:
            risk_free_rate = self.risk_free_rate
            
        excess_returns = returns - risk_free_rate/252  # Daily risk-free rate
        return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
    
    def calculate_max_drawdown(self, equity_curve):
        """Calculate maximum drawdown"""
        peak = np.maximum.accumulate(equity_curve)
        drawdown = (equity_curve - peak) / peak
        return np.min(drawdown)
    
    def calculate_var(self, returns, confidence_level=0.05):
        """Calculate Value at Risk (VaR)"""
        return np.percentile(returns, confidence_level * 100)
    
    def calculate_cvar(self, returns, confidence_level=0.05):
        """Calculate Conditional Value at Risk (CVaR)"""
        var = self.calculate_var(returns, confidence_level)
        return np.mean(returns[returns <= var])
    
    def kelly_criterion(self, win_rate, avg_win, avg_loss):
        """Calculate optimal position size using Kelly Criterion"""
        if avg_loss == 0:
            return 0
        
        win_loss_ratio = abs(avg_win / avg_loss)
        kelly_fraction = win_rate - (1 - win_rate) / win_loss_ratio
        
        # Cap Kelly fraction at 25% for safety
        return max(0, min(0.25, kelly_fraction))
    
    def monte_carlo_simulation(self, returns, num_simulations=1000, days=252):
        """Run Monte Carlo simulation on returns"""
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        simulations = []
        for _ in range(num_simulations):
            random_returns = np.random.normal(mean_return, std_return, days)
            cumulative_return = np.prod(1 + random_returns) - 1
            simulations.append(cumulative_return)
        
        return {
            'mean': np.mean(simulations),
            'std': np.std(simulations),
            'percentile_5': np.percentile(simulations, 5),
            'percentile_95': np.percentile(simulations, 95),
            'probability_positive': len([s for s in simulations if s > 0]) / len(simulations)
        }

def demonstrate_risk_analysis():
    """Demonstrate risk analysis capabilities"""
    print("🛡️  Advanced Risk Analysis Demo")
    print("=" * 50)
    
    # Generate sample returns data
    np.random.seed(42)  # For reproducible results
    daily_returns = np.random.normal(0.001, 0.02, 252)  # 1 year of daily returns
    
    # Create equity curve
    initial_equity = 10000
    equity_curve = [initial_equity]
    for ret in daily_returns:
        equity_curve.append(equity_curve[-1] * (1 + ret))
    
    analyzer = AdvancedRiskAnalyzer()
    
    # Calculate risk metrics
    print("📊 Risk Metrics:")
    sharpe = analyzer.calculate_sharpe_ratio(daily_returns)
    max_dd = analyzer.calculate_max_drawdown(equity_curve)
    var_5 = analyzer.calculate_var(daily_returns, 0.05)
    cvar_5 = analyzer.calculate_cvar(daily_returns, 0.05)
    
    print(f"Sharpe Ratio: {sharpe:.3f}")
    print(f"Maximum Drawdown: {max_dd*100:.2f}%")
    print(f"VaR (5%): {var_5*100:.2f}%")
    print(f"CVaR (5%): {cvar_5*100:.2f}%")
    
    # Kelly Criterion example
    print("\n🎯 Position Sizing (Kelly Criterion):")
    win_rate = 0.55
    avg_win = 0.02
    avg_loss = -0.015
    
    kelly_fraction = analyzer.kelly_criterion(win_rate, avg_win, avg_loss)
    print(f"Win Rate: {win_rate*100:.1f}%")
    print(f"Average Win: {avg_win*100:.2f}%")
    print(f"Average Loss: {avg_loss*100:.2f}%")
    print(f"Optimal Kelly Fraction: {kelly_fraction*100:.2f}%")
    
    # Monte Carlo simulation
    print("\n🎲 Monte Carlo Simulation (1000 runs, 1 year):")
    mc_results = analyzer.monte_carlo_simulation(daily_returns)
    
    print(f"Expected Return: {mc_results['mean']*100:.2f}%")
    print(f"Standard Deviation: {mc_results['std']*100:.2f}%")
    print(f"5th Percentile: {mc_results['percentile_5']*100:.2f}%")
    print(f"95th Percentile: {mc_results['percentile_95']*100:.2f}%")
    print(f"Probability of Positive Return: {mc_results['probability_positive']*100:.1f}%")
    
    # Risk-adjusted position sizing
    print("\n⚖️  Risk-Adjusted Position Sizing:")
    account_balance = 50000
    risk_per_trade = 0.01  # 1% risk per trade
    
    # Example trade setup
    entry_price = 45000
    stop_loss = 43000
    risk_per_share = entry_price - stop_loss
    
    position_size = (account_balance * risk_per_trade) / risk_per_share
    position_value = position_size * entry_price
    
    print(f"Account Balance: ${account_balance:,.2f}")
    print(f"Risk per Trade: {risk_per_trade*100:.1f}%")
    print(f"Entry Price: ${entry_price:,.2f}")
    print(f"Stop Loss: ${stop_loss:,.2f}")
    print(f"Risk per Share: ${risk_per_share:,.2f}")
    print(f"Position Size: {position_size:.4f} units")
    print(f"Position Value: ${position_value:,.2f}")
    print(f"Portfolio Allocation: {(position_value/account_balance)*100:.2f}%")

if __name__ == "__main__":
    demonstrate_risk_analysis()
